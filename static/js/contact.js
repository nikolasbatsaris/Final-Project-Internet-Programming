
// this javascript code checks if certain animated vehicle elements exist on the page
// if they do it makes them clickable and redirects the user to the registration page when clicked

document.addEventListener('DOMContentLoaded', function () { // run this code after the dom is fully loaded
    // Only run if animation elements exist (i.e., user is not logged in)
    const vehicles = document.querySelectorAll('.truck-group, .car1, .car2, .cta-float'); // select all elements with these classes
    if (vehicles.length > 0) { // if any of these elements exist
        vehicles.forEach(function (vehicle) { // loop through each element
            vehicle.style.cursor = 'pointer'; // make the cursor show as pointer on hover
            vehicle.addEventListener('click', function () { // add click event listener to each element
                window.location.href = '/register/'; // redirect to the register page when clicked
            });
        });
    }
});
