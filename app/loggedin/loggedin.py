from datetime import datetime, timedelta
from flask import Blueprint, app, render_template, flash
from flask_login import current_user, login_required
from app.form import EventForm, IcalImportForm
from app.models import Calendar, User, Friendship


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
    # this will evnetually retrun all the users friends. 
    friends = current_user.get_friends()
    for friend in friends:
        friend.avatar_url = f"https://i.pravatar.cc/150?u={friend.id}"
    # only show pending entries where the current user is the recipient
    friend_requests = Friendship.query.filter((Friendship.recipient_id == current_user.id) & (Friendship.status == 'pending')).all()
    # Join username to the friend request for display purposes, we can do this because we know the sender_id of the sender of the friend request is in the sender_id field of the Friendship model.
    for request in friend_requests:
        request.username = User.query.get(request.sender_id).username
        request.avatar_url = f"https://i.pravatar.cc/150?u={request.id}"
    return render_template("loggedin/friends.html", friends=friends, friend_requests=friend_requests)


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

    return render_template("loggedin/settings.html", form=form, last_synced=last_synced)

