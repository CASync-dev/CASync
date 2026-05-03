from datetime import datetime, timedelta
from flask import Blueprint, app, render_template, flash
from flask_login import current_user, login_required
from app.form import EventForm, IcalImportForm
from app.models import Calendar, User


loggedin = Blueprint('loggedin', __name__, template_folder='../templates/loggedin', static_folder='../static')


@loggedin.route("/dash")
@login_required
def dash():
    return render_template("loggedin/dash.html")

@loggedin.route("/schedule")
@login_required
def schedule():
    now = datetime.now()
    return render_template("loggedin/schedule.html", now=now, timedelta=timedelta)


@loggedin.route("/groups")
@login_required
def groups():
    return render_template("loggedin/groups.html")


@loggedin.route("/friends")
@login_required
def friends():
    # this will evnetually retrun all the users friends, for now i return all users
    friends = User.query.all()
    # give random avatar urls to each friend using their id as a seed for testing
    for friend in friends:
        friend.avatar_url = f"https://i.pravatar.cc/150?u={friend.id}"

    friends = friends + friends
    return render_template("loggedin/friends.html", friends=friends)


@loggedin.route("/settings", methods=['GET', 'POST'])
@login_required
def settings():
    from services.ical import import_ical
    form = IcalImportForm()
    if form.validate_on_submit():
        url = form.ical_url.data
        result, error = import_ical(url, current_user.id)
        if error:
            flash(f"Error importing iCal: {error}", "error")
        else:
            imported = result.get('imported') or result.get('created', 0)
            updated = result.get('updated', 0)
            flash(f"Imported {imported} events, updated {updated}.", "success")

    syncs = Calendar.query.filter_by(user_id=current_user.id).order_by(Calendar.synced_at.desc()).first()
    last_synced = syncs.synced_at if syncs else "Never"

    # For iCal Links editing and deleting
    links = Calendar.query.filter_by(user_id=current_user.id).all()

    return render_template("loggedin/settings.html", form=form, last_synced=last_synced, links=links)

