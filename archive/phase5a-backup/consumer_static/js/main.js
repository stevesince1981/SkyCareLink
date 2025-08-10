// MediFly Consumer MVP - Enhanced JavaScript Features
// AI Command Processing, Address Validation, Dynamic Pricing

document.addEventListener('DOMContentLoaded', function() {
    console.log('MediFly Consumer MVP Enhanced Features Loaded');
    initializeAICommands();
    initializeAddressValidation();
    initializeDynamicPricing();
    initializePriorityAnimations();
});

// AI Command Processing System
function initializeAICommands() {
    const aiInput = document.getElementById('aiCommand');
    if (aiInput) {
        aiInput.addEventListener('keypress', handleAICommand);
        console.log('AI command system initialized');
    }
}

function handleAICommand(event) {
    if (event.key === 'Enter') {
        const command = event.target.value.toLowerCase();
        console.log('AI Command received:', command);
        
        // Parse natural language commands
        if (command.includes('grandma') && command.includes('orlando') && command.includes('nyc')) {
            processGrandmaOrlandoCommand();
        } else if (command.includes('emergency') || command.includes('critical')) {
            processCriticalCommand();
        } else if (command.includes('mvp') || command.includes('membership')) {
            processMVPCommand();
        } else if (command.includes('vip') || command.includes('luxury')) {
            processVIPCommand();
        } else {
            showAIResponse('I can help you plan your medical transport. Try asking about emergency transport, MVP membership, or specific routes like "Orlando to NYC".');
        }
    }
}

function processGrandmaOrlandoCommand() {
    showAIResponse('Perfect! I\'ll help you plan a transport from Orlando to NYC. This would be a non-critical transport with family seat options. Shall I start the booking process?');
    
    // Auto-fill form if on intake page
    setTimeout(() => {
        if (document.getElementById('origin')) {
            document.getElementById('origin').value = 'Orlando, FL';
            document.getElementById('destination').value = 'New York, NY';
            document.getElementById('patient_name').value = 'Grandma';
            document.getElementById('severity').value = '2';
            triggerFormUpdate();
        } else {
            // Redirect to intake with parameters
            window.location.href = '/intake?type=non-critical&origin=Orlando%2C%20FL&destination=New%20York%2C%20NY&ai_suggestion=grandma_orlando';
        }
    }, 1500);
}

function processCriticalCommand() {
    showAIResponse('For emergency/critical transport, I recommend same-day options with weather monitoring. This includes a 20% urgency fee. Would you like to see critical transport affiliates?');
    setTimeout(() => {
        if (window.location.pathname === '/') {
            window.location.href = '/intake?type=critical';
        }
    }, 2000);
}

function processMVPCommand() {
    showAIResponse('MVP membership offers 10% discounts, priority booking, and exclusive beta features for $49/month. Would you like to learn more about MVP benefits?');
    setTimeout(() => {
        window.location.href = '/mvp_incentive';
    }, 2000);
}

function processVIPCommand() {
    showAIResponse('VIP cabin upgrade ($10K) includes luxury amenities, IV treatments, champagne service, and dedicated cabin attendant. Available on select aircraft.');
}

function showAIResponse(message) {
    // Create or update AI response area
    let responseArea = document.getElementById('aiResponse');
    if (!responseArea) {
        responseArea = document.createElement('div');
        responseArea.id = 'aiResponse';
        responseArea.className = 'alert alert-info mt-3';
        responseArea.innerHTML = `
            <div class="d-flex align-items-start">
                <i class="fas fa-robot me-2 mt-1"></i>
                <div class="ai-response-text"></div>
            </div>
        `;
        document.getElementById('aiCommand').parentNode.appendChild(responseArea);
    }
    
    const textArea = responseArea.querySelector('.ai-response-text');
    textArea.innerHTML = message;
    responseArea.style.display = 'block';
    
    // Scroll to response
    responseArea.scrollIntoView({ behavior: 'smooth' });
}

// Address Validation with Google Places API Stub
function initializeAddressValidation() {
    const originInput = document.getElementById('origin');
    const destinationInput = document.getElementById('destination');
    
    if (originInput) {
        originInput.addEventListener('input', function() {
            validateAddress(this, 'origin');
        });
    }
    
    if (destinationInput) {
        destinationInput.addEventListener('input', function() {
            validateAddress(this, 'destination');
        });
    }
}

