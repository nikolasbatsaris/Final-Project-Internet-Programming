// dark mode functionality (modern, consistent with dashboard)

function initializeDarkMode() {
    const pref = localStorage.getItem('darkMode'); // get saved dark mode preference
    const isDark = (pref === 'on') || (pref === null && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches); // decide if dark mode should be enabled

    if (isDark) {
        document.documentElement.classList.add('dark-mode'); // apply dark mode class
    } else {
        document.documentElement.classList.remove('dark-mode'); // remove dark mode class
    }

    const btn = document.querySelector('#darkModeToggle'); // select the toggle button
    if (btn) {
        btn.textContent = isDark ? '☀️' : '🌙'; // set icon based on current mode
    }
}

function toggleDarkMode() {
    const isDark = document.documentElement.classList.contains('dark-mode'); // check current mode
    const newMode = !isDark; // toggle mode

    if (newMode) {
        document.documentElement.classList.add('dark-mode'); // enable dark mode
        localStorage.setItem('darkMode', 'on'); // store preference
    } else {
        document.documentElement.classList.remove('dark-mode'); // disable dark mode
        localStorage.setItem('darkMode', 'off'); // store preference
    }

    const btn = document.querySelector('#darkModeToggle'); // select the toggle button
    if (btn) {
        btn.textContent = newMode ? '☀️' : '🌙'; // update button icon
    }
}

document.addEventListener('DOMContentLoaded', function() {
    initializeDarkMode(); // apply dark mode on initial load

    const darkModeBtn = document.querySelector('#darkModeToggle'); // get the toggle button
    if (darkModeBtn) {
        darkModeBtn.addEventListener('click', toggleDarkMode); // bind toggle event
    }

    document.querySelectorAll('.logout').forEach(function(logoutLink) { // find all logout buttons
        logoutLink.addEventListener('click', function() {
            localStorage.removeItem('darkMode'); // clear saved preference on logout
        });
    });
});
