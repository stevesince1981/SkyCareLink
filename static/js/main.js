// MediFly Hospital MVP - Main JavaScript File

'use strict';

// Global variables
let botui;
let currentStep = 1;
let trackingInterval;

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('MediFly application initialized');
    
    // Initialize components based on current page
    const currentPage = getCurrentPage();
    
    switch(currentPage) {
        case 'intake':
            initializeIntakeForm();
            break;
        case 'confirm':
            initializeConfirmForm();
            break;
        case 'tracking':
            initializeTracking();
            break;
        default:
            console.log('Default page initialization');
    }
    
    // Initialize chatbot on all pages
    initializeChatbotWidget();
});

// Utility Functions
function getCurrentPage() {
    const path = window.location.pathname;
    if (path.includes('intake')) return 'intake';
    if (path.includes('confirm')) return 'confirm';
    if (path.includes('tracking')) return 'tracking';
    if (path.includes('results')) return 'results';
    if (path.includes('summary')) return 'summary';
    return 'index';
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Intake Form Functions
function initializeIntakeForm() {
    console.log('Initializing intake form');
    
    const form = document.getElementById('intake-form');
    if (!form) return;
    
    // Set minimum date to current date
    const departureInput = document.getElementById('departure_date');
    if (departureInput) {
        const now = new Date();
        const dateString = now.toISOString().slice(0, 16);
        departureInput.min = dateString;
    }
    
    // Navigation event listeners
    setupFormNavigation();
    
    // Form validation
    setupFormValidation();
    
    // Equipment recommendations based on severity
    setupSeverityRecommendations();
}

function setupFormNavigation() {
    // Next step buttons
    document.querySelectorAll('.next-step').forEach(button => {
        button.addEventListener('click', function() {
            const nextStep = parseInt(this.dataset.next);
            if (validateCurrentStep(currentStep)) {
                showStep(nextStep);
                currentStep = nextStep;
            }
        });
    });
    
    // Previous step buttons
    document.querySelectorAll('.prev-step').forEach(button => {
        button.addEventListener('click', function() {
            const prevStep = parseInt(this.dataset.prev);
            showStep(prevStep);
            currentStep = prevStep;
        });
    });
}

function showStep(stepNumber) {
    // Hide all steps
    document.querySelectorAll('.form-step').forEach(step => {
        step.classList.add('d-none');
    });
    
    // Show target step
    const targetStep = document.getElementById(`step-${stepNumber}`);
    if (targetStep) {
        targetStep.classList.remove('d-none');
        
        // Focus on first input
        const firstInput = targetStep.querySelector('input, select, textarea');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
        
        // Scroll to top of form
        targetStep.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function validateCurrentStep(step) {
    const stepElement = document.getElementById(`step-${step}`);
    if (!stepElement) return true;
    
    const requiredFields = stepElement.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });
    
    return isValid;
}

function validateField(field) {
    const value = field.value.trim();
    let isValid = true;
    let message = '';
    
    // Required field validation
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        message = 'This field is required.';
    }
    
    // Date validation
    if (field.type === 'datetime-local' && value) {
        const selectedDate = new Date(value);
        const now = new Date();
        
        if (selectedDate <= now) {
            isValid = false;
            message = 'Please select a future date and time.';
        }
    }
    
    // Update field appearance
    field.classList.toggle('is-invalid', !isValid);
    field.classList.toggle('is-valid', isValid && value);
    
    // Show/hide feedback
    const feedback = field.parentNode.querySelector('.invalid-feedback');
    if (feedback && message) {
        feedback.textContent = message;
    }
    
    return isValid;
}

function setupFormValidation() {
    const form = document.getElementById('intake-form');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Validate all fields
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!validateField(field)) {
                isValid = false;
            }
        });
        
        if (isValid) {
            // Show loading state
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
            submitBtn.disabled = true;
            
            // Submit form after brief delay
            setTimeout(() => {
                form.submit();
            }, 1000);
        } else {
            showAlert('Please complete all required fields correctly.', 'danger');
        }
    });
    
    // Real-time validation
    form.addEventListener('input', function(e) {
        if (e.target.hasAttribute('required')) {
            validateField(e.target);
        }
    });
}

