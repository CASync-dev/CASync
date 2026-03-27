function loginImplementation() {
    let user = document.forms["login"]["user"].value;
    let pw = document.forms["login"]["pw"].value;

    if (user == "") {
        alert("Please enter your username.");
        return false;
    }
    if (pw == "") {
        alert("Please enter your password.");
        return false;
    }
    alert("Login submission has not been implemented. Look out in the future!");
    return false;
}