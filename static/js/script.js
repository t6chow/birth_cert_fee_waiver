// Global variables
let history = [];
let currentTab = 'natural';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    checkApiStatus();
    loadHistory();
});

// Tab switching functionality
function switchTab(tabName) {
    // Remove active class from all tabs
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    // Add active class to selected tab
    document.querySelector(`button[onclick="switchTab('${tabName}')"]`).classList.add('active');
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    currentTab = tabName;
}

// Toggle child name field and labels based on signup type
function toggleSignupType() {
    const signupTypeSelect = document.getElementById('signupType');
    const childNameGroup = document.getElementById('childNameGroup');
    const adultNameLabel = document.getElementById('adultNameLabel');
    
    if (signupTypeSelect.value === 'child') {
        childNameGroup.style.display = 'block';
        adultNameLabel.innerHTML = '<i class="fas fa-user"></i> Your Name (Parent/Guardian) *';
        childNameGroup.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else if (signupTypeSelect.value === 'self') {
        childNameGroup.style.display = 'none';
        adultNameLabel.innerHTML = '<i class="fas fa-user"></i> Your Name *';
        document.getElementById('childName').value = '';
    } else {
        childNameGroup.style.display = 'none';
        adultNameLabel.innerHTML = '<i class="fas fa-user"></i> Your Name *';
        document.getElementById('childName').value = '';
    }
}

// Check API status
async function checkApiStatus() {
    const statusCard = document.getElementById('api-status');
    const statusText = statusCard.querySelector('.status-text');
    
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        if (data.api_key_configured) {
            statusCard.classList.add('success');
            statusText.textContent = 'Ready';
            statusCard.querySelector('i').className = 'fas fa-check-circle';
        } else {
            statusCard.classList.add('error');
            statusText.textContent = 'API key not configured';
            statusCard.querySelector('i').className = 'fas fa-exclamation-triangle';
        }
    } catch (error) {
        statusCard.classList.add('error');
        statusText.textContent = 'Connection error';
        statusCard.querySelector('i').className = 'fas fa-times-circle';
    }
}

// Test webhook connection
async function testWebhook() {
    const statusCard = document.getElementById('webhook-status');
    const statusText = statusCard.querySelector('.status-text');
    const button = statusCard.querySelector('button');
    
    // Show loading state
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Testing...';
    statusText.textContent = 'Testing connection...';
    
    try {
        const response = await fetch('/api/test-webhook', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            statusCard.classList.remove('error');
            statusCard.classList.add('success');
            statusText.textContent = 'Connection successful';
            statusCard.querySelector('i').className = 'fas fa-check-circle';
        } else {
            statusCard.classList.remove('success');
            statusCard.classList.add('error');
            statusText.textContent = `Connection failed: ${data.error}`;
            statusCard.querySelector('i').className = 'fas fa-times-circle';
        }
    } catch (error) {
        statusCard.classList.remove('success');
        statusCard.classList.add('error');
        statusText.textContent = 'Connection error';
        statusCard.querySelector('i').className = 'fas fa-times-circle';
    } finally {
        // Reset button
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-link"></i> Test Connection';
    }
}

// Get form data based on current tab
function getFormData() {
    if (currentTab === 'natural') {
        return {
            input_type: 'natural',
            input: document.getElementById('naturalInput').value.trim()
        };
    } else {
        const signupType = document.getElementById('signupType').value;
        return {
            input_type: 'structured',
            signup_type: signupType,
            adult_name: document.getElementById('adultName').value.trim(),
            email_address: document.getElementById('emailAddress').value.trim() || null,
            child_name: document.getElementById('childName').value.trim() || null
        };
    }
}

// Validate form data
function validateForm(formData) {
    if (formData.input_type === 'natural') {
        if (!formData.input) {
            return { valid: false, message: 'Please provide some information about your situation.' };
        }
        if (formData.input.length < 10) {
            return { valid: false, message: 'Please provide more detailed information.' };
        }
    } else {
        if (!formData.signup_type) {
            return { valid: false, message: 'Please select who you are signing up.' };
        }
        if (!formData.adult_name) {
            return { valid: false, message: 'Please enter your name.' };
        }
        if (!formData.email_address) {
            return { valid: false, message: 'Please enter your email address.' };
        }
        if (formData.signup_type === 'child' && !formData.child_name) {
            return { valid: false, message: 'Please enter the child\'s name when signing up for a child.' };
        }
    }
    
    return { valid: true };
}

