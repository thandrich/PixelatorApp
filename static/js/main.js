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
    fileSelect.addEventListener('click', () => {
        fileElem.click();
    });

    fileElem.addEventListener('change', () => {
        handleFiles(fileElem.files);
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
}