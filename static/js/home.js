// this javascript code handles navigation for the get started button on page load
// it finds the button with a data url and redirects the user to that url when clicked

document.addEventListener('DOMContentLoaded', function() { // wait for the document to fully load
    // Use querySelector for the Get Started button
    const getStartedBtn = document.querySelector('.cta-btn[data-url]'); // select the button with data-url
    if (getStartedBtn) {
        getStartedBtn.onclick = function() { // add click event to button
            window.location.href = this.getAttribute('data-url'); // navigate to the url in data attribute
        };
    }
});
