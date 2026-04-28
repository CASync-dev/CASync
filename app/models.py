from datetime import datetime, timezone
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import login_manager

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(64), unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))  # Store hashed passwords
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))  # lambda so it's evaluated at insert time, not class definition

    events = db.relationship('Event', backref='owner', lazy='dynamic')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'
    # _repr__ is a special Python method that defines the string representation of an object, used for debugging.
    # When you call repr(obj) or view an object in a Python shell/debugger, Python calls __repr__ to get a readable description.

    # to_dict is a custom method we define to convert our User object into a plain dictionary
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
        }


class Event(db.Model):
    __tablename__ = 'events'

    id           = db.Column(db.Integer, primary_key=True)
    title        = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    date         = db.Column(db.Date, nullable=False)
    start_time   = db.Column(db.Time, nullable=False)
    end_time     = db.Column(db.Time, nullable=False)
    location     = db.Column(db.String(200))                          # optional
    color        = db.Column(db.String(20))         # optional, used for calendar display (e.g. "indigo", "red", etc.)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # links this event to its owner
    ical_uid    = db.Column(db.String(200))   # is the uid of the event in the ical
    ical_id    = db.Column(db.Integer, db.ForeignKey('calendars.id'))   # is the id of the calendar in the ical, we can use this to link events to a calendar and update them later if needed

    # Serialises the object to a plain dict — useful for returning JSON from a route
    # Note: date and time are converted to strings since JSON can't handle Python date/time objects
    def to_dict(self):
        return {
            'id':        self.id,
            'user_id':   self.user_id,
            'username':  self.owner.username,
            'title':     self.title,
            'description': self.description,
            'date':      self.date.isoformat(),
            'startTime': self.start_time.strftime('%H:%M'),
            'endTime':   self.end_time.strftime('%H:%M'),
            'location':  self.location,
            'color':     self.color,
            'ical_uid':  self.ical_uid,
            'ical_id':   self.ical_id,
        }

    def __repr__(self):
        return f'<Event {self.title} on {self.date}>'

class Calendar(db.Model):
    __tablename__ = 'calendars'

    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # links this calendar to its owner
    ical_url   = db.Column(db.String(500), nullable=False)  # URL of the iCal feed
    synced_at  = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))  # when this calendar was last synced

    def __repr__(self):
        return f'<Calendar {self.ical_url}>'