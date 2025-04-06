// Global variables
let paletteDialogOpened = false;
let lastValidImageFile = null;

// DOM Elements
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
const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal')); //Corrected selector


// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    // Load initial palette swatches if a palette is selected
    if (paletteSelect && paletteSelect.value) {
        loadPaletteSwatches(paletteSelect.value);
    }

    // Set up event listeners
    setupFileHandling();
    setupPaletteHandling();
    setupProcessing();
});

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
            alert(`Palette "${data.name}" imported successfully!`);
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

            const formData = new FormData();
            formData.append('file', lastValidImageFile);
            formData.append('palette', paletteSelect.value);
            formData.append('quantization_mode', quantizationSelect.value);
            formData.append('max_resolution', document.getElementById('max_resolution').value);
            formData.append('upscale_factor', document.getElementById('upscale_factor').value);

            // Show the loading modal
            loadingModal.show();

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.error) throw new Error(data.error);
                document.getElementById('result-container').innerHTML = `<img src="${data.processed_image_url}" alt="Processed Image">`;
                document.getElementById('download-container').style.display = 'block';
                document.getElementById('download-link').href = data.processed_image_url;
                
                // Ensure the loading modal is hidden
                loadingModal.hide();
            })
            .catch(error => {
                // Hide the loading modal in case of error
                loadingModal.hide();
                showError(error.message);
            })
            .finally(() => {
                // Make sure the loading modal is always hidden, even if there's an issue with the promises
                setTimeout(() => {
                    loadingModal.hide();
                }, 500);
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
        img.classList.add('mb-2');
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
            palettePreview.innerHTML = '<p class="text-danger">Failed to load palette.</p>';
        });
}

function showError(message) {
    const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
    document.getElementById('error-message').textContent = message;
    errorModal.show();
}

function clearFileInput() {
    if (fileElem) fileElem.value = '';
    lastValidImageFile = null;
    preview.innerHTML = '';
    if (processButton) processButton.disabled = true;
}

//This part is kept from the original code because it's not directly addressed in the edited snippet and is still relevant
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
