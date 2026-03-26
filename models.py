from datetime import datetime, timezone
from extensions import db

class User(db.Model):
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(64), unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

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
    location     = db.Column(db.String(200))
    color        = db.Column(db.String(20), default='indigo')
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

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
