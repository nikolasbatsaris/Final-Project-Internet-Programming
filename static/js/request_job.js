// progress bar logic
const formSections = document.querySelectorAll('.card-section'); // select all form sections with class 'card-section'
const progressBar = document.querySelector('#progressBar'); // get the progress bar element by ID
if (formSections.length && progressBar) { // check if both form sections and progress bar exist
    let filled = 0; // initialize the filled percentage
    formSections.forEach((section, idx) => { // loop through each section with its index
        section.addEventListener('focusin', () => { // add focusin event to detect when user enters a section
            filled = ((idx + 1) / formSections.length) * 100; // calculate progress based on section index
            progressBar.style.width = filled + '%'; // update the progress bar width
        });
    });
    // on page load, set to first section
    progressBar.style.width = (1 / formSections.length) * 100 + '%'; // initialize progress bar to first section
}

// enforce word limit on relevant fields
function enforceWordLimit(input, maxWords) { // function to limit input based on max word count
    input.addEventListener('input', function() { // add input event listener to the field
        let words = input.value.split(/\s+/).filter(Boolean); // split input into words and remove empty ones
        if (words.length > maxWords) { // if word count exceeds limit
            input.value = words.slice(0, maxWords).join(' '); // truncate to the maximum number of words
            if (!input.nextElementSibling || !input.nextElementSibling.classList.contains('word-limit-warning')) { // if no warning exists
                const warn = document.createElement('div'); // create warning div
                warn.className = 'word-limit-warning'; // assign class for styling
                warn.style.color = '#e74c3c'; // set warning color
                warn.style.fontSize = '0.95em'; // set font size
                warn.textContent = `Maximum ${maxWords} words allowed.`; // set warning text
                input.parentNode.appendChild(warn); // append warning to the input's parent
            }
        } else { // if word count is within limit
            if (input.nextElementSibling && input.nextElementSibling.classList.contains('word-limit-warning')) { // check if warning exists
                input.nextElementSibling.remove(); // remove the warning
            }
        }
    });
}
document.addEventListener('DOMContentLoaded', function() { // wait for the full DOM to load
    const wordLimitedFields = [ // list of input IDs to apply word limit enforcement
        'id_title', 'id_description', 'id_origin', 'id_origin_address', 'id_origin_zip',
        'id_destination', 'id_destination_address', 'id_destination_zip',
        'id_special_requirements', 'id_reference_code'
    ];
    wordLimitedFields.forEach(function(id) { // loop through each field ID
        const field = document.querySelector('#' + id); // get the input element by ID
        if (field) enforceWordLimit(field, 50); // if found, apply the enforceWordLimit function with max 50 words
    });
});