function setupSeverityRecommendations() {
    const severitySelect = document.getElementById('severity');
    if (!severitySelect) return;
    
    severitySelect.addEventListener('change', function() {
        const severity = parseInt(this.value);
        const equipmentCheckboxes = document.querySelectorAll('input[name="equipment"]');
        
        // Clear previous selections
        equipmentCheckboxes.forEach(cb => cb.checked = false);
        
        // Make recommendations based on severity
        switch(severity) {
            case 5:
                // Critical - recommend ventilator and oxygen
                document.getElementById('ventilator').checked = true;
                document.getElementById('oxygen').checked = true;
                showAlert('For critical patients, Ventilator and Oxygen support are recommended.', 'info');
                break;
            case 4:
                // Serious - recommend oxygen
                document.getElementById('oxygen').checked = true;
                showAlert('For serious conditions, Oxygen support is recommended.', 'info');
                break;
            case 1:
            case 2:
                // Minor/Moderate - recommend escort only
                document.getElementById('escort').checked = true;
                showAlert('For stable patients, Medical escort may be sufficient.', 'info');
                break;
        }
    });
}

// Confirm Form Functions
function initializeConfirmForm() {
    console.log('Initializing confirm form');
    
    const form = document.getElementById('confirm-form');
    if (!form) return;
    
    // Setup cost calculator
    setupCostCalculator();
    
    // Form validation
    form.addEventListener('submit', function(e) {
        const consentCheckbox = document.getElementById('consent');
        if (!consentCheckbox.checked) {
            e.preventDefault();
            showAlert('You must provide consent to proceed with the booking.', 'danger');
            consentCheckbox.focus();
        }
    });
}

function setupCostCalculator() {
    const familySeatCheckbox = document.getElementById('family_seat');
    const vipCabinCheckbox = document.getElementById('vip_cabin');
    
    if (!familySeatCheckbox || !vipCabinCheckbox) return;
    
    const basePrice = parseInt(document.getElementById('base-cost').textContent.replace(/[$,]/g, ''));
    
    function updateTotalCost() {
        let total = basePrice;
        
        // Show/hide add-on costs
        const familySeatCost = document.getElementById('family-seat-cost');
        const vipCabinCost = document.getElementById('vip-cabin-cost');
        
        if (familySeatCheckbox.checked) {
            total += 5000;
            familySeatCost.classList.remove('d-none');
        } else {
            familySeatCost.classList.add('d-none');
        }
        
        if (vipCabinCheckbox.checked) {
            total += 10000;
            vipCabinCost.classList.remove('d-none');
        } else {
            vipCabinCost.classList.add('d-none');
        }
        
        // Update total
        document.getElementById('total-cost').textContent = '$' + total.toLocaleString();
    }
    
    familySeatCheckbox.addEventListener('change', updateTotalCost);
    vipCabinCheckbox.addEventListener('change', updateTotalCost);
}

// Tracking Functions
function initializeTracking() {
    console.log('Initializing tracking system');
    
    // Start auto-refresh for tracking updates
    trackingInterval = setInterval(updateTrackingStatus, 10000);
    
    // Manual refresh button
    const refreshButton = document.getElementById('refresh-status');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            updateTrackingStatus();
        });
    }
}

function updateTrackingStatus() {
    fetch('/api/tracking_status')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Tracking error:', data.error);
                return;
            }
            
            // Update progress bar
            const progressBar = document.getElementById('progress-bar');
            if (progressBar) {
                progressBar.style.width = data.progress + '%';
                progressBar.setAttribute('aria-valuenow', data.progress);
                progressBar.textContent = Math.round(data.progress) + '%';
            }
            
            // Update status message
            const statusElement = document.getElementById('current-status');
            if (statusElement) {
                statusElement.textContent = data.stage_name;
            }
            
            // Check if complete
            if (data.progress >= 100) {
                clearInterval(trackingInterval);
                showAlert('Transport completed! Redirecting to summary...', 'success');
                setTimeout(() => {
                    window.location.href = '/summary';
                }, 2000);
            }
        })
        .catch(error => {
            console.error('Failed to update tracking status:', error);
        });
}

