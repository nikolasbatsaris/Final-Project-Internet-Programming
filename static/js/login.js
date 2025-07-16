// run the script when the document has fully loaded
document.addEventListener('DOMContentLoaded', function() {

    // find all input fields of type password
    document.querySelectorAll('input[type="password"]').forEach(function(input) {

        // get the parent element of the input
        let wrapper = input.parentElement;

        // if the parent does not already have a password wrapper class
        if (!wrapper.classList.contains('password-wrapper')) {

            // create a new wrapper div element
            wrapper = document.createElement('div');

            // set the wrapper to have relative positioning
            wrapper.style.position = 'relative';

            // give the wrapper a class name for styling
            wrapper.className = 'password-wrapper';

            // insert the wrapper before the password input
            input.parentNode.insertBefore(wrapper, input);

            // move the input inside the new wrapper
            wrapper.appendChild(input);
        }

        // if a show password button already exists do nothing
        if (wrapper.querySelector('.show-password-btn')) return;

        // create a new button element
        const btn = document.createElement('button');

        // set the button type to button to prevent form submission
        btn.type = 'button';

        // add a class name to the button for styling
        btn.className = 'show-password-btn';

        // set the initial button text to show
        btn.textContent = 'Show';

        // add a click event to the button
        btn.onclick = function(e) {

            // prevent default button behavior
            e.preventDefault();

            // if the input type is password switch it to text and change button label to hide
            if (input.type === 'password') {
                input.type = 'text';
                btn.textContent = 'Hide';

            // otherwise switch input back to password and change label to show
            } else {
                input.type = 'password';
                btn.textContent = 'Show';
            }
        };

        // add the button to the wrapper next to the input
        wrapper.appendChild(btn);
    });
});
