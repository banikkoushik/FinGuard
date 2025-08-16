// Password toggle visibility
const passwordToggles = document.querySelectorAll('.password-toggle-container');

passwordToggles.forEach(toggle => {
    toggle.addEventListener('click', () => {
        const icon = toggle.querySelector('i');
        const input = toggle.parentElement.querySelector('input');
        
        if (input.type === 'password') {
            input.type = 'text';
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        } else {
            input.type = 'password';
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
        }
    });
});

// Password strength indicator
const passwordInput = document.getElementById('signup-password');
const confirmInput = document.getElementById('signup-confirm');
const strengthFill = document.getElementById('password-strength-fill');
const strengthText = document.getElementById('password-strength-text');
const passwordMatch = document.getElementById('password-match');

if (passwordInput) {
    function checkPasswordStrength(password) {
        let strength = 0;
        
        // Check password length
        if (password.length > 7) strength += 25;
        
        // Check for mixed case
        if (password.match(/[a-z]/) && password.match(/[A-Z]/)) strength += 25;
        
        // Check for numbers
        if (password.match(/\d/)) strength += 25;
        
        // Check for special characters
        if (password.match(/[^a-zA-Z0-9]/)) strength += 25;
        
        // Update UI
        if (strengthFill) {
            strengthFill.style.width = `${strength}%`;
            
            if (strength < 50) {
                strengthFill.style.background = '#e74c3c';
                strengthText.textContent = 'Weak';
            } else if (strength < 75) {
                strengthFill.style.background = '#f39c12';
                strengthText.textContent = 'Medium';
            } else {
                strengthFill.style.background = '#2ecc71';
                strengthText.textContent = 'Strong';
            }
        }
    }
    
    function checkPasswordMatch() {
        if (passwordInput.value && confirmInput.value) {
            if (passwordInput.value !== confirmInput.value) {
                if (passwordMatch) passwordMatch.style.display = 'block';
                return false;
            } else {
                if (passwordMatch) passwordMatch.style.display = 'none';
                return true;
            }
        }
        return true;
    }
    
    passwordInput.addEventListener('input', () => {
        checkPasswordStrength(passwordInput.value);
        if (confirmInput) checkPasswordMatch();
    });
    
    if (confirmInput) {
        confirmInput.addEventListener('input', () => {
            checkPasswordMatch();
        });
    }
}

// Notification system
function showNotification(message, type) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} show`;
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Form submission
const loginForm = document.getElementById('login-form');
const signupForm = document.getElementById('signup-form');

if (loginForm) {
    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        
        // Simulate login process
        setTimeout(() => {
            if (email.includes('@') && password.length > 5) {
                showNotification('Login successful! Redirecting to dashboard...', 'success');
            } else {
                showNotification('Invalid email or password. Please try again.', 'error');
            }
        }, 1000);
    });
}

if (signupForm) {
    signupForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const name = document.getElementById('signup-name').value;
        const email = document.getElementById('signup-email').value;
        const password = document.getElementById('signup-password').value;
        const confirmPassword = document.getElementById('signup-confirm').value;
        
        // Validate password match
        if (passwordInput && confirmInput) {
            if (!checkPasswordMatch()) {
                showNotification('Passwords do not match', 'error');
                return;
            }
        }
        
        if (password.length < 8) {
            showNotification('Password must be at least 8 characters', 'error');
            return;
        }
        
        // Simulate signup process
        setTimeout(() => {
            showNotification('Account created successfully! Welcome to FinGuard', 'success');
        }, 1000);
    });
}

// Forgot password functionality
const forgotPassword = document.querySelector('.forgot-password');
if (forgotPassword) {
    forgotPassword.addEventListener('click', (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email')?.value;
        
        if (email) {
            showNotification(`Password reset instructions sent to ${email}`, 'success');
        } else {
            showNotification('Please enter your email address first', 'error');
        }
    });
}