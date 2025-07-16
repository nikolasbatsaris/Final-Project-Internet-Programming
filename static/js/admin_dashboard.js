// handles loading and toggling dark mode based on local storage or system preference
function initializeDarkMode() {
    const pref = localStorage.getItem('darkMode'); // get saved preference
    const isDark = (pref === 'on') || (pref === null && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches); // determine if dark mode should be on
    if (isDark) {
        document.documentElement.classList.add('dark-mode'); // enable dark mode
    } else {
        document.documentElement.classList.remove('dark-mode'); // disable dark mode
    }
    const btn = document.querySelector('#darkModeToggle'); // get dark mode button
    if (btn) {
        btn.textContent = isDark ? '☀️' : '🌙'; // update button icon
    }
}

// toggles dark mode and updates local storage and icon
function toggleDarkMode() {
    const isDark = document.documentElement.classList.contains('dark-mode'); // check if dark mode is active
    const newMode = !isDark; // toggle mode
    if (newMode) {
        document.documentElement.classList.add('dark-mode'); // turn on dark mode
        localStorage.setItem('darkMode', 'on'); // save preference
    } else {
        document.documentElement.classList.remove('dark-mode'); // turn off dark mode
        localStorage.setItem('darkMode', 'off'); // save preference
    }
    const btn = document.querySelector('#darkModeToggle'); // get dark mode button
    if (btn) {
        btn.textContent = newMode ? '☀️' : '🌙'; // update button icon
    }
}

// sets up dark mode and logout logic after page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeDarkMode(); // set initial mode
    const darkModeBtn = document.querySelector('#darkModeToggle'); // get toggle button
    if (darkModeBtn) {
        darkModeBtn.addEventListener('click', toggleDarkMode); // bind toggle function
    }
    // remove saved dark mode preference when user logs out
    document.querySelectorAll('.logout').forEach(function(logoutLink) {
        logoutLink.addEventListener('click', function() {
            localStorage.removeItem('darkMode'); // clear preference
        });
    });
});

// selects or unselects all checkboxes in a group
function toggleAll(type) {
    let checkboxes = document.querySelectorAll('.' + type + '-checkbox'); // get all checkboxes of given type
    let selectAll = document.querySelector('#selectAll' + (type === 'jobrequest' ? 'JobRequests' : 'LiveJobs')); // get the master checkbox
    checkboxes.forEach(cb => cb.checked = selectAll.checked); // set each to match master checkbox
}

// submits bulk approve form
function bulkApprove() {
    document.querySelector('#jobRequestBulkAction').value = 'approve'; // set action to approve
    document.querySelector('#bulkJobRequestForm').submit(); // submit form
}

// submits bulk remove form
function bulkRemove() {
    // Try to remove job requests if the form exists
    var jobRequestForm = document.querySelector('#bulkJobRequestForm');
    var jobRequestAction = document.querySelector('#jobRequestBulkAction');
    if (jobRequestForm && jobRequestAction) {
        jobRequestAction.value = 'remove';
        jobRequestForm.submit();
        return;
    }
    // Otherwise, try to remove live jobs
    var liveJobForm = document.querySelector('#bulkLiveJobsForm');
    var liveJobAction = document.querySelector('#liveJobBulkAction');
    if (liveJobForm && liveJobAction) {
        liveJobAction.value = 'remove';
        liveJobForm.submit();
    }
}

// triggers csv export with current filter and type
function exportCSV() {
    var type = document.querySelector('#exportType').value; // get export type
    window.location.href = exportCSVUrl + '?q=' + encodeURIComponent(q) + '&type=' + encodeURIComponent(type); // redirect to export url
}

// handles show more and show less for recent activity list
(function() {
    const btn = document.querySelector('#expandActivityBtn'); // get toggle button
    const list = document.querySelector('#recentActivityList'); // get activity list
    if (!btn || !list) return; // exit if either is missing

    const allItems = Array.from(list.children); // get all list items

    function showLimited() {
        allItems.forEach((li, i) => li.style.display = i < 5 ? '' : 'none'); // show only first 5 items
        btn.textContent = 'Show All Activity'; // update button text
    }

    function showAll() {
        allItems.forEach(li => li.style.display = ''); // show all items
        btn.textContent = 'Show Less'; // update button text
    }

    let expanded = false; // track toggle state
    showLimited(); // initialize to limited view

    btn.onclick = function() {
        expanded = !expanded; // toggle state
        if (expanded) showAll(); // show all if expanded
        else showLimited(); // otherwise show limited
    };
})();