// Process form data
async function processForm() {
    const formData = getFormData();
    const validation = validateForm(formData);
    
    if (!validation.valid) {
        showError(validation.message);
        return;
    }
    
    // Show loading modal
    showLoading(true);
    
    // Disable the process button
    const processBtn = document.getElementById('processBtn');
    processBtn.disabled = true;
    processBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    
    try {
        const response = await fetch('/api/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        // Add to history
        const historyItem = {
            timestamp: new Date().toLocaleString(),
            input: formData,
            result: result
        };
        
        history.unshift(historyItem);
        saveHistory();
        
        // Display results
        displayResults(result);
        updateHistoryDisplay();
        
    } catch (error) {
        showError('Network error occurred. Please try again.');
        console.error('Processing error:', error);
    } finally {
        // Hide loading modal and reset button
        showLoading(false);
        processBtn.disabled = false;
        processBtn.innerHTML = '<i class="fas fa-cogs"></i> Process & Submit';
    }
}

// Display results
function displayResults(result) {
    const resultsSection = document.getElementById('resultsSection');
    const resultsContent = document.getElementById('resultsContent');
    
    let html = '';
    
    if (result.success) {
        html = `
            <div class="result-card result-success">
                <div class="result-header">
                    <div class="result-status success">
                        <i class="fas fa-check-circle"></i>
                        Success - Data processed and webhook sent
                    </div>
                </div>
                <div class="data-grid">
        `;
        
        // Display extracted form data
        if (result.form_data) {
            Object.entries(result.form_data).forEach(([key, value]) => {
                if (value !== null && value !== '') {
                    html += `
                        <div class="data-item">
                            <div class="data-label">${key.replace(/_/g, ' ')}</div>
                            <div class="data-value">${value}</div>
                        </div>
                    `;
                }
            });
        }
        
        html += `
                </div>
        `;
        
        // Display webhook response
        if (result.webhook_result) {
            html += `
                <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                    <h4><i class="fas fa-link"></i> Webhook Response</h4>
                    <div class="data-grid" style="margin-top: 15px;">
                        <div class="data-item">
                            <div class="data-label">Status Code</div>
                            <div class="data-value">${result.webhook_result.status_code || 'N/A'}</div>
                        </div>
                        <div class="data-item">
                            <div class="data-label">Response</div>
                            <div class="data-value">${result.webhook_result.response_text || 'N/A'}</div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        html += `</div>`;
        
    } else {
        html = `
            <div class="result-card result-error">
                <div class="result-header">
                    <div class="result-status error">
                        <i class="fas fa-times-circle"></i>
                        Error - ${result.error || 'Unknown error occurred'}
                    </div>
                </div>
        `;
        
        // Show partially extracted data if available
        if (result.extracted_data) {
            html += `
                <div style="margin-top: 15px;">
                    <h4><i class="fas fa-info-circle"></i> Partially Extracted Data</h4>
                    <div class="data-grid" style="margin-top: 15px;">
            `;
            
            Object.entries(result.extracted_data).forEach(([key, value]) => {
                if (value !== null && value !== '') {
                    html += `
                        <div class="data-item">
                            <div class="data-label">${key.replace(/_/g, ' ')}</div>
                            <div class="data-value">${value}</div>
                        </div>
                    `;
                }
            });
            
            html += `
                    </div>
                </div>
            `;
        }
        
        html += `</div>`;
    }
    
    resultsContent.innerHTML = html;
    resultsSection.style.display = 'block';
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Update history display
function updateHistoryDisplay() {
    const historySection = document.getElementById('historySection');
    const historyContent = document.getElementById('historyContent');
    
    if (history.length === 0) {
        historySection.style.display = 'none';
        return;
    }
    
    let html = '';
    
    history.forEach((item, index) => {
        const isSuccess = item.result.success;
        const inputText = item.input.input_type === 'natural' 
            ? item.input.input 
            : `Name: ${item.input.adult_name || item.input.name_of_requestor || 'N/A'}${item.input.email_address ? `, Email: ${item.input.email_address}` : ''}, Type: ${item.input.signup_type || (item.input.request_on_behalf === 'y' ? 'child' : 'self')}${item.input.child_name || item.input.name_of_child ? `, Child: ${item.input.child_name || item.input.name_of_child}` : ''}`;`
        
        html += `
            <div class="history-item ${isSuccess ? 'result-success' : 'result-error'}">
                <div class="result-header">
                    <div class="result-status ${isSuccess ? 'success' : 'error'}">
                        <i class="fas fa-${isSuccess ? 'check-circle' : 'times-circle'}"></i>
                        ${isSuccess ? 'Success' : 'Error'}
                    </div>
                    <small style="color: #666;">${item.timestamp}</small>
                </div>
                <div style="margin: 10px 0;">
                    <strong>Input:</strong> ${inputText.substring(0, 100)}${inputText.length > 100 ? '...' : ''}
                </div>
        `;
        
        if (isSuccess && item.result.form_data) {
            html += `<div class="data-grid" style="margin-top: 15px;">`;
            Object.entries(item.result.form_data).forEach(([key, value]) => {
                if (value !== null && value !== '') {
                    html += `
                        <div class="data-item">
                            <div class="data-label">${key.replace(/_/g, ' ')}</div>
                            <div class="data-value">${value}</div>
                        </div>
                    `;
                }
            });
            html += `</div>`;
        } else if (!isSuccess) {
            html += `<div style="color: #f56565; margin-top: 10px;"><strong>Error:</strong> ${item.result.error}</div>`;
        }
        
        html += `</div>`;
    });
    
    historyContent.innerHTML = html;
    historySection.style.display = 'block';
}

// Clear form
function clearForm() {
    if (currentTab === 'natural') {
        document.getElementById('naturalInput').value = '';
    } else {
        document.getElementById('signupType').value = '';
        document.getElementById('adultName').value = '';
        document.getElementById('emailAddress').value = '';
        document.getElementById('childName').value = '';
        document.getElementById('childNameGroup').style.display = 'none';
        document.getElementById('adultNameLabel').innerHTML = '<i class="fas fa-user"></i> Your Name *';
    }
    
    // Hide results
    document.getElementById('resultsSection').style.display = 'none';
}

// Clear history
function clearHistory() {
    if (confirm('Are you sure you want to clear the processing history?')) {
        history = [];
        saveHistory();
        document.getElementById('historySection').style.display = 'none';
    }
}

// Show/hide loading modal
function showLoading(show) {
    const modal = document.getElementById('loadingModal');
    modal.style.display = show ? 'block' : 'none';
}

// Show error message
function showError(message) {
    // Create a simple error display
    const existingError = document.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: #f56565;
        color: white;
        padding: 15px 25px;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(245, 101, 101, 0.3);
        z-index: 1001;
        max-width: 500px;
        text-align: center;
        animation: slideDown 0.3s ease-out;
    `;
    
    errorDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${message}`;
    
    document.body.appendChild(errorDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.remove();
        }
    }, 5000);
    
    // Add click to dismiss
    errorDiv.addEventListener('click', () => {
        errorDiv.remove();
    });
}

// Save history to localStorage
function saveHistory() {
    try {
        localStorage.setItem('dignifi_history', JSON.stringify(history));
    } catch (error) {
        console.warn('Could not save history to localStorage:', error);
    }
}

// Load history from localStorage
function loadHistory() {
    try {
        const saved = localStorage.getItem('dignifi_history');
        if (saved) {
            history = JSON.parse(saved);
            updateHistoryDisplay();
        }
    } catch (error) {
        console.warn('Could not load history from localStorage:', error);
        history = [];
    }
}

// Add CSS animation for error message
const style = document.createElement('style');
style.textContent = `
    @keyframes slideDown {
        from {
            transform: translate(-50%, -100%);
            opacity: 0;
        }
        to {
            transform: translate(-50%, 0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);