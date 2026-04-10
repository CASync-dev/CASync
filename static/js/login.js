//TODO: authentication into server

const f = document.getElementById("login");
f.addEventListener("submit", function(event) {
  event.preventDefault();
  // To prevent auto-reload upon submission.
  loginImplementation();
  return false;
})

const errormsg = document.getElementById("field-error");

function loginImplementation() {
  let user = document.forms['login']['user'].value;
  let pw = document.forms['login']['pw'].value;

  if (user == '') {
    errormsg.innerText = 'Please enter your username.';
    return false;
  }
  if (pw == '') {
    errormsg.innerText = 'Please enter your password.';
    return false;
  }
  window.location.href = '/dev/login';
  return false;
}
