from datetime import datetime, timezone
from extensions import db

class User(db.Model):
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(64), unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))  # lambda so it's evaluated at insert time, not class definition

    # Not a real column — a virtual link so you can do user.events to get all events for a user
    # backref='owner' means you can also go the other way: event.owner gives you the user
    # lazy='dynamic' returns a query object instead of loading everything at once
    events = db.relationship('Event', backref='owner', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'


class Event(db.Model):
    __tablename__ = 'events'

    id           = db.Column(db.Integer, primary_key=True)
    title        = db.Column(db.String(200), nullable=False)
    date         = db.Column(db.Date, nullable=False)
    start_time   = db.Column(db.Time, nullable=False)
    end_time     = db.Column(db.Time, nullable=False)
    location     = db.Column(db.String(200))                          # optional
    color        = db.Column(db.String(20), default='indigo')         # optional, falls back to indigo
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # links this event to its owner

    # Serialises the object to a plain dict — useful for returning JSON from a route
    # Note: date and time are converted to strings since JSON can't handle Python date/time objects
    def to_dict(self):
        return {
            'id':        self.id,
            'title':     self.title,
            'date':      self.date.isoformat(),
            'startTime': self.start_time.strftime('%H:%M'),
            'endTime':   self.end_time.strftime('%H:%M'),
            'location':  self.location,
            'color':     self.color,
        }

    def __repr__(self):
        return f'<Event {self.title} on {self.date}>'
