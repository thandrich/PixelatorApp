// Global variables
let paletteDialogOpened = false;
let lastValidImageFile = null;
let isProcessing = false; // Flag to track processing state

// DOM Elements
document.addEventListener('DOMContentLoaded', () => {
    // Initialize elements
    const fileElem = document.getElementById('fileElem');
    const dropZone = document.getElementById('drop-area');
    const preview = document.getElementById('preview');
    const processButton = document.getElementById('process-button');
    const paletteSelect = document.getElementById('palette');
    const quantizationSelect = document.getElementById('quantization_mode');
    const quantizationDescription = document.getElementById('quantization_description');
    const palettePreview = document.getElementById('palette-preview');
    const importPaletteLink = document.getElementById('import-palette-link');
    const importPaletteInput = document.getElementById('import-palette-file');
    const fileSelect = document.getElementById('fileSelect');
    const loadingModalElement = document.getElementById('loadingModal');
    const errorModalElement = document.getElementById('errorModal');
    const cancelButton = document.getElementById('cancelProcessingBtn');

    // Load initial palette swatches if a palette is selected
    if (paletteSelect && paletteSelect.value) {
        loadPaletteSwatches(paletteSelect.value);
    }

    // Set up event listeners
    setupFileHandling();
    setupPaletteHandling();
    setupProcessing();
    
    // Set up the cancel processing button
    if (cancelButton) {
        cancelButton.addEventListener('click', () => {
            hideLoadingModal();
        });
    }

    // Setup modal close buttons
    setupModalCloseButtons();

    function setupModalCloseButtons() {
        // For all elements with data-bs-dismiss="modal"
        document.querySelectorAll('[data-bs-dismiss="modal"]').forEach(button => {
            button.addEventListener('click', function() {
                const modalId = this.closest('.md-modal').id;
                hideModal(modalId);
            });
        });
    }

    function setupFileHandling() {
        if (fileSelect && fileElem) {
            fileSelect.addEventListener('click', () => {
                fileElem.click();
            });
        }

        if (fileElem && dropZone) {
            // File input change handler
            fileElem.addEventListener('change', (e) => {
                handleFiles(e.target.files);
            });

            // Drag and drop handlers
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.add('highlight');
            });

            dropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove('highlight');
            });

            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove('highlight');
                handleFiles(e.dataTransfer.files);
            });
        }
    }

    function setupPaletteHandling() {
        if (paletteSelect) {
            paletteSelect.addEventListener('change', () => {
                loadPaletteSwatches(paletteSelect.value);
            });
        }

        if (importPaletteLink && importPaletteInput) {
            importPaletteLink.addEventListener('click', (e) => {
                e.preventDefault();
                if (!paletteDialogOpened) {
                    paletteDialogOpened = true;
                    importPaletteInput.click();
                    setTimeout(() => {
                        paletteDialogOpened = false;
                    }, 1000);
                }
            });

            importPaletteInput.addEventListener('change', handlePaletteImport);
        }
    }

    function handlePaletteImport() {
        if (importPaletteInput.files.length > 0) {
            const file = importPaletteInput.files[0];
            if (!file.name.endsWith('.hex') && !file.name.endsWith('.txt')) {
                showError('Please select a valid palette file (.hex or .txt)');
                importPaletteInput.value = '';
                return;
            }

            const formData = new FormData();
            formData.append('palette_file', file);
            formData.append('name', file.name.replace(/\.[^/.]+$/, ''));

            fetch('/palette/import', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) throw new Error(data.error);
                const option = document.createElement('option');
                option.value = data.id;
                option.text = data.name;
                paletteSelect.add(option);
                paletteSelect.value = data.id;
                loadPaletteSwatches(data.id);
                
                // Add a subtle visual feedback
                if (importPaletteLink) {
                    const originalText = importPaletteLink.textContent.trim();
                    importPaletteLink.innerHTML = '<span class="material-symbols-outlined">check_circle</span> Palette Imported';
                    importPaletteLink.classList.add('md-button-filled');
                    importPaletteLink.classList.remove('md-button-tonal');
                    
                    // Reset after 2 seconds
                    setTimeout(() => {
                        importPaletteLink.innerHTML = '<span class="material-symbols-outlined">color_lens</span> Import Additional Palettes';
                        importPaletteLink.classList.remove('md-button-filled');
                        importPaletteLink.classList.add('md-button-tonal');
                    }, 2000);
                }
            })
            .catch(error => {
                showError(error.message);
            })
            .finally(() => {
                importPaletteInput.value = '';
            });
        }
    }

    function setupProcessing() {
        if (processButton) {
            processButton.addEventListener('click', () => {
                if (!lastValidImageFile) {
                    showError('Please select an image first.');
                    return;
                }
                
                if (isProcessing) {
                    console.log('Already processing, ignoring click');
                    return;
                }

                const formData = new FormData();
                formData.append('file', lastValidImageFile);
                formData.append('palette', paletteSelect.value);
                
                // Get and log the quantization mode
                const selectedMode = quantizationSelect.value;
                console.log(`Selected quantization mode: ${selectedMode}`);
                formData.append('quantization_mode', selectedMode);
                
                formData.append('max_resolution', document.getElementById('max_resolution').value);
                formData.append('upscale_factor', document.getElementById('upscale_factor').value);

                // Show the loading modal
                showLoadingModal();

                fetch('/upload', {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    console.log(`Received response status: ${response.status}`);
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    console.log(`Received data: ${JSON.stringify(data)}`);
                    if (data.error) throw new Error(data.error);
                    
                    document.getElementById('result-container').innerHTML = `<img src="${data.processed_image_url}" alt="Processed Image" class="md-image-display">`;
                    document.getElementById('download-container').style.display = 'block';
                    document.getElementById('download-link').href = data.processed_image_url;
                    
                    // Log the quantization mode from response
                    console.log(`Response quantization mode: ${data.quantization_mode}`);
                    
                    // Hide the loading modal
                    setTimeout(() => {
                        hideLoadingModal();
                    }, 250); // Small delay to ensure everything is ready
                })
                .catch(error => {
                    console.error('Error processing image:', error);
                    showError(error.message);
                })
                .finally(() => {
                    console.log('Processing finished, ensuring modal is hidden');
                    setTimeout(() => {
                        hideLoadingModal();
                    }, 500); // Longer delay in finally as a backup
                });
            });
        }
    }

    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            if (!file.type.match('image.*')) {
                showError('Please select an image file.');
                clearFileInput();
                return;
            }

            lastValidImageFile = file;
            preview.innerHTML = '';
            const img = document.createElement('img');
            img.classList.add('md-mb-2');
            img.file = file;
            preview.appendChild(img);

            const reader = new FileReader();
            reader.onload = (e) => {
                img.src = e.target.result;
            };
            reader.readAsDataURL(file);
            processButton.disabled = false;
        }
    }

    function loadPaletteSwatches(paletteId) {
        fetch(`/palette/${paletteId}`)
            .then(response => {
                if (!response.ok) throw new Error('Failed to load palette');
                return response.json();
            })
            .then(data => {
                palettePreview.innerHTML = '';
                data.colors.forEach(color => {
                    const swatch = document.createElement('div');
                    swatch.className = 'color-swatch';
                    swatch.style.backgroundColor = `#${color}`;
                    swatch.title = `#${color}`;
                    palettePreview.appendChild(swatch);
                });
            })
            .catch(error => {
                console.error('Error loading palette:', error);
                palettePreview.innerHTML = '<p class="md-text-error md-text-body-small">Failed to load palette.</p>';
            });
    }

    // Update quantization description when mode is changed
    if (quantizationSelect && quantizationDescription) {
        quantizationSelect.addEventListener('change', () => {
            updateQuantizationDescription();
        });

        // Set initial quantization description
        updateQuantizationDescription();
    }

    function updateQuantizationDescription() {
        const selectedOption = quantizationSelect.options[quantizationSelect.selectedIndex];
        // Check if serverData exists first
        if (window.serverData && window.serverData.quantizationModes) {
            const selectedMode = window.serverData.quantizationModes.find(mode => mode.value === selectedOption.value);
            if (selectedMode) {
                quantizationDescription.textContent = selectedMode.description;
            }
        } else {
            // Fallback to hardcoded descriptions if serverData is not available
            switch(selectedOption.value) {
                case 'contrast':
                    quantizationDescription.textContent = 'Emphasizes edges while quantizing';
                    break;
                case 'natural':
                    quantizationDescription.textContent = 'Attempts a more natural color reduction using CIELAB color space';
                    break;
                case 'kmeans':
                    quantizationDescription.textContent = 'Uses k-means clustering to find dominant colors and match to palette';
                    break;
                case 'kmeans_brightness':
                    quantizationDescription.textContent = 'Uses k-means and maps clusters based on brightness';
                    break;
                default:
                    quantizationDescription.textContent = '';
            }
        }
    }

    function showLoadingModal() {
        if (loadingModalElement) {
            loadingModalElement.classList.add('show');
            isProcessing = true;
            console.log('Loading modal shown manually');
        }
    }

    function hideLoadingModal() {
        if (loadingModalElement) {
            loadingModalElement.classList.remove('show');
            isProcessing = false;
            console.log('Loading modal hidden manually');
        }
    }

    function showError(message) {
        if (errorModalElement) {
            // Set the error message
            document.getElementById('error-message').textContent = message;
            
            // Show the modal
            errorModalElement.classList.add('show');
        }
    }

    function hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('show');
        }
    }

    function clearFileInput() {
        if (fileElem) fileElem.value = '';
        lastValidImageFile = null;
        preview.innerHTML = '';
        if (processButton) processButton.disabled = true;
    }
});
