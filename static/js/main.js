// Main JavaScript for Pixel Art Generator

// DOM Elements
document.addEventListener('DOMContentLoaded', function() {
    // Only run this code if these elements exist (they might not on error pages)
    if (document.getElementById('drop-area')) {
        initializeApp();
    }
});

function initializeApp() {
    const dropArea = document.getElementById('drop-area');
    const fileElem = document.getElementById('fileElem');
    const fileSelect = document.getElementById('fileSelect');
    const preview = document.getElementById('preview');
    const processButton = document.getElementById('process-button');
    const paletteSelect = document.getElementById('palette');
    const palettePreview = document.getElementById('palette-preview');
    const quantizationSelect = document.getElementById('quantization_mode');
    const quantizationDescription = document.getElementById('quantization_description');
    const resultContainer = document.getElementById('result-container');
    const downloadContainer = document.getElementById('download-container');
    const downloadLink = document.getElementById('download-link');
    const settingsForm = document.getElementById('settings-form');
    const importPaletteLink = document.getElementById('import-palette-link');
    const importPaletteInput = document.getElementById('import-palette-file');

    // Prevent defaults for drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Highlight drop area when dragging over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        dropArea.classList.add('highlight');
    }

    function unhighlight() {
        dropArea.classList.remove('highlight');
    }

    // Handle dropped files
    dropArea.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            handleFiles(files);
        }
    }

    // Handle file selection via button
    // First, remove any existing event listeners to prevent duplicates
    const oldFileSelect = fileSelect.cloneNode(true);
    fileSelect.parentNode.replaceChild(oldFileSelect, fileSelect);
    
    // Reassign the variable to the new element
    const newFileSelect = document.getElementById('fileSelect');
    newFileSelect.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        fileElem.click();
    }, { once: true });

    // Remove and reattach the change listener to prevent duplicates
    const oldFileElem = fileElem.cloneNode(true);
    fileElem.parentNode.replaceChild(oldFileElem, fileElem);
    
    // Reassign the variable to the new element
    const newFileElem = document.getElementById('fileElem');
    newFileElem.addEventListener('change', () => {
        handleFiles(newFileElem.files);
    });

    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            
            // Check if file is an image
            if (!file.type.match('image.*')) {
                showError('Please select an image file.');
                clearFileInput();
                return;
            }
            
            // Clear any previous preview
            preview.innerHTML = '';
            
            // Create preview image
            const img = document.createElement('img');
            img.classList.add('mb-2');
            img.file = file;
            preview.appendChild(img);
            
            // Read the file
            const reader = new FileReader();
            reader.onload = (e) => {
                img.src = e.target.result;
            };
            reader.readAsDataURL(file);
            
            // Enable the process button
            processButton.disabled = false;
        }
    }

    function clearFileInput() {
        fileElem.value = '';
        preview.innerHTML = '';
        processButton.disabled = true;
    }

    // Load palette swatches when a palette is selected
    if (paletteSelect) {
        paletteSelect.addEventListener('change', () => {
            loadPaletteSwatches(paletteSelect.value);
        });

        // Load initial palette swatches
        if (paletteSelect.value) {
            loadPaletteSwatches(paletteSelect.value);
        }
    }

    function loadPaletteSwatches(paletteId) {
        fetch(`/palette/${paletteId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load palette');
                }
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
                palettePreview.innerHTML = '<p class="text-danger">Failed to load palette.</p>';
            });
    }

    function showError(message) {
        // Check if we have Bootstrap's Modal
        if (typeof bootstrap !== 'undefined' && document.getElementById('errorModal')) {
            const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
            const errorMessage = document.getElementById('error-message');
            errorMessage.textContent = message;
            errorModal.show();
        } else {
            // Fallback to alert
            alert(message);
        }
    }
    
    // Update quantization description when mode is changed
    if (quantizationSelect && quantizationDescription) {
        quantizationSelect.addEventListener('change', () => {
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
        });
        
        // Set initial quantization description
        const initialOption = quantizationSelect.options[quantizationSelect.selectedIndex];
        // Check if serverData exists first
        if (window.serverData && window.serverData.quantizationModes) {
            const initialMode = window.serverData.quantizationModes.find(mode => mode.value === initialOption.value);
            if (initialMode) {
                quantizationDescription.textContent = initialMode.description;
            }
        } else {
            // Fallback to hardcoded descriptions if serverData is not available
            switch(initialOption.value) {
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
    
    // Process image when button is clicked
    if (processButton) {
        processButton.addEventListener('click', () => {
            if (fileElem.files.length === 0) {
                showError('Please select an image first.');
                return;
            }
            
            // Show loading modal
            const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
            loadingModal.show();
            
            // Create form data
            const formData = new FormData();
            formData.append('file', fileElem.files[0]);
            formData.append('palette', paletteSelect.value);
            formData.append('quantization_mode', quantizationSelect.value);
            formData.append('max_resolution', document.getElementById('max_resolution').value);
            formData.append('upscale_factor', document.getElementById('upscale_factor').value);
            
            // Send the request
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || 'Failed to process image');
                    });
                }
                return response.json();
            })
            .then(data => {
                // Hide loading modal
                loadingModal.hide();
                
                // Show result
                resultContainer.innerHTML = `
                    <img src="${data.processed_image_url}" alt="Processed Image" class="img-fluid">
                    <p class="mt-2">Processed with ${data.palette_name} palette</p>
                `;
                
                // Show download button
                downloadContainer.style.display = 'block';
                downloadLink.href = data.processed_image_url;
                downloadLink.download = `pixel_art_${Date.now()}.png`;
            })
            .catch(error => {
                // Hide loading modal
                loadingModal.hide();
                
                // Show error
                showError(error.message);
            });
        });
    }
    
    // Handle palette import
    if (importPaletteLink && importPaletteInput) {
        // First, remove any existing event listeners to prevent duplicates
        const oldImportPaletteLink = importPaletteLink.cloneNode(true);
        importPaletteLink.parentNode.replaceChild(oldImportPaletteLink, importPaletteLink);
        
        // Reassign the variable to the new element
        const newImportPaletteLink = document.getElementById('import-palette-link');
        newImportPaletteLink.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            importPaletteInput.click();
        }, { once: true });
        
        // Remove and reattach the change listener to prevent duplicates
        const oldImportPaletteInput = importPaletteInput.cloneNode(true);
        importPaletteInput.parentNode.replaceChild(oldImportPaletteInput, importPaletteInput);
        
        // Reassign the variable to the new element
        const newImportPaletteInput = document.getElementById('import-palette-file');
        newImportPaletteInput.addEventListener('change', () => {
            if (newImportPaletteInput.files.length > 0) {
                const file = newImportPaletteInput.files[0];
                
                // Check if file is a text/hex file
                if (!file.name.endsWith('.hex') && !file.name.endsWith('.txt')) {
                    showError('Please select a valid palette file (.hex or .txt)');
                    newImportPaletteInput.value = '';
                    return;
                }
                
                const formData = new FormData();
                formData.append('palette_file', file);
                formData.append('name', file.name.replace(/\.[^/.]+$/, '')); // Remove extension for name
                
                fetch('/palette/import', {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(data => {
                            throw new Error(data.error || 'Failed to import palette');
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    // Add the new palette to the select
                    const option = document.createElement('option');
                    option.value = data.id;
                    option.text = data.name;
                    paletteSelect.add(option);
                    
                    // Select the new palette
                    paletteSelect.value = data.id;
                    
                    // Load the new palette swatches
                    loadPaletteSwatches(data.id);
                    
                    // Show success message
                    alert(`Palette "${data.name}" imported successfully!`);
                })
                .catch(error => {
                    showError(error.message);
                })
                .finally(() => {
                    // Clear the file input
                    importPaletteInput.value = '';
                });
            }
        });
    }
}