import os

from flask import current_app
from sqlalchemy import delete

from app import db
from app.models import Calendar, Event, User

def removeUser(userid):
    '''
    Parameters:
    - userid: id of user to be removed.
    1. Delete PFP associated with User, if one exists.

    2. Delete Events associated with ical links associated with the user

    3. Delete iCal Links associated with user

    4. Delete User

    ps. Shouldn't need to remove groups with the user.
    '''
    user = User.query.filter(User.id == userid).first()
    calendars = Calendar.query.filter(Calendar.user_id == userid).all()
    events = Event.query.filter(Event.user_id == userid).all()

    # 1. Delete PFP ( Might be redundant to change the bool when we're about to delete the user, but just a precaution. )
    if user.avatarurl:
        os.remove(os.path.join(current_app.config['UPLOAD_PATH'], str(user.id)))
        user.avatarurl = False

    # 2. Delete Events
    delEvents = delete(Event).where(Event.user_id == userid)
    db.session.execute(delEvents)
    # 3. Delete Calendars
    delCal = delete(Calendar).where(Calendar.user_id == userid)
    db.session.execute(delCal)
    # 4. Delete User
    delUser = delete(User).where(User.id == userid)
    db.session.execute(delUser)

    db.session.commit()
    return


