from datetime import datetime, timedelta
from flask import Blueprint, app, redirect, render_template, flash, url_for
from flask_login import current_user, login_required, logout_user
from sqlalchemy import delete, update
from app.form import EventForm, IcalImportForm, accountDelForm, changePasswordForm
from services.ical import import_ical
from services.delacc import removeUser
from app import db
from app.models import Calendar, User, Friendship


loggedin = Blueprint('loggedin', __name__, template_folder='../templates/loggedin', static_folder='../static')

@loggedin.context_processor
def inject_friend_requests():
    if not current_user.is_authenticated:
        return {}
    count = Friendship.query.filter(
        (Friendship.recipient_id == current_user.id) &
        (Friendship.status == 'pending')
    ).count()
    return {'friend_requests_count': count}


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
    now = datetime.now()
    return render_template("loggedin/groups.html", groups = current_user.groups, now=now, timedelta=timedelta)


@loggedin.route("/friends")
@login_required
def friends():
    # this will evnetually retrun all the users friends. 
    friends = current_user.get_friends()
    for friend in friends:
        friend.avatar_url = friend.avatar(150)
    # only show pending entries where the current user is the recipient
    friend_requests = Friendship.query.filter((Friendship.recipient_id == current_user.id) & (Friendship.status == 'pending')).all()
    # Join username to the friend request for display purposes, we can do this because we know the sender_id of the sender of the friend request is in the sender_id field of the Friendship model.
    for request in friend_requests:
        request.username = User.query.get(request.sender_id).username
        request.avatar_url = User.query.get(request.sender_id).avatar(150)
    return render_template("loggedin/friends.html", friend_requests=friend_requests, friends=friends)


@loggedin.route("/settings", methods=['GET', 'POST'])
@login_required
def settings():
    form = IcalImportForm()
    changePassform = changePasswordForm()
    acdform = accountDelForm()
    # iCal Form Validation
    if form.validate_on_submit():
        url = form.ical_url.data
        result, error = import_ical(url, current_user.id)
        if error:
            flash(f"Error importing iCal: {error}", "error")
        else:
            imported = result.get('imported') or result.get('created', 0)
            updated = result.get('updated', 0)
            flash(f"Imported {imported} events, updated {updated}.", "success")
    # Account Deletion form Validation
    elif acdform.validate_on_submit():
        if current_user.email != acdform.email.data:
            flash(f'Error in account deletion: Incorrect email.', "error")
        elif current_user.username != acdform.username.data:
            flash(f'Error in account deletion: Incorrect username.', "error")
        elif not current_user.verify_password(acdform.password.data):
            flash(f'Error in account deletion: Incorrect password.', "error")
        else:
            # Will implement the rest of this method at a later date, when groups/friends are fully implemented.
            removeUser(current_user.id)
            logout_user()
            flash('Your account has been deleted.', 'info')
            return redirect(url_for('loggedout.login'))
     # Change Password Form Validation
    elif changePassform.validate_on_submit():
        current = changePassform.current_password.data
        if current_user.verify_password(current):
            current_user.password = changePassform.new_password.data
            db.session.commit()
            flash(f"Successfully changed user's password.", "success")
        else:
            flash(f"Error changing password: Incorrect password.", "error")
    

    syncs = Calendar.query.filter_by(user_id=current_user.id).order_by(Calendar.synced_at.desc()).first()
    last_synced = syncs.synced_at if syncs else "Never"

    # For iCal Links editing and deleting
    links = Calendar.query.filter_by(user_id=current_user.id).all()

    return render_template("loggedin/settings.html", form=form, last_synced=last_synced, links=links, cpform=changePassform, acdform= acdform)

