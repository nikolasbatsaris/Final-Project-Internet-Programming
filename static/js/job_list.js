// this javascript code powers the job list page features including dark mode toggle like and book ajax actions job modal detail display responsive pagination and animation toggle logic

// Job List Page JavaScript
// Handles dark mode, like/book actions, modal logic, responsive pagination, and UI interactivity

// --- Dark Mode Theme Persistence ---
// Set dark mode on or off and persist preference
function setDarkMode(on) { // applies dark mode based on input
    if(on) {
        document.documentElement.classList.add('dark-mode'); // enable dark mode class
        localStorage.setItem('darkMode', 'on'); // save preference
    } else {
        document.documentElement.classList.remove('dark-mode'); // disable dark mode class
        localStorage.setItem('darkMode', 'off'); // save preference
    }
}
// Get dark mode preference from localStorage or system
function getDarkMode() { // retrieves stored theme or uses system default
    const pref = localStorage.getItem('darkMode'); // get preference from localstorage
    if (pref === null) {
        return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches; // fallback to system setting
    }
    return pref === 'on'; // return true if preference is on
}

// Main DOMContentLoaded event handler
// Initializes dark mode, like/book buttons, carousel, pagination, modal logic, etc.
document.addEventListener('DOMContentLoaded', function() {
    // --- Dark Mode Toggle Button ---
    // Handles toggling dark mode and updating the button icon
    var darkModeToggle = document.querySelector('#darkModeToggle'); // get dark mode toggle button
    if (darkModeToggle) {
        darkModeToggle.onclick = function() {
            const on = !getDarkMode(); // flip mode
            setDarkMode(on); // apply new mode
            this.textContent = on ? '☀️' : '🌙'; // update icon
        };
        setDarkMode(getDarkMode()); // apply stored or system mode
        darkModeToggle.textContent = getDarkMode() ? '☀️' : '🌙'; // update icon on load
    }
    // Clear dark mode preference on logout
    var logoutLinks = document.querySelectorAll('.logout'); // find all logout links
    if (logoutLinks.length) {
        logoutLinks.forEach(function(logoutLink) {
            logoutLink.addEventListener('click', function() {
                localStorage.removeItem('darkMode'); // clear saved theme
            });
        });
    }

    // --- Like Button AJAX Integration ---
    // Handles like button clicks for each job card (not modal)
    if (window.jQuery) {
        $('.like-btn').click(function(e) {
            e.preventDefault(); // prevent default click
            var btn = $(this); // get button
            var jobId = btn.data('job-id'); // get job id
            var likeCountSpan = $('#like-count-' + jobId); // get like count display
            btn.prop('disabled', true); // disable during ajax
            // Send AJAX POST to like endpoint
            $.ajax({
                url: '/jobs/' + jobId + '/like/',
                type: 'POST',
                headers: { 'X-CSRFToken': getCookie('csrftoken') },
                success: function(data) {
                    if (data.success) {
                        likeCountSpan.text('👍 ' + data.likes); // update count
                        btn.toggleClass('liked', data.action === 'liked'); // toggle class
                        btn.attr('aria-pressed', data.action === 'liked'); // update state
                        // Animate heart icon
                        var heart = btn.find('.heart-icon'); // get heart
                        heart.css('transform', 'scale(1.3)'); // scale up
                        setTimeout(function() { heart.css('transform', 'scale(1)'); }, 180); // reset
                    }
                    btn.prop('disabled', false); // reenable
                },
                error: function() {
                    btn.prop('disabled', false); // reenable on error
                    alert('Error liking job. Please try again.'); // show error
                }
            });
        });
    }

    // --- Pause/Resume Animation Toggle ---
    // Handles pausing/resuming background animations (if present)
    const pauseBtn = document.querySelector('#pauseAnimToggle'); // get pause button
    if (pauseBtn) {
        pauseBtn.onclick = function() {
            const paused = document.body.classList.toggle('paused'); // toggle paused class
            pauseBtn.textContent = paused ? '▶️' : '⏸️'; // update icon
            pauseBtn.title = paused ? 'Resume Animation' : 'Pause Animation'; // update title
        };
    }

    // --- Responsive Pagination: Adjust jobs per page based on screen size ---
    function adjustJobsPerPage() { // adjusts per page count by screen width
        const width = window.innerWidth; // get screen width
        let perPage = 6; // default value
        if (width <= 360) perPage = 1;
        else if (width <= 480) perPage = 2;
        else if (width <= 600) perPage = 3;
        else if (width <= 768) perPage = 4;
        else if (width <= 900) perPage = 5;
        else perPage = 6;
        const urlParams = new URLSearchParams(window.location.search); // get url params
        const currentPerPage = parseInt(urlParams.get('per_page') || '6'); // get current per page
        if (currentPerPage !== perPage) {
            urlParams.set('per_page', perPage); // set new per page
            urlParams.delete('page'); // reset pagination
            const newUrl = window.location.pathname + '?' + urlParams.toString(); // construct new url
            window.location.href = newUrl; // reload page
        }
    }
    window.addEventListener('load', adjustJobsPerPage); // adjust on page load
    window.addEventListener('resize', function() {
        clearTimeout(window.resizeTimeout); // clear old timeout
        window.resizeTimeout = setTimeout(adjustJobsPerPage, 250); // debounce resize
    });

    // --- job detail modal functions ---
    // handles opening the modal, fetching job data, and populating the modal content
    window.openJobDetailModal = function(jobId) { // define global function to open job detail modal with job id
        document.querySelector('#jobDetailModal').style.display = 'flex'; // display the modal by setting its style to flex
        document.body.style.overflow = 'hidden'; // disable page scrolling while modal is open
        fetch(`/jobs/${jobId}/json/`) // fetch job data from server in json format
            .then(response => response.json()) // parse the json response
            .then(data => { // handle the json data
                const template = document.querySelector('#job-detail-template'); // select the html template for job details
                const clone = template.content.cloneNode(true); // create a copy of the template content
                clone.querySelector('.job-title').textContent = data.title || '—'; // insert job title or fallback
                clone.querySelector('.job-description').textContent = data.description || '—'; // insert job description or fallback
                clone.querySelector('.job-origin').textContent = data.origin || '—'; // insert origin city or fallback
                clone.querySelector('.job-origin-address').textContent = data.origin_address ? `(${data.origin_address}, ${data.origin_zip || ''})` : ''; // insert origin address and zip or leave blank
                clone.querySelector('.job-destination').textContent = data.destination || '—'; // insert destination city or fallback
                clone.querySelector('.job-destination-address').textContent = data.destination_address ? `(${data.destination_address}, ${data.destination_zip || ''})` : ''; // insert destination address and zip or leave blank
                clone.querySelector('.job-pickup-date').textContent = data.pickup_date || '—'; // insert pickup date or fallback
                clone.querySelector('.job-pickup-time-from').textContent = data.pickup_time_from || '—'; // insert pickup start time or fallback
                clone.querySelector('.job-pickup-time-to').textContent = data.pickup_time_to || '—'; // insert pickup end time or fallback
                clone.querySelector('.job-delivery-deadline').textContent = data.delivery_deadline || '—'; // insert delivery deadline or fallback
                clone.querySelector('.job-cargo-type').textContent = data.cargo_type || '—'; // insert cargo type or fallback
                // Dimensions (cm) display logic (robust, supports both per-box and main fields)
                const clean = (val) => (val !== undefined && val !== null && val !== '' && val !== 'null') ? val : '—';
                const length = clean(data.length_per_box_cm ?? data.length_cm);
                const width = clean(data.width_per_box_cm ?? data.width_cm);
                const height = clean(data.height_per_box_cm ?? data.height_cm);
                clone.querySelector('.job-length-cm').textContent = length;
                clone.querySelector('.job-width-cm').textContent = width;
                clone.querySelector('.job-height-cm').textContent = height;
                clone.querySelector('.job-special-requirements').textContent = data.special_requirements || '—'; // insert special requirements or fallback
                clone.querySelector('.job-declared-value').textContent = data.declared_value ? `€${data.declared_value}` : '—'; // insert declared value or fallback
                clone.querySelector('.job-like-count').textContent = data.like_count || '0'; // insert like count or default to 0
                clone.querySelector('.job-booked').textContent = data.booked ? 'yes' : 'no'; // show if the job is booked
                clone.querySelector('.job-created-at').textContent = data.created_at || '—'; // insert job creation date or fallback
                const content = document.querySelector('#jobDetailContent'); // select the modal content container
                content.innerHTML = ''; // clear previous content
                content.appendChild(clone); // append the new job detail content
                const likeBtnPlaceholder = content.querySelector('#job-like-btn-placeholder'); // get placeholder for like button
                const bookBtnPlaceholder = content.querySelector('#job-book-btn-placeholder'); // get placeholder for book button
                const loginPrompt = content.querySelector('#job-login-prompt'); // get login prompt element
                likeBtnPlaceholder.innerHTML = ''; // clear like button placeholder
                bookBtnPlaceholder.innerHTML = ''; // clear book button placeholder
                loginPrompt.style.display = 'none'; // hide login prompt by default
                if (data.is_authenticated) { // if user is logged in
                    const likeBtn = document.createElement('button'); // create like button
                    likeBtn.className = 'like-btn-modal' + (data.liked ? ' liked' : ''); // set button class based on like status
                    likeBtn.setAttribute('data-job-id', data.id); // store job id on button
                    likeBtn.setAttribute('aria-pressed', data.liked ? 'true' : 'false'); // set accessibility attribute
                    likeBtn.textContent = data.liked ? '❤️ Liked' : '🤍 Like'; // set button label based on like status
                    likeBtnPlaceholder.appendChild(likeBtn); // add like button to modal
                    const bookBtn = document.createElement('button'); // create book button
                    bookBtn.className = 'book-btn-modal' + (data.booked ? ' booked' : ''); // set class based on booking status
                    bookBtn.setAttribute('data-job-id', data.id); // store job id on button
                    if (data.booked) bookBtn.disabled = true; // disable if already booked
                    bookBtn.textContent = data.booked ? '🚚 Booked!' : '🚚 Book Job'; // set button label based on booking status
                    bookBtnPlaceholder.appendChild(bookBtn); // add book button to modal
                    likeBtn.addEventListener('click', function() { // handle like button click
                        const btn = this; // store button reference
                        btn.disabled = true; // disable button to prevent spamming
                        fetch(`/jobs/${data.id}/like/`, { // send post request to like job
                            method: 'POST', // use post method
                            headers: { 'X-CSRFToken': getCookie('csrftoken') }, // include csrf token
                        })
                        .then(response => response.json()) // parse response
                        .then(res => { // handle response
                            if (res.success) { // if request succeeded
                                btn.classList.toggle('liked', res.action === 'liked'); // toggle liked class
                                btn.setAttribute('aria-pressed', res.action === 'liked'); // update accessibility attribute
                                content.querySelector('.job-like-count').textContent = res.likes; // update like count
                                btn.textContent = res.action === 'liked' ? '❤️ Liked' : '🤍 Like'; // update button label
                            }
                            btn.disabled = false; // re-enable button
                        })
                        .catch(() => { btn.disabled = false; }); // re-enable on error
                    });
                    if (!data.booked) { // if not already booked
                        bookBtn.addEventListener('click', function() { // handle book button click
                            const btn = this; // store button reference
                            btn.disabled = true; // disable to prevent multiple requests
                            fetch(`/jobs/${data.id}/book/`, { // send post request to book job
                                method: 'POST', // use post method
                                headers: { 'X-CSRFToken': getCookie('csrftoken') }, // include csrf token
                            })
                            .then(response => response.json()) // parse response
                            .then(res => { // handle response
                                if (res.success) { // if booking succeeded
                                    btn.textContent = '🚚 Booked!'; // update button label
                                    btn.classList.add('booked'); // mark button as booked
                                    btn.disabled = true; // disable button
                                    content.querySelector('.job-booked').textContent = 'yes'; // update booked status in modal
                                }
                                btn.disabled = false; // re-enable button (in case of failure)
                            })
                            .catch(() => { btn.disabled = false; }); // re-enable on error
                        });
                    }
                } else { // if not authenticated
                    loginPrompt.style.display = ''; // show login prompt
                    loginPrompt.textContent = 'login to like or book this job.'; // set login message
                }
            })
            .catch(error => { // handle fetch error
                document.querySelector('#jobDetailContent').innerHTML = '<div style="color:#e74c3c;">error loading job details. please try again.</div>'; // show error message in modal
            });
    };

    // close the job detail modal
    window.closeJobDetailModal = function() { // define global function to close modal
        document.querySelector('#jobDetailModal').style.display = 'none'; // hide modal
        document.body.style.overflow = 'auto'; // re-enable page scrolling
    };
    // close modal on click outside of modal content
    window.onclick = function(event) { // handle window click
        const modal = document.querySelector('#jobDetailModal'); // get modal element
        if (event.target === modal) window.closeJobDetailModal(); // close modal if clicked outside content
    };



    document.addEventListener('keydown', function(event) { // listen for key press
        if (event.key === 'Escape') window.closeJobDetailModal(); // close modal on escape
    });



});

// --- CSRF Cookie Helper ---
// Utility function to get a cookie value by name (for CSRF protection)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