// Chatbot Functions
function initializeChatbotWidget() {
    console.log('Initializing chatbot widget');
    
    // Setup chatbot toggle
    const chatbotHeader = document.querySelector('.chatbot-header');
    if (chatbotHeader) {
        chatbotHeader.addEventListener('click', toggleChatbot);
    }
    
    // Initialize BotUI if available
    if (typeof BotUI !== 'undefined') {
        initializeBotUI();
    }
}

function toggleChatbot() {
    const chatbotBody = document.getElementById('chatbot-body');
    const toggleIcon = document.querySelector('.chatbot-toggle');
    
    if (chatbotBody && toggleIcon) {
        const isVisible = chatbotBody.classList.contains('show');
        
        if (isVisible) {
            chatbotBody.classList.remove('show');
            chatbotBody.style.display = 'none';
            toggleIcon.classList.remove('rotated');
        } else {
            chatbotBody.classList.add('show');
            chatbotBody.style.display = 'block';
            toggleIcon.classList.add('rotated');
        }
    }
}

function initializeBotUI() {
    if (!document.getElementById('botui-app')) return;
    
    try {
        botui = new BotUI('botui-app');
        
        // Initial greeting
        botui.message.add({
            content: 'Hello! I\'m here to help you with your medical transport booking. What would you like to know?'
        }).then(() => {
            return botui.action.button({
                action: [
                    {
                        text: 'Equipment Options',
                        value: 'equipment'
                    },
                    {
                        text: 'Severity Levels',
                        value: 'severity'
                    },
                    {
                        text: 'Pricing Info',
                        value: 'pricing'
                    }
                ]
            });
        }).then((res) => {
            handleChatbotResponse(res.value);
        });
        
    } catch (error) {
        console.error('Failed to initialize BotUI:', error);
    }
}

function initializeChatbot(messages) {
    // Fallback chatbot implementation for when BotUI is not available
    console.log('Initializing simple chatbot with messages:', messages);
}

function handleChatbotResponse(choice) {
    if (!botui) return;
    
    let response = '';
    
    switch(choice) {
        case 'equipment':
            response = 'We provide various medical equipment including Ventilators for critical patients, ECMO machines for cardiac support, Incubators for neonatal care, Oxygen support, and medical escorts. Equipment selection depends on patient severity level.';
            break;
        case 'severity':
            response = 'Severity levels range from 1-5: Level 1 (Minor injuries like fractures), Level 2-3 (Moderate conditions requiring monitoring), Level 4 (Serious conditions needing ICU care), Level 5 (Critical patients requiring life support).';
            break;
        case 'pricing':
            response = 'Transport costs vary by provider and services: AirMed Response ($128,500 - ICU certified), REVA CriticalCare ($112,000 - Doctor onboard), MercyWings Global ($102,000 - Basic evacuation). Add-ons include Family Seat ($5,000) and VIP Cabin ($10,000).';
            break;
        default:
            response = 'I can help you understand our equipment options, severity levels, or pricing information. What would you like to know more about?';
    }
    
    botui.message.add({
        content: response
    }).then(() => {
        return botui.action.button({
            action: [
                {
                    text: 'Ask Another Question',
                    value: 'continue'
                },
                {
                    text: 'Close Chat',
                    value: 'close'
                }
            ]
        });
    }).then((res) => {
        if (res.value === 'continue') {
            // Restart the conversation
            setTimeout(() => {
                initializeBotUI();
            }, 500);
        } else {
            botui.message.add({
                content: 'Thank you for using MediFly! If you need more help, just click the chat button again.'
            });
        }
    });
}

// Utility function to format currency
function formatCurrency(amount) {
    return '$' + amount.toLocaleString();
}

// Accessibility helpers
function announceToScreenReader(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.style.position = 'absolute';
    announcement.style.left = '-10000px';
    announcement.style.width = '1px';
    announcement.style.height = '1px';
    announcement.style.overflow = 'hidden';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    setTimeout(() => {
        document.body.removeChild(announcement);
    }, 1000);
}

// Cleanup function
window.addEventListener('beforeunload', function() {
    if (trackingInterval) {
        clearInterval(trackingInterval);
    }
});

// Export functions for global access
window.MediFly = {
    initializeIntakeForm,
    initializeConfirmForm,
    initializeTracking,
    initializeChatbot,
    toggleChatbot,
    showAlert,
    formatCurrency
};
