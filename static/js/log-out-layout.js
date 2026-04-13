// For now the click event is embedde into log-out-layout.html for simplicity.
// May change in the future

// Loads the mobile sidebar
function mobileMenu() {
    const popout = document.getElementById("mobile-menu");
    popout.style.display = "block";

}

// Unloads mobile sidebar
function closeMobileMenu() {
    const popout = document.getElementById("mobile-menu");
    popout.style.display = "none";

}