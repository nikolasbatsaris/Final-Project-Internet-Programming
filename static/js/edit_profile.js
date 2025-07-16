// this javascript code manages persistent dark mode across pages and syncs with system preference
// it also provides ajax validation for username email and password fields
// it handles real time change detection in profile forms and toggles password section visibility

// Persistent dark mode toggle for all pages, fallback to system preference on logout
function setDarkMode(on) { // apply dark mode styles to body and containers
    if(on) {
        document.body.classList.add('dark-mode'); // enable dark mode class
        document.body.style.background = '#222'; // set dark background
        document.querySelectorAll('.container').forEach(function(el){ // loop through all container elements
            el.style.background = ''; // reset background
            el.style.color = ''; // reset text color
        });
    } else {
        document.body.classList.remove('dark-mode'); // remove dark mode class
        document.body.style.background = '#f5f5f5'; // set light background
        document.querySelectorAll('.container').forEach(function(el){ // loop through all container elements
            el.style.background = ''; // reset background
            el.style.color = ''; // reset text color
        });
    }
}
function getDarkMode() { // get saved dark mode preference or system setting
    const pref = localStorage.getItem('darkMode'); // check local storage
    if (pref === null) {
        // No preference, use system
        return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches; // check system setting
    }
    return pref === 'on'; // return true if saved as on
}
document.querySelector('.btn[title="Toggle dark mode"]')?.addEventListener('click', function() { // toggle dark mode on button click
    const on = !getDarkMode(); // flip current mode
    localStorage.setItem('darkMode', on ? 'on' : 'off'); // save preference
    setDarkMode(on); // apply mode
});
// On page load
setDarkMode(getDarkMode()); // apply dark mode when page loads
// On logout, clear darkMode preference
if (document.querySelectorAll('.logout').length) { // check if logout buttons exist
    document.querySelectorAll('.logout').forEach(function(logoutLink) { // loop through logout buttons
        logoutLink.addEventListener('click', function() {
            localStorage.removeItem('darkMode'); // clear preference on logout
        });
    });
}

document.addEventListener('DOMContentLoaded', function() { // wait for dom to load
    // Username/email AJAX check
    function showFieldMessage(input, msg, isError) { // display validation message below input
        let msgEl = input.parentElement.querySelector('.field-msg'); // find existing message
        if (!msgEl) {
            msgEl = document.createElement('div'); // create if not exist
            msgEl.className = 'field-msg'; // set class
            input.parentElement.appendChild(msgEl); // append to input parent
        }
        msgEl.textContent = msg; // set text
        msgEl.style.color = isError ? '#e74c3c' : '#27ae60'; // set color based on error
        msgEl.style.fontSize = '0.98em'; // set font size
        msgEl.style.marginTop = '2px'; // set margin
    }
    // Username
    const usernameInput = document.querySelector('input[name="username"]'); // get username input
    if (usernameInput) {
        usernameInput.addEventListener('blur', function() { // on losing focus
            const val = usernameInput.value.trim(); // get input value
            if (!val) return; // skip if empty
            fetch(`/ajax/check-username/?username=${encodeURIComponent(val)}`) // send request
                .then(r => r.json()) // parse json
                .then(data => {
                    showFieldMessage(usernameInput, data.message, data.exists); // show result
                });
        });
    }
    // Email
    const emailInput = document.querySelector('input[name="email"]'); // get email input
    if (emailInput) {
        emailInput.addEventListener('blur', function() {
            const val = emailInput.value.trim(); // get value
            if (!val) return; // skip if empty
            fetch(`/ajax/check-email/?email=${encodeURIComponent(val)}`) // send request
                .then(r => r.json())
                .then(data => {
                    showFieldMessage(emailInput, data.message, data.exists); // show result
                });
        });
    }
    // Password validation (current and new)
    const oldPassInput = document.querySelector('input[name="old_password"]'); // current password input
    const newPass1Input = document.querySelector('input[name="new_password1"]'); // new password input
    const newPass2Input = document.querySelector('input[name="new_password2"]'); // confirm new password input
    if (oldPassInput) {
        oldPassInput.addEventListener('blur', function() { // on blur validate old password
            const val = oldPassInput.value;
            if (!val) return;
            fetch('/ajax/check-password/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `password=${encodeURIComponent(val)}`
            })
            .then(r => r.json())
            .then(data => {
                showFieldMessage(oldPassInput, data.message, !data.valid); // show result
            });
        });
    }
    function checkNewPasswords() { // validate new passwords
        if (newPass1Input && newPass2Input) {
            const v1 = newPass1Input.value;
            const v2 = newPass2Input.value;
            let msg = '';
            let isError = false;
            if (v1 && v2) {
                if (v1 !== v2) {
                    msg = 'New passwords do not match.';
                    isError = true;
                } else if (v1.length < 8) {
                    msg = 'Password must be at least 8 characters.';
                    isError = true;
                } else {
                    msg = 'Passwords match.';
                    isError = false;
                }
            }
            showFieldMessage(newPass2Input, msg, isError); // show match or error
        }
    }
    if (newPass1Input && newPass2Input) {
        newPass1Input.addEventListener('input', checkNewPasswords); // validate while typing
        newPass2Input.addEventListener('input', checkNewPasswords);
    }
   
    const form = document.querySelector('.edit-profile-form-container form'); // profile form
    const saveBtn = form ? form.querySelector('button[name="save_profile"]') : null; // save button
    if (form && saveBtn) {
        // Store initial values
        const initial = {}; // track initial field values
        form.querySelectorAll('input').forEach(input => {
            initial[input.name] = input.value; // store initial input value
        });
        function checkChanged() { // check if anything changed
            let changed = false;
            form.querySelectorAll('input').forEach(input => {
                // Allow username to be blank, only check if any field changed
                if (input.value !== initial[input.name]) {
                    changed = true;
                }
            });
            saveBtn.disabled = !changed; // enable save button if something changed
        }
        form.querySelectorAll('input').forEach(input => {
            input.addEventListener('input', checkChanged); // listen for input change
        });
        form.addEventListener('submit', function(e) {
            let changed = false;
            form.querySelectorAll('input').forEach(input => {
                if (input.value !== initial[input.name]) {
                    changed = true;
                }
            });
            if (!changed) {
                e.preventDefault(); // stop submission if nothing changed
                saveBtn.disabled = true;
            }
        });
    }
    const toggleBtn = document.querySelector('.toggle-password-section'); // toggle password section button
    const passwordSection = document.querySelector('#passwordSection'); // password section container
    if (toggleBtn && passwordSection) {
        toggleBtn.addEventListener('click', function() {
            if (passwordSection.style.display === 'none' || passwordSection.style.display === '') {
                passwordSection.style.display = 'block'; // show password section
                toggleBtn.textContent = 'Hide Password Section';
            } else {
                passwordSection.style.display = 'none'; // hide password section
                toggleBtn.textContent = 'Change Password';
            }
        });
    }
}); 

// --- THEME SYNC WITH DASHBOARD ---
(function syncThemeWithDashboard() { // iife for syncing theme with dashboard
    function setDarkMode(on) {
        if(on) {
            document.documentElement.classList.add('dark-mode'); // enable root class
        } else {
            document.documentElement.classList.remove('dark-mode'); // disable root class
        }
    }
    function getDarkMode() {
        const pref = localStorage.getItem('darkMode'); // get saved mode
        if (pref === null) {
            return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches; // use system setting
        }
        return pref === 'on'; // return saved preference
    }
    setDarkMode(getDarkMode()); // apply theme on load
})();
