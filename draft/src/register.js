function regValidation() {
    let mail = document.forms["register"]["mail"].value;
    let user = document.forms["register"]["user"].value;
    let p1 = document.forms["register"]["pw1"].value;
    let p2 = document.forms["register"]["pw2"].value;

    if (!check(mail, "email")) { return false;}
    if (!check(user, "username")) { return false;}
    if (!check(p1, "password")) { return false;}
    if (p1 != p2) {
        alert("Passwords don't match; Please try again.");
        return false;
    }
    
    alert("Register submission has not been implemented. Look out in the future!");
    return false;
}

function check(x, y) {
    if (x == "") {
        alert("Please enter a " + y + ".");
        return false;
    }
    return true;
}