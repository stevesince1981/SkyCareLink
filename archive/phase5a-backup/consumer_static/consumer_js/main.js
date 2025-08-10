// MediFly Consumer MVP - Main JavaScript

// Global variables
let botui;

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('MediFly Consumer application initialized');
    
    // Initialize Bootstrap tooltips
    initializeTooltips();
    
    // Initialize components based on current page
    const currentPage = getCurrentPage();
    
    switch(currentPage) {
        case 'intake':
            initializeIntakeForm();
            break;
        case 'results':
            initializeResultsPage();
            break;
        case 'confirm':
            initializeConfirmForm();
            break;
        case 'tracking':
            initializeTracking();
            break;
        case 'summary':
            initializeSummaryPage();
            break;
        default:
            console.log('Landing page or other page initialization');
    }
    
    // Initialize chatbot on all pages
    initializeChatbotWidget();
    
    // Add smooth scrolling to all anchor links
    addSmoothScrolling();
});

// Utility Functions
function getCurrentPage() {
    const path = window.location.pathname;
    if (path.includes('/intake')) return 'intake';
    if (path.includes('/results')) return 'results';
    if (path.includes('/confirm')) return 'confirm';
    if (path.includes('/tracking')) return 'tracking';
    if (path.includes('/summary')) return 'summary';
    if (path.includes('/admin')) return 'admin';
    return 'landing';
}

function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

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

// Page-specific initialization functions
function initializeIntakeForm() {
    console.log('Initializing intake form');
    setupSeverityRecommendations();
    setupFormValidation();
}

function initializeResultsPage() {
    console.log('Initializing results page');
    
    // Add hover animations to provider cards
    const providerCards = document.querySelectorAll('.provider-card');
    providerCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
}

function initializeConfirmForm() {
    console.log('Initializing confirm form');
    setupCostCalculator();
    setupAddonInteractions();
}

function initializeTracking() {
    console.log('Initializing tracking page');
    // Tracking functionality is handled in the template script
}

function initializeSummaryPage() {
    console.log('Initializing summary page');
    // Add celebration animations
    const successIcon = document.querySelector('.success-icon i');
    if (successIcon) {
        successIcon.style.animation = 'bounce 2s infinite';
    }
}

// Intake Form Functions
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
                document.getElementById('ventilator').checked = true;
                document.getElementById('oxygen').checked = true;
                recommendationMessage = 'For life-threatening conditions (Severity 5), Ventilator and Oxygen support are essential. Consider ECMO for cardiac cases.';
                showRecommendationAlert('For life-threatening conditions, Ventilator and Oxygen support are strongly recommended.', 'warning');
                break;
            case 4:
                document.getElementById('oxygen').checked = true;
                recommendationMessage = 'For critical conditions (Severity 4), Oxygen support is recommended. Monitor if Ventilator support may be needed.';
                showRecommendationAlert('For critical conditions, Oxygen support is recommended. Consider Ventilator if needed.', 'info');
                break;
            case 3:
                document.getElementById('oxygen').checked = true;
                recommendationMessage = 'For serious conditions (Severity 3), Oxygen support and medical monitoring are recommended.';
                showRecommendationAlert('For serious conditions, Oxygen support is recommended.', 'info');
                break;
            case 2:
                document.getElementById('escort').checked = true;
                recommendationMessage = 'For stable moderate patients (Severity 2), Medical escort with basic monitoring is usually sufficient.';
                showRecommendationAlert('For stable conditions requiring monitoring, Medical escort is usually sufficient.', 'success');
                break;
            case 1:
                document.getElementById('escort').checked = true;
                recommendationMessage = 'For minor conditions (Severity 1), Medical escort only is typically sufficient for safe transport.';
                showRecommendationAlert('For minor conditions, Medical escort only is typically sufficient.', 'success');
                break;
        }
        
        // Trigger chatbot recommendation if available
        if (window.currentSeverityLevel !== severity) {
            window.currentSeverityLevel = severity;
            triggerChatbotRecommendation(recommendationMessage);
        }
    });
}

