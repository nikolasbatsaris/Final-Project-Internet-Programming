// this javascript code adds show and hide buttons to all password input fields
// each password field is wrapped and given a toggle button that reveals or hides the password when clicked

// wait for the page to load
document.addEventListener('DOMContentLoaded', function() {
    // find all password input fields
    const passwordFields = document.querySelectorAll('input[type="password"]');
    // for each password field
    passwordFields.forEach(function(field) {
        // create a wrapper div to hold the field and toggle button
        const wrapper = document.createElement('div');
        // set the wrapper to relative so the button can be positioned inside
        wrapper.style.position = 'relative';
        // put the wrapper before the field in the dom
        field.parentNode.insertBefore(wrapper, field);
        // move the field inside the wrapper
        wrapper.appendChild(field);

        // create a button to show or hide the password
        const toggle = document.createElement('button');
        // set button type so it doesn't submit the form
        toggle.type = 'button';
        // set the button text to show
        toggle.textContent = 'Show';
        // position the button inside the wrapper, to the right
        toggle.style.position = 'absolute';
        toggle.style.right = '8px';
        toggle.style.top = '50%';
        // center the button vertically
        toggle.style.transform = 'translateY(-50%)';
        // add some padding to the button
        toggle.style.padding = '2px 8px';
        // make the button text a bit smaller
        toggle.style.fontSize = '0.9em';
        // make the cursor a pointer when hovering
        toggle.style.cursor = 'pointer';
        // add the button to the wrapper
        wrapper.appendChild(toggle);

        // when the button is clicked
        toggle.addEventListener('click', function() {
            // if the field is a password, show it
            if (field.type === 'password') {
                field.type = 'text';
                // change button text to hide
                toggle.textContent = 'Hide';
            } else {
                // if it's visible, hide it again
                field.type = 'password';
                // change button text to show
                toggle.textContent = 'Show';
            }
        });
    });
});
