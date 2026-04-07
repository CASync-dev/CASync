// Right now the submit detection is implemented directly in the HTML, since authentication has not be implemented
// This will change when we figure authentication out! :)
const f = document.getElementById("register");
f.addEventListener("submit", function(event) {
    event.preventDefault();
  // To prevent auto-reload upon submission.
    regValidation();
    return false;
});
const errormsg = document.getElementById("field-error");

function regValidation() {
    let mail = document.forms["register"]["mail"].value;
    let user = document.forms["register"]["user"].value;
    let p1 = document.forms["register"]["pw1"].value;
    let p2 = document.forms["register"]["pw2"].value;

    if (!check(mail, "email")) { return false;}
    if (!check(user, "username")) { return false;}
    if (!check(p1, "password")) { return false;}
    if (p1 != p2) {
        errormsg.innerText = "Passwords don't match; Please try again.";
        return false;
    }
    
    alert("Register submission has not been implemented. Look out in the future!");
    return false;
}

function check(x, y) {
    if (x == "") {
        let msg = "Please enter a " + y + ".";
        errormsg.innerText = msg;
        return false;
    }
    return true;
}