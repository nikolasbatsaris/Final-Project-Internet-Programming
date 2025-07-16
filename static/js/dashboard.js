// this javascript code handles modal logic for showing job and job request details
// it listens for clicks on dashboard items loads data via fetch and fills the modal template
// it also handles closing the modal either via the close button or clicking outside the modal content

// Dashboard Modal Logic

document.addEventListener('DOMContentLoaded', function() { // waits until the dom is fully loaded
    // Open modal when a dashboard job item is clicked
    document.querySelectorAll('.dashboard-list-item[data-type="job"]').forEach(function(item) { // selects all job type items
        item.addEventListener('click', function() { // adds click event to each job item
            var jobId = this.getAttribute('data-id'); // gets the job id from data attribute
            openJobDetailModal(jobId); // calls function to open job modal
        });
    });

    // Open modal when a dashboard job request item is clicked
    document.querySelectorAll('.dashboard-list-item[data-type="request"]').forEach(function(item) { // selects all request type items
        item.addEventListener('click', function() { // adds click event to each request item
            var requestId = this.getAttribute('data-id'); // gets the request id from data attribute
            openJobRequestDetailModal(requestId); // calls function to open job request modal
        });
    });

    // Close modal logic
    var closeBtn = document.querySelector('#closeJobDetailModal'); // selects close button
    var modal = document.querySelector('#jobDetailModal'); // selects modal container
    if (closeBtn && modal) { // only if both elements exist
        closeBtn.onclick = function() { // when close button is clicked
            modal.style.display = 'none'; // hide modal
            document.body.style.overflow = ''; // restore page scroll
        };
        // Also close modal when clicking outside modal-content
        modal.addEventListener('click', function(e) { // add click event on modal background
            if (e.target === modal) { // check if clicked outside content
                modal.style.display = 'none'; // hide modal
                document.body.style.overflow = ''; // restore scroll
            }
        });
    }
});

// Modal open/fill logic (adapted from job_list.js)
function openJobDetailModal(jobId) { // function to show job modal and fill with data
    var modal = document.querySelector('#jobDetailModal'); // select modal element
    modal.style.display = 'flex'; // show modal with flex layout
    document.body.style.overflow = 'hidden'; // prevent scrolling
    fetch(`/jobs/${jobId}/json/`) // fetch job data from server
        .then(response => response.json()) // parse response as json
        .then(data => { // once data is available
            const template = document.querySelector('#job-detail-template'); // select modal template
            const clone = template.content.cloneNode(true); // clone the template
            clone.querySelector('.job-title').textContent = data.title || '—'; // fill job title
            clone.querySelector('.job-description').textContent = data.description || '—'; // fill job description
            clone.querySelector('.job-origin').textContent = data.origin || '—'; // fill origin city
            clone.querySelector('.job-origin-address').textContent = data.origin_address ? `(${data.origin_address}, ${data.origin_zip || ''})` : ''; // fill origin address
            clone.querySelector('.job-destination').textContent = data.destination || '—'; // fill destination city
            clone.querySelector('.job-destination-address').textContent = data.destination_address ? `(${data.destination_address}, ${data.destination_zip || ''})` : ''; // fill destination address
            clone.querySelector('.job-pickup-date').textContent = data.pickup_date || '—'; // fill pickup date
            clone.querySelector('.job-pickup-time-from').textContent = data.pickup_time_from || '—'; // fill pickup time from
            clone.querySelector('.job-pickup-time-to').textContent = data.pickup_time_to || '—'; // fill pickup time to
            clone.querySelector('.job-delivery-deadline').textContent = data.delivery_deadline || '—'; // fill delivery deadline
            clone.querySelector('.job-cargo-type').textContent = data.cargo_type || '—'; // fill cargo type
            clone.querySelector('.job-length-cm').textContent = data.length_cm || '—'; // fill cargo length
            clone.querySelector('.job-width-cm').textContent = data.width_cm || '—'; // fill cargo width
            clone.querySelector('.job-height-cm').textContent = data.height_cm || '—'; // fill cargo height
            clone.querySelector('.job-special-requirements').textContent = data.special_requirements || '—'; // fill special requirements
            clone.querySelector('.job-declared-value').textContent = data.declared_value ? `€${data.declared_value}` : '—'; // fill declared value
            clone.querySelector('.job-like-count').textContent = data.like_count || '0'; // fill like count
            clone.querySelector('.job-booked').textContent = data.booked ? 'Yes' : 'No'; // fill booked status
            clone.querySelector('.job-created-at').textContent = data.created_at || '—'; // fill creation date
            const content = document.querySelector('#jobDetailContent'); // select modal content area
            content.innerHTML = ''; // clear old content
            content.appendChild(clone); // add new filled content
        });
}

