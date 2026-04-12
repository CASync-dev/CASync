// JS for layout for logged-out pages (homepage, faq)
// Compeltely broken RIP will fix later
const menubutton = document.getElementById("mobile-menu-button-open");
menubutton.addEventListener("click", mobileMenu);

function mobileMenu() {
    const popout = document.getElementById("mobile-menu");
    popout.style.display = "block";

}