function validateAddress(input, type) {
    const address = input.value;
    if (address.length > 3) {
        // Simulate Google Places API validation
        console.log('Validating address:', address, 'for', type);
        
        // Mock address suggestions
        const suggestions = getAddressSuggestions(address);
        showAddressSuggestions(input, suggestions);
    }
}

function getAddressSuggestions(address) {
    const mockSuggestions = {
        'orlando': [
            'Orlando Regional Medical Center, Orlando, FL',
            'Orlando International Airport, Orlando, FL', 
            'AdventHealth Orlando, Orlando, FL'
        ],
        'ny': [
            'NewYork-Presbyterian Hospital, New York, NY',
            'Mount Sinai Hospital, New York, NY',
            'JFK International Airport, New York, NY'
        ],
        'miami': [
            'Jackson Memorial Hospital, Miami, FL',
            'Miami International Airport, Miami, FL',
            'Baptist Hospital of Miami, Miami, FL'
        ]
    };
    
    const lowerAddress = address.toLowerCase();
    for (let key in mockSuggestions) {
        if (lowerAddress.includes(key)) {
            return mockSuggestions[key];
        }
    }
    return [];
}

function showAddressSuggestions(input, suggestions) {
    // Remove existing suggestions
    const existingSuggestions = document.querySelector('.address-suggestions');
    if (existingSuggestions) {
        existingSuggestions.remove();
    }
    
    if (suggestions.length > 0) {
        const suggestionDiv = document.createElement('div');
        suggestionDiv.className = 'address-suggestions';
        suggestionDiv.style.cssText = `
            position: absolute;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            z-index: 1000;
            width: 100%;
            max-height: 200px;
            overflow-y: auto;
        `;
        
        suggestions.forEach(suggestion => {
            const suggestionItem = document.createElement('div');
            suggestionItem.className = 'suggestion-item';
            suggestionItem.style.cssText = `
                padding: 10px;
                cursor: pointer;
                border-bottom: 1px solid #eee;
            `;
            suggestionItem.textContent = suggestion;
            
            suggestionItem.addEventListener('click', function() {
                input.value = suggestion;
                suggestionDiv.remove();
                console.log('Address selected:', suggestion);
            });
            
            suggestionItem.addEventListener('mouseenter', function() {
                this.style.backgroundColor = '#f0f0f0';
            });
            
            suggestionItem.addEventListener('mouseleave', function() {
                this.style.backgroundColor = 'white';
            });
            
            suggestionDiv.appendChild(suggestionItem);
        });
        
        // Position suggestions
        const rect = input.getBoundingClientRect();
        suggestionDiv.style.top = (rect.bottom + window.scrollY) + 'px';
        suggestionDiv.style.left = rect.left + 'px';
        suggestionDiv.style.width = rect.width + 'px';
        
        input.parentNode.style.position = 'relative';
        input.parentNode.appendChild(suggestionDiv);
    }
}

// Dynamic Equipment Pricing System
function initializeDynamicPricing() {
    const equipmentCheckboxes = document.querySelectorAll('input[name="equipment"]');
    const sameDayCheckbox = document.getElementById('same_day');
    
    equipmentCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateEquipmentPricing);
    });
    
    if (sameDayCheckbox) {
        sameDayCheckbox.addEventListener('change', updateSameDayPricing);
    }
}

function updateEquipmentPricing() {
    const equipmentPricing = {
        'ventilator': 5000,
        'ecmo': 10000, 
        'incubator': 3000,
        'escort': 2000,
        'oxygen': 1000
    };
    
    let totalEquipmentCost = 0;
    const selectedEquipment = [];
    
    document.querySelectorAll('input[name="equipment"]:checked').forEach(checkbox => {
        const equipmentType = checkbox.value;
        const cost = equipmentPricing[equipmentType] || 0;
        totalEquipmentCost += cost;
        selectedEquipment.push(`${equipmentType.charAt(0).toUpperCase() + equipmentType.slice(1)} (+$${cost.toLocaleString()})`);
    });
    
    // Update equipment cost display
    updateEquipmentCostDisplay(totalEquipmentCost, selectedEquipment);
    
    console.log('Equipment total cost:', totalEquipmentCost);
    console.log('Selected equipment:', selectedEquipment);
}

