from flask import Blueprint, redirect, session, url_for

api_dev = Blueprint('api_dev', __name__)

#--- API routes - at the moment they return json responses but thats not long term

#curent mock login logic - just toggles login state for testing purposes
# the login and logout pages currently just toggle the session variable 
# and redirect to the appropriate page, but this will be replaced with 
# real login logic later on
@api_dev.route("/dev/login")
def dev_login():
    session['logged_in'] = True
    return redirect(url_for('loggedin.dash'))

@api_dev.route("/dev/logout")
def dev_logout():
    session.clear()
    return redirect(url_for('loggedout.home'))