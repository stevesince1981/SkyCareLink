/* Site Audit & UX Tightening - UI Functionality */
/* Accordion state persistence, dead click detection, and link validation */

(function() {
    'use strict';

    // Accordion functionality with session persistence
    function initAccordions() {
        const accordions = document.querySelectorAll('.accordion');
        
        accordions.forEach(accordion => {
            const header = accordion.querySelector('.header');
            const content = accordion.querySelector('.content');
            const accordionId = accordion.getAttribute('data-accordion-id');
            
            if (!header || !content || !accordionId) return;
            
            // Add toggle icon if not present
            if (!header.querySelector('.toggle-icon')) {
                const icon = document.createElement('span');
                icon.className = 'toggle-icon';
                icon.innerHTML = '▼';
                header.appendChild(icon);
            }
            
            // Restore state from sessionStorage
            const savedState = sessionStorage.getItem(`accordion_${accordionId}`);
            if (savedState === 'open') {
                accordion.classList.add('open');
            }
            
            // Add click listener
            header.addEventListener('click', function() {
                const isOpen = accordion.classList.contains('open');
                
                if (isOpen) {
                    accordion.classList.remove('open');
                    sessionStorage.setItem(`accordion_${accordionId}`, 'closed');
                } else {
                    accordion.classList.add('open');
                    sessionStorage.setItem(`accordion_${accordionId}`, 'open');
                }
            });
        });
    }
    
    // Dead click detection
    function detectDeadClicks() {
        const buttons = document.querySelectorAll('button, a');
        const deadClicks = [];
        
        buttons.forEach(el => {
            const computedStyle = window.getComputedStyle(el);
            
            // Check for disabled state
            if (el.disabled || computedStyle.pointerEvents === 'none') {
                deadClicks.push({
                    element: el,
                    reason: 'Disabled or pointer-events: none',
                    text: el.textContent.trim()
                });
                return;
            }
            
            // Check buttons without proper handlers
            if (el.tagName === 'BUTTON') {
                const hasForm = el.form !== null;
                const hasType = el.getAttribute('type');
                const hasClickHandler = el.onclick !== null || el.hasAttribute('data-bs-toggle') || el.hasAttribute('onclick');
                
                if (!hasForm && !hasClickHandler && hasType !== 'button') {
                    deadClicks.push({
                        element: el,
                        reason: 'Button without form or click handler',
                        text: el.textContent.trim()
                    });
                }
            }
            
            // Check links without proper hrefs
            if (el.tagName === 'A') {
                const href = el.getAttribute('href');
                if (!href || href === '#' || href === 'javascript:void(0)') {
                    const hasClickHandler = el.onclick !== null || el.hasAttribute('data-bs-toggle') || el.hasAttribute('onclick');
                    if (!hasClickHandler) {
                        deadClicks.push({
                            element: el,
                            reason: 'Link without proper href or click handler',
                            text: el.textContent.trim()
                        });
                    }
                }
            }
        });
        
        // Log dead clicks to console
        if (deadClicks.length > 0) {
            console.group('⚠️ Dead Clicks Detected');
            deadClicks.forEach(item => {
                console.warn('Dead click:', item.element, `- ${item.reason}`, `Text: "${item.text}"`);
            });
            console.groupEnd();
        } else {
            console.log('✓ No dead clicks detected');
        }
        
        return deadClicks;
    }
    
    // Link validation (client-side 404 detector)
    function validateLinks() {
        const links = document.querySelectorAll('a[href]');
        const brokenLinks = [];
        
        links.forEach(link => {
            const href = link.getAttribute('href');
            
            // Only check same-origin URLs
            if (href.startsWith('/') || href.includes(window.location.hostname)) {
                fetch(href, { method: 'HEAD' })
                    .then(response => {
                        if (!response.ok) {
                            brokenLinks.push({ link, href, status: response.status });
                            console.warn('⚠️ Broken link:', href, `(${response.status})`);
                        }
                    })
                    .catch(error => {
                        brokenLinks.push({ link, href, error: error.message });
                        console.warn('⚠️ Broken link:', href, `(${error.message})`);
                    });
            }
        });
        
        // Log summary after a delay to allow async checks
        setTimeout(() => {
            if (brokenLinks.length === 0) {
                console.log('✓ No broken links detected');
            } else {
                console.warn(`⚠️ Found ${brokenLinks.length} broken links`);
            }
        }, 2000);
    }
    
    // Enhanced button state management
    function enhanceButtonStates() {
        const buttons = document.querySelectorAll('button, .btn');
        
        buttons.forEach(button => {
            // Ensure disabled buttons have proper visual state
            if (button.disabled) {
                button.style.opacity = '0.5';
                button.style.cursor = 'not-allowed';
            }
            
            // Add hover effects for enabled buttons
            if (!button.disabled) {
                button.addEventListener('mouseenter', function() {
                    this.style.transform = 'translateY(-1px)';
                });
                
                button.addEventListener('mouseleave', function() {
                    this.style.transform = 'translateY(0)';
                });
            }
        });
    }
    
    // Form validation helper
    function addFormValidationFeedback() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                const requiredFields = form.querySelectorAll('[required]');
                let isValid = true;
                
                requiredFields.forEach(field => {
                    if (!field.value.trim()) {
                        isValid = false;
                        field.classList.add('is-invalid');
                        
                        // Add error message if not present
                        if (!field.nextElementSibling || !field.nextElementSibling.classList.contains('invalid-feedback')) {
                            const errorDiv = document.createElement('div');
                            errorDiv.className = 'invalid-feedback';
                            errorDiv.textContent = 'This field is required.';
                            field.parentNode.insertBefore(errorDiv, field.nextSibling);
                        }
                    } else {
                        field.classList.remove('is-invalid');
                        const errorDiv = field.nextElementSibling;
                        if (errorDiv && errorDiv.classList.contains('invalid-feedback')) {
                            errorDiv.remove();
                        }
                    }
                });
                
                if (!isValid) {
                    e.preventDefault();
                    console.warn('⚠️ Form validation failed');
                }
            });
        });
    }
    
    // Compact CSS loader
    function loadCompactCSS() {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = '/static/css/compact.css';
        document.head.appendChild(link);
    }
    
    // Console utilities for manual QA
    window.sitAuditUtils = {
        detectDeadClicks: detectDeadClicks,
        validateLinks: validateLinks,
        checkAccordions: function() {
            const accordions = document.querySelectorAll('.accordion');
            console.log(`Found ${accordions.length} accordions:`);
            accordions.forEach(acc => {
                const id = acc.getAttribute('data-accordion-id');
                const state = acc.classList.contains('open') ? 'open' : 'closed';
                const saved = sessionStorage.getItem(`accordion_${id}`);
                console.log(`  ${id}: ${state} (saved: ${saved})`);
            });
        },
        runFullAudit: function() {
            console.log('🔍 Running full site audit...');
            loadCompactCSS();
            detectDeadClicks();
            validateLinks();
            this.checkAccordions();
            console.log('✅ Site audit complete');
        }
    };
    
    // Initialize everything on DOM ready
    document.addEventListener('DOMContentLoaded', function() {
        console.log('🚀 UI.js initializing...');
        
        // Load compact CSS
        loadCompactCSS();
        
        // Initialize all functionality
        initAccordions();
        enhanceButtonStates();
        addFormValidationFeedback();
        
        // Run audits in development mode
        if (window.location.hostname === 'localhost' || window.location.hostname.includes('replit')) {
            setTimeout(() => {
                detectDeadClicks();
                validateLinks();
            }, 1000);
        }
        
        console.log('✅ UI.js initialized');
        console.log('💡 Use sitAuditUtils.runFullAudit() for manual testing');
    });
    
})();