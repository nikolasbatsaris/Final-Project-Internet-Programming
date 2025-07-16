// this javascript code manages dark mode and mobile navigation menu behavior
// it saves the user preference for dark mode using local storage
// it toggles between light and dark themes and updates icons accordingly
// it also handles showing and hiding the mobile navigation menu when clicking links or outside the menu

// when the page is loaded
document.addEventListener('DOMContentLoaded', function() {
    // function to turn dark mode on or off
    function setDarkMode(on) {
        // if dark mode is on
        if(on) {
            // add dark-mode class to html
            document.documentElement.classList.add('dark-mode');
            // save dark mode on in local storage
            localStorage.setItem('darkMode', 'on');
        } else {
            // remove dark-mode class from html
            document.documentElement.classList.remove('dark-mode');
            // save dark mode off in local storage
            localStorage.setItem('darkMode', 'off');
        }
    }




    // function to get dark mode setting
    function getDarkMode() {
        // get dark mode from local storage
        const pref = localStorage.getItem('darkMode');
        // if no setting is found
        if (pref === null) {
            // use system dark mode setting
            return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        }
        // return true if dark mode is on
        return pref === 'on';
    }




    // function to show or hide mobile menu
    function toggleMobileMenu() {
        // get mobile nav element
        const mobileNav = document.querySelector('#mobileNav');
        // toggle active class
        mobileNav.classList.toggle('active');
    }




    // close mobile menu when clicking outside
    document.addEventListener('click', function(event) {
        // get mobile nav
        const mobileNav = document.querySelector('#mobileNav');
        // get mobile menu button
        const mobileMenuToggle = document.querySelector('#mobileMenuToggle');
        // if click is not on nav or button
        if (!mobileNav.contains(event.target) && !mobileMenuToggle.contains(event.target)) {
            // close mobile nav
            mobileNav.classList.remove('active');
        }
    });




    // close mobile menu when clicking a link
    document.querySelectorAll('.mobile-nav a').forEach(link => {
        // for each link add click event
        link.addEventListener('click', function() {
            // close mobile nav
            document.querySelector('#mobileNav').classList.remove('active');
        });
    });




    // when dark mode button is clicked
    document.querySelector('#darkModeToggle').onclick = function() {
        // toggle dark mode
        const on = !getDarkMode();
        setDarkMode(on);
        // change icon on button
        this.textContent = on ? '☀️' : '🌙';
        // change icon on mobile button
        document.querySelector('#mobileDarkModeToggle').textContent = on ? '☀️' : '🌙';
    };




    // when mobile dark mode button is clicked
    document.querySelector('#mobileDarkModeToggle').onclick = function() {
        // toggle dark mode
        const on = !getDarkMode();
        setDarkMode(on);
        // change icon on button
        this.textContent = on ? '☀️' : '🌙';
        // change icon on desktop button
        document.querySelector('#darkModeToggle').textContent = on ? '☀️' : '🌙';
    };




    // when mobile menu button is clicked
    document.querySelector('#mobileMenuToggle').onclick = function() {
        // open or close mobile menu
        toggleMobileMenu();
    };



    
    // set dark mode on page load
    setDarkMode(getDarkMode());
    // set icon for dark mode button
    const darkModeIcon = getDarkMode() ? '☀️' : '🌙';
    document.querySelector('#darkModeToggle').textContent = darkModeIcon;
    document.querySelector('#mobileDarkModeToggle').textContent = darkModeIcon;
}); 
