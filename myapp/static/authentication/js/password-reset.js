// Password Reset Enhanced JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Form submission handling
    const resetForm = document.getElementById('passwordResetForm');
    if (resetForm) {
        resetForm.addEventListener('submit', function(e) {
            const submitBtn = document.querySelector('#resetBtn');
            if (submitBtn) {
                submitBtn.classList.add('loading');
            }
        });
    }

    // Email validation
    const emailInput = document.getElementById('id_email');
    if (emailInput) {
        emailInput.addEventListener('blur', function() {
            validateEmail(this.value);
        });
    }

    // Real-time email validation
    function validateEmail(email) {
        const feedback = document.getElementById('email-feedback');
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        
        if (!email) {
            feedback.textContent = '';
            feedback.className = 'input-feedback';
            return;
        }
        
        if (!emailRegex.test(email)) {
            feedback.textContent = 'Please enter a valid email address';
            feedback.className = 'input-feedback invalid';
        } else {
            feedback.textContent = 'Email format looks good';
            feedback.className = 'input-feedback valid';
        }
    }

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.style.opacity !== '0') {
                alert.style.opacity = '0';
                setTimeout(() => {
                    alert.style.display = 'none';
                }, 600);
            }
        }, 5000);
    });

    // Close alert functionality
    const closeBtns = document.querySelectorAll('.closebtn');
    closeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const alert = this.parentElement;
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 600);
        });
    });

    // Smooth scrolling for any anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
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

    // Focus management for better accessibility
    const focusableElements = document.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    // Trap focus within the form for better accessibility
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];

    if (firstFocusable && lastFocusable) {
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Tab') {
                if (e.shiftKey) {
                    if (document.activeElement === firstFocusable) {
                        e.preventDefault();
                        lastFocusable.focus();
                    }
                } else {
                    if (document.activeElement === lastFocusable) {
                        e.preventDefault();
                        firstFocusable.focus();
                    }
                }
            }
        });
    }

    // Add loading state to form submission
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.classList.add('loading');
            }
        });
    });

    // Prevent double submission
    let isSubmitting = false;
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (isSubmitting) {
                e.preventDefault();
                return;
            }
            isSubmitting = true;
            
            // Reset after 5 seconds in case of error
            setTimeout(() => {
                isSubmitting = false;
            }, 5000);
        });
    });
});

// Utility functions
function showMessage(message, type = 'info') {
    const container = document.querySelector('.container');
    if (!container) return;

    const alert = document.createElement('div');
    alert.className = `alert ${type}`;
    alert.innerHTML = `
        <strong>${type.charAt(0).toUpperCase() + type.slice(1)}:</strong> ${message}
        <span class="closebtn">&times;</span>
    `;

    container.insertBefore(alert, container.firstChild);

    // Auto-hide after 5 seconds
    setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => {
            alert.remove();
        }, 600);
    }, 5000);

    // Close button functionality
    const closeBtn = alert.querySelector('.closebtn');
    closeBtn.addEventListener('click', () => {
        alert.style.opacity = '0';
        setTimeout(() => {
            alert.remove();
        }, 600);
    });
}

// Debounce function for performance
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Enhanced email validation with debouncing
const debouncedEmailValidation = debounce(validateEmail, 300);

// Export functions for use in templates
window.passwordResetUtils = {
    showMessage,
    validateEmail: debouncedEmailValidation
}; 