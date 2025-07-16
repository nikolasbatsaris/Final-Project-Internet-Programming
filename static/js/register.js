// this javascript code adds password visibility toggles to password inputs and validates registration form fields before submission including required fields email format and password match

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

    // find the registration form
    const form = document.querySelector('form');
    // if the form exists
    if (form) {
        // when the form is submitted
        form.addEventListener('submit', function(e) {
            // start with valid as true
            let valid = true;
            // make an array to hold error messages
            let messages = [];
            // find all required fields in the form
            const requiredFields = form.querySelectorAll('[required]');
            // check each required field
            requiredFields.forEach(function(field) {
                // if the field is empty
                if (!field.value.trim()) {
                    valid = false;
                    // add a message for this field
                    messages.push(field.name + ' is required.');
                }
            });
            // find the email field
            const emailField = form.querySelector('input[type="email"]');
            // if the email field exists and has a value
            if (emailField && emailField.value) {
                // regex to check email format
                const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                // if the email doesn't match the pattern
                if (!emailPattern.test(emailField.value)) {
                    valid = false;
                    // add a message for invalid email
                    messages.push('Invalid email format.');
                }
            }
            // find the two password fields
            const password1 = form.querySelector('input[name="password1"]');
            const password2 = form.querySelector('input[name="password2"]');
            // if both password fields exist and don't match
            if (password1 && password2 && password1.value !== password2.value) {
                valid = false;
                // add a message for password mismatch
                messages.push('Passwords do not match.');
            }
            // find or create a div to show errors
            let errorDiv = document.querySelector('#register-errors');
            if (!errorDiv) {
                errorDiv = document.createElement('div');
                errorDiv.id = 'register-errors';
                errorDiv.style.color = 'red';
                errorDiv.style.marginBottom = '1em';
                // put the error div at the top of the form
                form.prepend(errorDiv);
            }
            // clear any old errors
            errorDiv.innerHTML = '';
            // if the form is not valid
            if (!valid) {
                // stop the form from submitting
                e.preventDefault();
                // show each error message
                messages.forEach(function(msg) {
                    const p = document.createElement('p');
                    p.textContent = msg;
                    errorDiv.appendChild(p);
                });
            }
        });
    }

    // username/email availability check (ajax) - to be added later
    // ...
});
