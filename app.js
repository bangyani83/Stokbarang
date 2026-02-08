/**
 * FIFO Stock Management - Main JavaScript File
 */

// Global variables
let debounceTimer;

// Debounce function for search inputs
function debounce(func, wait) {
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(debounceTimer);
            func(...args);
        };
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(later, wait);
    };
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('id-ID', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('id-ID', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

// Show loading spinner
function showLoading(element) {
    if (!element) return;
    
    element.innerHTML = `
        <div class="spinner"></div>
        <span class="ml-2">Memproses...</span>
    `;
    element.disabled = true;
}

// Hide loading spinner
function hideLoading(element, originalText) {
    if (!element) return;
    
    element.innerHTML = originalText;
    element.disabled = false;
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transition-all duration-300 ${
        type === 'success' ? 'bg-green-500 text-white' :
        type === 'error' ? 'bg-red-500 text-white' :
        type === 'warning' ? 'bg-yellow-500 text-white' :
        'bg-blue-500 text-white'
    }`;
    toast.innerHTML = `
        <div class="flex items-center">
            <i class="fas fa-${
                type === 'success' ? 'check-circle' :
                type === 'error' ? 'exclamation-circle' :
                type === 'warning' ? 'exclamation-triangle' :
                'info-circle'
            } mr-2"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Confirm dialog
function confirmDialog(message, callback) {
    const dialog = document.createElement('div');
    dialog.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
    dialog.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div class="p-6">
                <div class="flex items-center mb-4">
                    <i class="fas fa-exclamation-triangle text-yellow-500 text-2xl mr-3"></i>
                    <h3 class="text-lg font-semibold text-gray-800">Konfirmasi</h3>
                </div>
                <p class="text-gray-600 mb-6">${message}</p>
                <div class="flex justify-end space-x-3">
                    <button onclick="this.closest('.fixed').remove()" 
                            class="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50">
                        Batal
                    </button>
                    <button onclick="this.closest('.fixed').remove(); callback()" 
                            class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">
                        Ya, Lanjutkan
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Replace callback with actual function
    const confirmBtn = dialog.querySelector('button:last-child');
    confirmBtn.onclick = function() {
        dialog.remove();
        callback();
    };
    
    document.body.appendChild(dialog);
}

// Export table to CSV
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    for (const row of rows) {
        const rowData = [];
        const cols = row.querySelectorAll('td, th');
        
        for (const col of cols) {
            // Clean up the data
            let data = col.innerText
                .replace(/(\r\n|\n|\r)/gm, '')
                .replace(/(\s\s)/gm, ' ')
                .trim();
            
            // Escape quotes
            data = data.replace(/"/g, '""');
            
            // Add quotes if data contains comma
            if (data.includes(',')) {
                data = `"${data}"`;
            }
            
            rowData.push(data);
        }
        
        csv.push(rowData.join(','));
    }
    
    // Download CSV file
    const csvFile = new Blob([csv.join('\n')], { type: 'text/csv' });
    const downloadLink = document.createElement('a');
    downloadLink.download = filename;
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

// Validate form
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    for (const field of requiredFields) {
        if (!field.value.trim()) {
            field.classList.add('border-red-500');
            isValid = false;
            
            // Show error message
            let errorDiv = field.parentNode.querySelector('.field-error');
            if (!errorDiv) {
                errorDiv = document.createElement('div');
                errorDiv.className = 'field-error text-red-500 text-sm mt-1';
                field.parentNode.appendChild(errorDiv);
            }
            errorDiv.textContent = 'Field ini harus diisi';
        } else {
            field.classList.remove('border-red-500');
            
            // Remove error message
            const errorDiv = field.parentNode.querySelector('.field-error');
            if (errorDiv) {
                errorDiv.remove();
            }
        }
    }
    
    return isValid;
}

// Initialize tooltips
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', function() {
            const tooltipText = this.getAttribute('data-tooltip');
            const tooltip = document.createElement('div');
            tooltip.className = 'absolute z-50 px-2 py-1 text-sm text-white bg-gray-900 rounded shadow-lg';
            tooltip.textContent = tooltipText;
            
            const rect = this.getBoundingClientRect();
            tooltip.style.top = `${rect.top - 30}px`;
            tooltip.style.left = `${rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;
            
            tooltip.id = 'current-tooltip';
            document.body.appendChild(tooltip);
        });
        
        element.addEventListener('mouseleave', function() {
            const tooltip = document.getElementById('current-tooltip');
            if (tooltip) {
                tooltip.remove();
            }
        });
    });
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Berhasil disalin ke clipboard', 'success');
    }).catch(err => {
        console.error('Failed to copy: ', err);
        showToast('Gagal menyalin', 'error');
    });
}

// Auto-save form data
function setupAutoSave(formId, key) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    // Load saved data
    const savedData = localStorage.getItem(key);
    if (savedData) {
        try {
            const data = JSON.parse(savedData);
            Object.keys(data).forEach(fieldName => {
                const field = form.querySelector(`[name="${fieldName}"]`);
                if (field) {
                    field.value = data[fieldName];
                }
            });
        } catch (e) {
            console.error('Failed to load saved data:', e);
        }
    }
    
    // Save on input
    form.addEventListener('input', debounce(() => {
        const formData = new FormData(form);
        const data = {};
        for (const [key, value] of formData.entries()) {
            data[key] = value;
        }
        localStorage.setItem(key, JSON.stringify(data));
    }, 1000));
    
    // Clear on submit
    form.addEventListener('submit', () => {
        localStorage.removeItem(key);
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initTooltips();
    
    // Auto-format currency inputs
    const currencyInputs = document.querySelectorAll('input[data-currency]');
    currencyInputs.forEach(input => {
        input.addEventListener('blur', function() {
            const value = parseFloat(this.value);
            if (!isNaN(value)) {
                this.value = formatCurrency(value);
            }
        });
        
        input.addEventListener('focus', function() {
            const value = parseFloat(this.value.replace(/[^\d.-]/g, ''));
            if (!isNaN(value)) {
                this.value = value;
            }
        });
    });
    
    // Auto-format date inputs
    const dateInputs = document.querySelectorAll('input[type="date"]');
    const today = new Date().toISOString().split('T')[0];
    dateInputs.forEach(input => {
        if (!input.value) {
            input.value = today;
        }
    });
    
    // Confirm before leaving unsaved changes
    window.addEventListener('beforeunload', function(e) {
        const forms = document.querySelectorAll('form');
        let hasUnsavedChanges = false;
        
        forms.forEach(form => {
            if (form.classList.contains('unsaved')) {
                hasUnsavedChanges = true;
            }
        });
        
        if (hasUnsavedChanges) {
            e.preventDefault();
            e.returnValue = '';
        }
    });
    
    // Mark forms as unsaved when modified
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('input', function() {
            this.classList.add('unsaved');
        });
        
        form.addEventListener('submit', function() {
            this.classList.remove('unsaved');
        });
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl+S to save
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            const saveButton = document.querySelector('button[type="submit"]');
            if (saveButton) {
                saveButton.click();
            }
        }
        
        // Ctrl+F to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            const searchInput = document.querySelector('input[type="search"], #searchInput');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal, [role="dialog"]');
            modals.forEach(modal => {
                if (modal.style.display !== 'none') {
                    modal.style.display = 'none';
                }
            });
        }
    });
    
    // Responsive table scrolling
    const tables = document.querySelectorAll('.overflow-x-auto table');
    tables.forEach(table => {
        const wrapper = table.closest('.overflow-x-auto');
        if (wrapper && wrapper.scrollWidth > wrapper.clientWidth) {
            wrapper.classList.add('shadow-inner');
        }
    });
});

// Export functions to global scope
window.FIFOApp = {
    showToast,
    confirmDialog,
    exportTableToCSV,
    formatCurrency,
    formatDate,
    copyToClipboard,
    setupAutoSave
};
