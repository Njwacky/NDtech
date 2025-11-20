document.addEventListener('DOMContentLoaded', function() {
    const currentPasswordInput = document.getElementById('current_password');
    const newPasswordInput = document.getElementById('new_password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const form = document.querySelector('form');

    // Function to show validation message
    function showValidation(input, message, isValid) {
        // Remove existing validation message
        const existingMessage = input.parentNode.querySelector('.validation-message');
        if (existingMessage) {
            existingMessage.remove();
        }

        if (message) {
            const validationDiv = document.createElement('div');
            validationDiv.className = `validation-message ${isValid ? 'valid' : 'invalid'}`;
            validationDiv.textContent = message;
            validationDiv.style.fontSize = '0.875rem';
            validationDiv.style.marginTop = '0.25rem';
            
            if (isValid) {
                validationDiv.style.color = '#28a745';
            } else {
                validationDiv.style.color = '#dc3545';
            }
            
            input.parentNode.appendChild(validationDiv);
        }
    }

    // Function to validate password strength
    function validatePasswordStrength(password) {
        if (password.length === 0) return { valid: true, message: '' };
        
        if (password.length < 6) {
            return { valid: false, message: 'Password must be at least 6 characters' };
        }
        
        if (password.length < 8) {
            return { valid: true, message: 'Weak password - consider using 8+ characters' };
        }
        
        // Check for common patterns
        const hasUpperCase = /[A-Z]/.test(password);
        const hasLowerCase = /[a-z]/.test(password);
        const hasNumbers = /\d/.test(password);
        const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);
        
        const strength = [hasUpperCase, hasLowerCase, hasNumbers, hasSpecialChar].filter(Boolean).length;
        
        if (strength >= 3) {
            return { valid: true, message: 'Strong password' };
        } else if (strength >= 2) {
            return { valid: true, message: 'Medium strength password' };
        } else {
            return { valid: true, message: 'Weak password - add uppercase, numbers, or special characters' };
        }
    }

    // Real-time validation for new password
    newPasswordInput.addEventListener('input', function() {
        const password = this.value;
        const validation = validatePasswordStrength(password);
        showValidation(this, validation.message, validation.valid);
        
        // Also validate confirm password if it has a value
        if (confirmPasswordInput.value) {
            validatePasswordMatch();
        }
    });

    // Real-time validation for confirm password
    confirmPasswordInput.addEventListener('input', validatePasswordMatch);

    function validatePasswordMatch() {
        const newPassword = newPasswordInput.value;
        const confirmPassword = confirmPasswordInput.value;
        
        if (confirmPassword.length === 0) {
            showValidation(confirmPasswordInput, '', true);
            return;
        }
        
        if (newPassword === confirmPassword) {
            showValidation(confirmPasswordInput, 'Passwords match', true);
        } else {
            showValidation(confirmPasswordInput, 'Passwords do not match', false);
        }
    }

    // Form submission validation
    form.addEventListener('submit', function(e) {
        const currentPassword = currentPasswordInput.value;
        const newPassword = newPasswordInput.value;
        const confirmPassword = confirmPasswordInput.value;
        
        // Check if user is trying to change password (new password or confirm password filled)
        const passwordChangeAttempt = newPassword || confirmPassword;
        
        if (passwordChangeAttempt) {
            // Validate current password is provided
            if (!currentPassword) {
                e.preventDefault();
                showValidation(currentPasswordInput, 'Current password is required to change password', false);
                currentPasswordInput.focus();
                return;
            }
            
            // Validate new password
            if (!newPassword) {
                e.preventDefault();
                showValidation(newPasswordInput, 'New password is required', false);
                newPasswordInput.focus();
                return;
            }
            
            if (newPassword.length < 6) {
                e.preventDefault();
                showValidation(newPasswordInput, 'Password must be at least 6 characters', false);
                newPasswordInput.focus();
                return;
            }
            
            // Validate password match
            if (newPassword !== confirmPassword) {
                e.preventDefault();
                showValidation(confirmPasswordInput, 'Passwords do not match', false);
                confirmPasswordInput.focus();
                return;
            }
        }
        
        // If all validations pass, show loading state
        const submitButton = form.querySelector('.btn-submit');
        const originalText = submitButton.innerHTML;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
        submitButton.disabled = true;
        
        // Reset button after 3 seconds (in case form doesn't submit)
        setTimeout(() => {
            submitButton.innerHTML = originalText;
            submitButton.disabled = false;
        }, 3000);
    });

    // Clear validation messages when user starts typing in current password
    currentPasswordInput.addEventListener('input', function() {
        if (this.value.length > 0) {
            showValidation(this, '', true);
        }
    });

    // Add visual feedback for password section focus
    const passwordSection = document.querySelector('.password-section');
    const passwordInputs = passwordSection.querySelectorAll('input[type="password"]');
    
    passwordInputs.forEach(input => {
        input.addEventListener('focus', function() {
            passwordSection.style.borderColor = '#007bff';
            passwordSection.style.backgroundColor = '#f0f8ff';
        });
        
        input.addEventListener('blur', function() {
            passwordSection.style.borderColor = '#dee2e6';
            passwordSection.style.backgroundColor = '#f8f9fa';
        });
    });
});
