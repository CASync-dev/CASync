// Right now the submit detection is implemented directly in the HTML, since authentication has not be implemented
// This will change when we figure authentication out! :)

function loginImplementation() {
  let user = document.forms['login']['user'].value;
  let pw = document.forms['login']['pw'].value;

  if (user == '') {
    alert('Please enter your username.');
    return false;
  }
  if (pw == '') {
    alert('Please enter your password.');
    return false;
  }
  window.location.href = '/dev/login';
  return false;
}