// Modal open/fill logic for job requests
function openJobRequestDetailModal(requestId) { // function to show request modal and fill with data
    var modal = document.querySelector('#jobDetailModal'); // select modal
    modal.style.display = 'flex'; // show modal
    document.body.style.overflow = 'hidden'; // disable page scroll
    fetch(`/requests/${requestId}/json/`) // fetch request data
        .then(response => response.json()) // parse response
        .then(data => { // when data is available
            const template = document.querySelector('#job-detail-template'); // get template
            const clone = template.content.cloneNode(true); // clone template content
            clone.querySelector('.job-title').textContent = data.title || '—'; // fill title
            clone.querySelector('.job-description').textContent = data.description || '—'; // fill description
            clone.querySelector('.job-origin').textContent = data.origin || '—'; // fill origin city
            clone.querySelector('.job-origin-address').textContent = data.origin_address ? `(${data.origin_address}, ${data.origin_zip || ''})` : ''; // fill origin address
            clone.querySelector('.job-destination').textContent = data.destination || '—'; // fill destination city
            clone.querySelector('.job-destination-address').textContent = data.destination_address ? `(${data.destination_address}, ${data.destination_zip || ''})` : ''; // fill destination address
            clone.querySelector('.job-pickup-date').textContent = data.pickup_date || '—'; // fill pickup date
            clone.querySelector('.job-pickup-time-from').textContent = data.pickup_time_from || '—'; // fill pickup time from
            clone.querySelector('.job-pickup-time-to').textContent = data.pickup_time_to || '—'; // fill pickup time to
            clone.querySelector('.job-delivery-deadline').textContent = data.delivery_deadline || '—'; // fill delivery deadline
            clone.querySelector('.job-cargo-type').textContent = data.cargo_type || '—'; // fill cargo type
            // Dimensions (cm) display logic for job requests
            let length = '—', width = '—', height = '—';
            if ('length_per_box_cm' in data || 'width_per_box_cm' in data || 'height_per_box_cm' in data) {
              length = (data.length_per_box_cm !== undefined && data.length_per_box_cm !== null && data.length_per_box_cm !== '') ? data.length_per_box_cm : (data.length_cm !== undefined && data.length_cm !== null && data.length_cm !== '' ? data.length_cm : '—');
              width = (data.width_per_box_cm !== undefined && data.width_per_box_cm !== null && data.width_per_box_cm !== '') ? data.width_per_box_cm : (data.width_cm !== undefined && data.width_cm !== null && data.width_cm !== '' ? data.width_cm : '—');
              height = (data.height_per_box_cm !== undefined && data.height_per_box_cm !== null && data.height_per_box_cm !== '') ? data.height_per_box_cm : (data.height_cm !== undefined && data.height_cm !== null && data.height_cm !== '' ? data.height_cm : '—');
            } else {
              length = (data.length_cm !== undefined && data.length_cm !== null && data.length_cm !== '') ? data.length_cm : '—';
              width = (data.width_cm !== undefined && data.width_cm !== null && data.width_cm !== '') ? data.width_cm : '—';
              height = (data.height_cm !== undefined && data.height_cm !== null && data.height_cm !== '') ? data.height_cm : '—';
            }
            clone.querySelector('.job-length-cm').textContent = length;
            clone.querySelector('.job-width-cm').textContent = width;
            clone.querySelector('.job-height-cm').textContent = height;
            clone.querySelector('.job-special-requirements').textContent = data.special_requirements || '—'; // fill special requirements
            clone.querySelector('.job-declared-value').textContent = data.declared_value ? `€${data.declared_value}` : '—'; // fill declared value
            clone.querySelector('.job-like-count').textContent = data.like_count !== undefined ? data.like_count : '—'; // fill like count
            clone.querySelector('.job-booked').textContent = data.status ? data.status.charAt(0).toUpperCase() + data.status.slice(1) : '—'; // fill status
            clone.querySelector('.job-created-at').textContent = data.created_at || '—'; // fill creation date
            const content = document.querySelector('#jobDetailContent'); // select content area
            content.innerHTML = ''; // clear old content
            content.appendChild(clone); // append new content
        });
}
