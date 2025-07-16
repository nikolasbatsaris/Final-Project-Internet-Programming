document.addEventListener('DOMContentLoaded', function() { // wait until the page is fully loaded

    // add show/hide password toggle to all password fields
    document.querySelectorAll('input[type="password"]').forEach(function(input) { // for each password field
        let wrapper = input.parentElement; // get the current parent of the input
        if (!wrapper.classList.contains('password-wrapper')) { // if it's not already wrapped
            wrapper = document.createElement('div'); // create a new wrapper div
            wrapper.style.position = 'relative'; // set position so toggle button can be absolutely placed
            wrapper.className = 'password-wrapper'; // assign a class for identification
            input.parentNode.insertBefore(wrapper, input); // insert the wrapper before the input
            wrapper.appendChild(input); // move the input into the wrapper
        }

        if (wrapper.querySelector('.show-password-btn')) return; // prevent duplicate toggle buttons

        const btn = document.createElement('button'); // create a new button
        btn.type = 'button'; // make sure it doesn't submit the form
        btn.className = 'show-password-btn'; // assign a class for styling
        btn.textContent = 'Show'; // default button text

        btn.onclick = function(e) { // add click event to toggle visibility
            e.preventDefault(); // prevent default form behavior
            if (input.type === 'password') { // if field is hidden
                input.type = 'text'; // show password
                btn.textContent = 'Hide'; // update button text
            } else {
                input.type = 'password'; // hide password
                btn.textContent = 'Show'; // update button text
            }
        };

        wrapper.appendChild(btn); // add button to the wrapper
    });

    // registration form validation
    const form = document.querySelector('form'); // select the form
    if (form) { // if form exists
        form.addEventListener('submit', function(e) { // on form submit
            let valid = true; // assume the form is valid
            form.querySelectorAll('.error-message').forEach(el => el.textContent = ''); // clear previous error messages

            const username = form.querySelector('input[name="username"]'); // get username input
            if (!username.value.trim()) { // check if empty
                showError(username, 'Username is required.'); // show error
                valid = false; // mark as invalid
            } else if (username.value.length > 25) { // check max length
                showError(username, 'Max 25 characters.'); // show error
                valid = false; // mark as invalid
            }

            const email = form.querySelector('input[name="email"]'); // get email input
            if (!email.value.trim()) { // check if empty
                showError(email, 'Email is required.'); // show error
                valid = false; // mark as invalid
            } else if (!/^\S+@\S+\.\S+$/.test(email.value)) { // check email format
                showError(email, 'Invalid email format.'); // show error
                valid = false; // mark as invalid
            } else if (email.value.length > 30) { // check max length
                showError(email, 'Max 30 characters.'); // show error
                valid = false; // mark as invalid
            }

            const password1 = form.querySelector('input[name="password1"]'); // get first password input
            if (!password1.value) { // check if empty
                showError(password1, 'Password is required.'); // show error
                valid = false; // mark as invalid
            } else if (password1.value.length < 8 || password1.value.length > 30) { // check length bounds
                showError(password1, 'Password must be 8-30 characters.'); // show error
                valid = false; // mark as invalid
            }

            const password2 = form.querySelector('input[name="password2"]'); // get second password input
            if (!password2.value) { // check if empty
                showError(password2, 'Please confirm your password.'); // show error
                valid = false; // mark as invalid
            } else if (password1.value !== password2.value) { // check if passwords match
                showError(password2, 'Passwords do not match.'); // show error
                valid = false; // mark as invalid
            }

            if (!valid) { // if form is not valid
                e.preventDefault(); // prevent submission
            }
        });
    }

    function showError(input, message) { // function to show an error below an input
        let group = input.closest('.form-group'); // find the nearest parent form-group
        if (group) { // if it exists
            let error = group.querySelector('.error-message'); // look for an existing error element
            if (!error) { // if none exists
                error = document.createElement('div'); // create a new div
                error.className = 'error-message'; // assign error styling class
                group.appendChild(error); // add error message container to the form group
            }
            error.textContent = message; // set the message
        }
    }
});