function updateEquipmentCostDisplay(totalCost, selectedEquipment) {
    let costDisplay = document.getElementById('equipmentCostDisplay');
    if (!costDisplay) {
        costDisplay = document.createElement('div');
        costDisplay.id = 'equipmentCostDisplay';
        costDisplay.className = 'equipment-pricing mt-3';
        
        const equipmentSection = document.querySelector('.equipment-section') || document.querySelector('form');
        if (equipmentSection) {
            equipmentSection.appendChild(costDisplay);
        }
    }
    
    if (totalCost > 0) {
        costDisplay.innerHTML = `
            <h6><i class="fas fa-calculator me-2"></i>Equipment Cost Summary</h6>
            <div class="selected-equipment">
                ${selectedEquipment.map(item => `<span class="badge bg-success me-1">${item}</span>`).join('')}
            </div>
            <div class="total-cost mt-2">
                <strong>Total Equipment Cost: $${totalCost.toLocaleString()}</strong>
            </div>
            <small class="text-muted d-block mt-1">
                <i class="fas fa-info-circle me-1"></i>
                Affiliate may recommend additional life-saving equipment during pre-flight assessment.
            </small>
        `;
        costDisplay.style.display = 'block';
    } else {
        costDisplay.style.display = 'none';
    }
}

function updateSameDayPricing() {
    const sameDayCheckbox = document.getElementById('same_day');
    const warningArea = document.getElementById('sameDayWarning');
    
    if (sameDayCheckbox && sameDayCheckbox.checked) {
        if (!warningArea) {
            const warning = document.createElement('div');
            warning.id = 'sameDayWarning';
            warning.className = 'same-day-warning';
            warning.innerHTML = `
                <h6><i class="fas fa-exclamation-triangle me-2"></i>Same-Day Transport Notice</h6>
                <ul class="mb-2">
                    <li><strong>20% urgency fee</strong> will be added to all affiliate quotes</li>
                    <li><strong>Weather dependent</strong> - flights may be delayed or canceled</li>
                    <li><strong>Limited availability</strong> - fewer affiliates for immediate departure</li>
                    <li><strong>Priority scheduling</strong> - takes precedence over planned transports</li>
                </ul>
                <small class="text-muted">
                    Same-day requests are subject to affiliate availability and weather conditions.
                </small>
            `;
            
            sameDayCheckbox.parentNode.appendChild(warning);
        } else {
            warningArea.style.display = 'block';
        }
    } else if (warningArea) {
        warningArea.style.display = 'none';
    }
}

// Priority Partner Animations
function initializePriorityAnimations() {
    const priorityCards = document.querySelectorAll('.priority-card');
    console.log(`Initializing priority animations for ${priorityCards.length} cards`);
    
    priorityCards.forEach(card => {
        // Enhanced pulse animation for priority partners
        card.style.animation = 'pulse 2s infinite, glow 3s ease-in-out infinite alternate';
        
        // Add priority badge if not present
        if (!card.querySelector('.priority-badge')) {
            const badge = document.createElement('div');
            badge.className = 'priority-badge';
            badge.innerHTML = '<i class="fas fa-crown me-1"></i>Priority Partner';
            card.appendChild(badge);
        }
    });
}

// Form update trigger for dynamic changes
function triggerFormUpdate() {
    // Trigger equipment pricing update
    updateEquipmentPricing();
    
    // Trigger same-day pricing if applicable
    const sameDayCheckbox = document.getElementById('same_day');
    if (sameDayCheckbox) {
        updateSameDayPricing();
    }
    
    console.log('Form updates triggered');
}

// Handle affiliate name blurring on results page
function initializeAffiliateBlurring() {
    const providerNames = document.querySelectorAll('.provider-name');
    providerNames.forEach(name => {
        const originalName = name.dataset.actualName;
        if (originalName) {
            name.textContent = name.textContent.replace(originalName, originalName.charAt(0) + '****');
        }
    });
}

// Global functions for template use
window.handleAICommand = handleAICommand;
window.triggerFormUpdate = triggerFormUpdate;
window.updateEquipmentPricing = updateEquipmentPricing;
window.updateSameDayPricing = updateSameDayPricing;