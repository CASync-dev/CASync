from flask import Blueprint, redirect, render_template, session, url_for, flash
from app.form import EventForm, IcalImportForm

loggedin = Blueprint('loggedin', __name__, template_folder='../templates/loggedin', static_folder='../static')

# --- Session login logic
@loggedin.context_processor
# This function injects the 'logged_in' variable into all tempaltes
def inject_auth():
    return {'logged_in': session.get('logged_in', False)}
def require_login():
    if not session.get('logged_in'):
        return redirect(url_for('loggedout.home'))
    return None

@loggedin.route("/dash")
def dash():
    guard = require_login()
    if guard: return guard
    return render_template("loggedin/dash.html")

@loggedin.route("/schedule")
def schedule():
    guard = require_login()
    if guard: return guard
    return render_template("loggedin/schedule.html")


@loggedin.route("/groups")
def groups():
    guard = require_login()
    if guard: return guard
    return render_template("loggedin/groups.html")


@loggedin.route("/friends")
def friends():
    guard = require_login()
    if guard: return guard
    return render_template("loggedin/friends.html")


@loggedin.route("/settings", methods=['GET', 'POST'])
def settings():
    from services.ical import import_ical
    # login protection
    guard = require_login()
    if guard: return guard
    # ical submit form
    form = IcalImportForm()
    if form.validate_on_submit():
        url = form.ical_url.data
        user_id = int(form.user_id.data)
        # Process the iCal import logic here
        result, error = import_ical(url, user_id)
        if error:
            flash(f"Error importing iCal: {error}", "error")
        else:
            imported = result.get('imported') or result.get('created', 0)
            updated = result.get('updated', 0)
            flash(f"Imported {imported} events, updated {updated}.", "success")

    return render_template("loggedin/settings.html", form=form)
