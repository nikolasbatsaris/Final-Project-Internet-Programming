// dark mode functionality

function initializeDarkMode() {
    const pref = localStorage.getItem('darkMode'); // get stored dark mode preference from local storage
    const isDark = (pref === 'on') || (pref === null && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches); // determine if dark mode should be enabled

    if (isDark) {
        document.documentElement.classList.add('dark-mode'); // apply dark mode class to the root html element
    } else {
        document.documentElement.classList.remove('dark-mode'); // remove dark mode class
    }

    const btn = document.querySelector('#darkModeToggle'); // get the dark mode toggle button by id 
    if (btn) {
        btn.textContent = isDark ? '☀️' : '🌙'; // update the button icon depending on mode
    }
}

function toggleDarkMode() {
    const isDark = document.documentElement.classList.contains('dark-mode'); // check if dark mode is currently active
    const newMode = !isDark; // toggle the current mode

    if (newMode) {
        document.documentElement.classList.add('dark-mode'); // enable dark mode
        localStorage.setItem('darkMode', 'on'); // save preference in local storage
    } else {
        document.documentElement.classList.remove('dark-mode'); // disable dark mode
        localStorage.setItem('darkMode', 'off'); // save preference in local storage
    }

    const btn = document.querySelector('#darkModeToggle'); // get the dark mode toggle button 
    if (btn) {
        btn.textContent = newMode ? '☀️' : '🌙'; // update icon based on new mode
    }
}

// initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeDarkMode(); // run dark mode setup when the page loads

    const darkModeBtn = document.querySelector('#darkModeToggle'); // get the dark mode toggle button 
    if (darkModeBtn) {
        darkModeBtn.addEventListener('click', toggleDarkMode); // bind click to toggle dark mode
    }

    document.querySelectorAll('.logout').forEach(function(logoutLink) { // select all logout buttons
        logoutLink.addEventListener('click', function() {
            localStorage.removeItem('darkMode'); // clear dark mode preference on logout
        });
    });
});
