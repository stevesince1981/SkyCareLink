// MediFly Hospital MVP - Main JavaScript File

'use strict';

// Global variables
let botui;
let currentStep = 1;
let trackingInterval;

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('MediFly application initialized');
    
    // Initialize Bootstrap tooltips
    initializeTooltips();
    
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
        case 'results':
            initializeResultsPage();
            break;
        default:
            console.log('Default page initialization');
    }
    
    // Initialize chatbot on all pages
    initializeChatbotWidget();
    
    // Add smooth scrolling to all anchor links
    addSmoothScrolling();
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

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Add smooth scrolling
function addSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Results page enhancements
function initializeResultsPage() {
    console.log('Initializing results page');
    
    // Add hover animations to provider cards
    const providerCards = document.querySelectorAll('.provider-card');
    providerCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
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
        
        // Make recommendations based on severity and update chatbot
        let recommendationMessage = '';
        switch(severity) {
            case 5:
                // Critical - recommend ventilator and oxygen
                document.getElementById('ventilator').checked = true;
                document.getElementById('oxygen').checked = true;
                recommendationMessage = 'For critical patients (Severity 5), Ventilator and Oxygen support are strongly recommended. Consider ECMO for cardiac cases.';
                showAlert('Critical patient: Ventilator and Oxygen support recommended.', 'warning');
                break;
            case 4:
                // Serious - recommend oxygen and consider ventilator
                document.getElementById('oxygen').checked = true;
                recommendationMessage = 'For serious conditions (Severity 4), Oxygen support is recommended. Monitor if Ventilator support may be needed.';
                showAlert('Serious condition: Oxygen support recommended.', 'info');
                break;
            case 3:
                // Moderate serious - recommend oxygen
                document.getElementById('oxygen').checked = true;
                recommendationMessage = 'For moderate serious conditions (Severity 3), Oxygen support and medical monitoring are recommended.';
                showAlert('Moderate serious: Oxygen support recommended.', 'info');
                break;
            case 2:
                // Stable moderate - recommend escort
                document.getElementById('escort').checked = true;
                recommendationMessage = 'For stable moderate patients (Severity 2), Medical escort with basic monitoring is usually sufficient.';
                showAlert('Stable condition: Medical escort recommended.', 'success');
                break;
            case 1:
                // Minor - recommend escort only
                document.getElementById('escort').checked = true;
                recommendationMessage = 'For minor conditions (Severity 1), Medical escort only is typically sufficient for safe transport.';
                showAlert('Minor condition: Medical escort is sufficient.', 'success');
                break;
        }
        
        // Update chatbot with severity-specific recommendation
        if (window.currentSeverityLevel !== severity) {
            window.currentSeverityLevel = severity;
            triggerChatbotRecommendation(recommendationMessage);
        }
    });
}

function triggerChatbotRecommendation(message) {
    // Add severity recommendation to chatbot if available
    if (typeof botui !== 'undefined' && botui) {
        botui.message.add({
            content: message,
            delay: 1000
        });
    }
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
    
    // Clear any existing interval
    if (trackingInterval) {
        clearInterval(trackingInterval);
    }
    
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
        
        // Enhanced initial greeting
        botui.message.add({
            content: 'Welcome to MediFly! I can help with equipment selection, severity levels, and provide recommendations based on your patient\'s condition.'
        }).then(() => {
            return botui.action.button({
                action: [
                    {
                        text: 'Equipment Help',
                        value: 'equipment'
                    },
                    {
                        text: 'Severity Guide',
                        value: 'severity'
                    },
                    {
                        text: 'Affiliate Comparison',
                        value: 'providers'
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
            response = 'Our medical equipment includes: Ventilators (for respiratory support), ECMO machines (cardiac/lung support), Incubators (neonatal care), Oxygen support (basic respiratory aid), and Medical escorts (professional supervision). I recommend equipment based on your selected severity level.';
            break;
        case 'severity':
            response = 'Severity Guide: Level 1 (Minor - broken bones, stable injuries), Level 2 (Moderate - needs monitoring), Level 3 (Serious - immediate medical attention), Level 4 (Critical - ICU care required), Level 5 (Life-threatening - ventilator/life support needed). Select a level and I\'ll recommend appropriate equipment.';
            break;
        case 'providers':
            response = 'Affiliate comparison: AirMed Response (Premium - $128,500, ICU certified, 3h ETA), REVA CriticalCare (Standard - $112,000, Doctor onboard, 5h ETA), MercyWings Global (Budget - $102,000, Basic evacuation, 6h ETA). Choose based on urgency and medical needs.';
            break;
        case 'pricing':
            response = 'Base costs: AirMed $128,500, REVA $112,000, MercyWings $102,000. Optional add-ons: Family Seat (+$5,000 - allows one family member), VIP Cabin (+$10,000 - enhanced comfort and privacy). Prices include medical team and basic equipment.';
            break;
        default:
            response = 'I can help with equipment selection, severity assessment, provider comparison, or pricing details. What specific information do you need?';
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