function showRecommendationAlert(message, type) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.recommendation-alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create new alert
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} recommendation-alert mt-2`;
    alert.innerHTML = `<i class="fas fa-lightbulb me-2"></i>${message}`;
    
    // Insert after severity select
    const severitySelect = document.getElementById('severity');
    if (severitySelect) {
        severitySelect.parentNode.appendChild(alert);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 10000);
    }
}

function setupFormValidation() {
    const form = document.getElementById('intake-form');
    if (!form) return;
    
    const travelDateInput = document.getElementById('travel_date');
    if (travelDateInput) {
        // Set minimum date to tomorrow
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        travelDateInput.min = tomorrow.toISOString().split('T')[0];
    }
    
    form.addEventListener('submit', function(e) {
        if (!form.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
        } else if (travelDateInput) {
            // Check if travel date is in the future
            const selectedDate = new Date(travelDateInput.value);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            if (selectedDate <= today) {
                e.preventDefault();
                showRecommendationAlert('Please select a future date for travel.', 'danger');
                travelDateInput.focus();
                return;
            }
        }
        
        form.classList.add('was-validated');
    });
}

// Confirm Form Functions
function setupCostCalculator() {
    const familySeatCheckbox = document.getElementById('family_seat');
    const vipCabinCheckbox = document.getElementById('vip_cabin');
    
    if (!familySeatCheckbox || !vipCabinCheckbox) return;
    
    function updateTotalCost() {
        const basePrice = parseFloat(document.querySelector('.base-cost').textContent.replace(/[$,]/g, ''));
        let total = basePrice;
        
        // Show/hide family seat cost
        const familySeatCost = document.querySelector('.family-seat-cost');
        if (familySeatCheckbox.checked) {
            total += 5000;
            if (familySeatCost) familySeatCost.style.display = 'flex';
        } else {
            if (familySeatCost) familySeatCost.style.display = 'none';
        }
        
        // Show/hide VIP cabin cost
        const vipCabinCost = document.querySelector('.vip-cabin-cost');
        if (vipCabinCheckbox.checked) {
            total += 10000;
            if (vipCabinCost) vipCabinCost.style.display = 'flex';
        } else {
            if (vipCabinCost) vipCabinCost.style.display = 'none';
        }
        
        // Update total
        const totalAmount = document.querySelector('.total-amount');
        if (totalAmount) {
            totalAmount.textContent = '$' + total.toLocaleString();
        }
    }
    
    familySeatCheckbox.addEventListener('change', updateTotalCost);
    vipCabinCheckbox.addEventListener('change', updateTotalCost);
}

function setupAddonInteractions() {
    const addonCards = document.querySelectorAll('.addon-card');
    addonCards.forEach(card => {
        const checkbox = card.querySelector('input[type="checkbox"]');
        
        if (checkbox) {
            card.addEventListener('click', function(e) {
                if (e.target.type !== 'checkbox') {
                    checkbox.checked = !checkbox.checked;
                    checkbox.dispatchEvent(new Event('change'));
                }
            });
            
            checkbox.addEventListener('change', function() {
                if (this.checked) {
                    card.classList.add('selected');
                } else {
                    card.classList.remove('selected');
                }
            });
        }
    });
}

// Chatbot Functions
function initializeChatbotWidget() {
    console.log('Initializing chatbot widget');
    
    // Try to initialize BotUI if available
    if (typeof BotUI !== 'undefined') {
        initializeBotUI();
    } else {
        // Fallback to simple chatbot
        initializeSimpleChatbot();
    }
}

function initializeBotUI() {
    if (!document.getElementById('botui-app')) return;
    
    try {
        botui = new BotUI('botui-app');
        
        // Enhanced family-focused greeting
        botui.message.add({
            content: 'Hi there! I\'m here to help you understand medical transport options for your loved one. What would you like to know?'
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
                        text: 'Family Options',
                        value: 'family'
                    }
                ]
            });
        }).then((res) => {
            handleChatbotResponse(res.value);
        });
        
    } catch (error) {
        console.error('Failed to initialize BotUI:', error);
        initializeSimpleChatbot();
    }
}

function handleChatbotResponse(choice) {
    if (!botui) return;
    
    let response = '';
    
    switch(choice) {
        case 'equipment':
            response = 'Our medical equipment includes: Ventilators (for breathing support), ECMO machines (heart/lung support), Incubators (newborn care), Oxygen support (basic breathing aid), and Medical escorts (professional supervision). I recommend equipment based on your loved one\'s severity level.';
            break;
        case 'severity':
            response = 'Severity Guide for your loved one: Level 1 (Minor - stable injuries like sprains), Level 2 (Stable but needs monitoring), Level 3 (Serious - immediate medical attention), Level 4 (Critical - ICU care required), Level 5 (Life-threatening - ventilator/life support needed). Select a level and I\'ll recommend appropriate equipment.';
            break;
        case 'providers':
            response = 'Affiliate comparison for your family: AirMed Response (Premium care - $128,500, ICU certified, 3h ETA), REVA CriticalCare (Doctor onboard - $112,000, physician accompanies, 5h ETA), MercyWings Global (Family-friendly - $102,000, compassionate care, 6h ETA). Choose based on your loved one\'s needs and urgency.';
            break;
        case 'family':
            response = 'Family accommodations available: Family Seat (+$5,000 - allows one family member to accompany your loved one), VIP Cabin (+$10,000 - enhanced comfort and privacy). We also provide regular updates throughout the journey to keep you informed about your loved one\'s condition.';
            break;
        default:
            response = 'I\'m here to help with equipment selection, severity assessment, provider comparison, or family accommodations. What specific information do you need about caring for your loved one?';
    }
    
    botui.message.add({
        content: response,
        delay: 1000
    }).then(() => {
        return botui.action.button({
            action: [
                {
                    text: 'Ask Another Question',
                    value: 'restart'
                },
                {
                    text: 'I\'m Ready to Book',
                    value: 'book'
                }
            ]
        });
    }).then((res) => {
        if (res.value === 'restart') {
            // Restart the conversation
            botui.message.removeAll().then(() => {
                initializeBotUI();
            });
        } else if (res.value === 'book') {
            botui.message.add({
                content: 'Great! Click the "Find a Medical Flight" button to start the booking process. I\'ll be here to help throughout your journey.'
            });
        }
    });
}

function initializeSimpleChatbot() {
    // Fallback chatbot implementation
    const currentPage = getCurrentPage();
    let messages = [];
    
    switch(currentPage) {
        case 'intake':
            messages = [
                {trigger: 'equipment_help', message: 'Need help selecting equipment for your loved one?', type: 'text'},
                {trigger: 'equipment_suggestions', message: 'For Severity 5 patients, I recommend selecting Ventilator and Oxygen support. For Severity 1-2, Medical escort only may be sufficient.', type: 'text'},
                {trigger: 'severity_help', message: 'What do the severity levels mean?', type: 'text'},
                {trigger: 'severity_explanation', message: 'Severity 1: Minor injuries like fractures. Severity 3: Serious conditions needing medical attention. Severity 5: Critical patients on life support.', type: 'text'}
            ];
            break;
        case 'results':
            messages = [
                {trigger: 'provider_help', message: 'Need help choosing a provider for your loved one?', type: 'text'},
                {trigger: 'provider_recommendation', message: 'For critical patients (Severity 4-5), I recommend AirMed Response with ICU certification. For stable patients, MercyWings offers compassionate family-friendly care.', type: 'text'},
                {trigger: 'cost_help', message: 'Why are there price differences?', type: 'text'},
                {trigger: 'cost_explanation', message: 'Prices vary based on medical team certification, equipment available, and response time. Higher-certified teams cost more but provide advanced care for your loved one.', type: 'text'}
            ];
            break;
        default:
            messages = [
                {trigger: 'welcome', message: 'Welcome to MediFly! I can help you understand medical transport options for your loved one.', type: 'text'},
                {trigger: 'family_support', message: 'How can I help your family today?', type: 'text'},
                {trigger: 'general_help', message: 'I can assist with severity levels, equipment options, provider comparisons, and family accommodations.', type: 'text'}
            ];
    }
    
    console.log('Initializing simple chatbot with messages:', messages);
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

// Utility function for PDF download (mock)
function downloadPDF() {
    console.log('Initiating PDF download...');
    // This would be replaced with actual PDF generation in production
}