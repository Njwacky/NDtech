document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('registrationForm');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const loader = document.getElementById('loader');

    // Simple helper to show loading state
    const showLoading = () => {
        submitBtn.disabled = true;
        btnText.style.display = 'none';
        loader.style.display = 'block';
    };

    form.addEventListener('submit', () => {
        // Since this is a Django form, we let it submit naturally after validation
        // But we show the loading state for UX
        showLoading();
    });

    // Client-side validation for immediate feedback
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirmPassword');

    const validatePasswords = () => {
        if (password.value !== confirmPassword.value) {
            confirmPassword.setCustomValidity("Passwords don't match");
        } else {
            confirmPassword.setCustomValidity('');
        }
    };

    if (password && confirmPassword) {
        password.onchange = validatePasswords;
        confirmPassword.onkeyup = validatePasswords;
    }
});
