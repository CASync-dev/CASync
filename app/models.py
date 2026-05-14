from datetime import datetime, timezone
from flask import current_app, url_for
from app import db
from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Table, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship
from . import login_manager
from hashlib import md5


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Base(DeclarativeBase):
    pass


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))  # Store hashed passwords
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )  # lambda so it's evaluated at insert time, not class definition
    avatarurl = db.Column(db.Boolean, default=False)  # Default uses Gravatar

    events = db.relationship("Event", backref="owner", lazy="dynamic")
    # Many to many relationship with groups

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"

    # _repr__ is a special Python method that defines the string representation of an object, used for debugging.
    # When you call repr(obj) or view an object in a Python shell/debugger, Python calls __repr__ to get a readable description.

    # to_dict is a custom method we define to convert our User object into a plain dictionary
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
            "pfp": self.avatar(200),
        }

    def gravatar(self, size):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return f"https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}"

    def getavatar(self):
        return url_for("static", filename="avatars/" + str(self.id))

    def avatar(self, size):
        if self.avatarurl:
            return self.getavatar()
        else:
            return self.gravatar(150)

    def public_dict(self):
        return {"id": self.id, "username": self.username, "pfp": self.avatar(200)}

    def get_friends(self):
        # This method retrieves all friends of the user by querying the Friendship model for entries where the user is either the sender
        #  or recipient of an accepted friendship. It then combines these results to return a list of User objects representing the user's friends.
        sent = (
            db.session.query(User)
            .join(Friendship, Friendship.recipient_id == User.id)
            .filter(Friendship.sender_id == self.id, Friendship.status == "accepted")
        )
        received = (
            db.session.query(User)
            .join(Friendship, Friendship.sender_id == User.id)
            .filter(Friendship.recipient_id == self.id, Friendship.status == "accepted")
        )
        # returns a nice list of the users friedns regardless of who sent the request, much simpelr for front end
        return sent.union(received).all()


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    # Full ISO datetimes (UTC) so events can span multiple days.
    start_time = db.Column(db.DateTime(timezone=True), nullable=False)
    end_time = db.Column(db.DateTime(timezone=True), nullable=False)
    location = db.Column(db.String(200))  # optional
    color = db.Column(
        db.String(20)
    )  # optional, used for calendar display (e.g. "indigo", "red", etc.)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )  # links this event to its owner
    ical_uid = db.Column(db.String(200))  # is the uid of the event in the ical
    ical_id = db.Column(
        db.Integer, db.ForeignKey("calendars.id")
    )  # is the id of the calendar in the ical, we can use this to link events to a calendar and update them later if needed
    going = db.Column(db.Boolean, nullable=False, default=True)  # whether the user is going to this event

    # Serialises the object to a plain dict — useful for returning JSON from a route
    # startTime/endTime are full ISO datetimes (UTC). The frontend derives the date and
    # local HH:MM display from these.
    #
    # SQLite has no native timezone storage, so DateTime(timezone=True) values come back
    # as naive datetimes even though we always write UTC. Re-attach UTC here so the JSON
    # string carries the offset and the browser converts to the user's local time.
    def to_dict(self):
        def _iso(dt):
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.owner.username,
            "title": self.title,
            "description": self.description,
            "startTime": _iso(self.start_time),
            "endTime": _iso(self.end_time),
            "location": self.location,
            "color": self.color,
            "ical_uid": self.ical_uid,
            "ical_id": self.ical_id,
            "going": self.going,
        }

    def __repr__(self):
        return f"<Event {self.title} at {self.start_time}>"


class Calendar(db.Model):
    __tablename__ = "calendars"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )  # links this calendar to its owner
    ical_url = db.Column(db.String(500), nullable=False)  # URL of the iCal feed
    synced_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )  # when this calendar was last synced

    def __repr__(self):
        return f"<Calendar {self.ical_url}>"


class Friendship(db.Model):
    __tablename__ = "friendships"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )  # the user who sent the friend request
    recipient_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )  # the user who received the friend request
    status = db.Column(
        db.String(20), nullable=False
    )  # "pending", "accepted", "rejected"
    created_at = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )  # when the friend request was created
    accepted_at = db.Column(
        db.DateTime(timezone=True)
    )  # when the friend request was accepted (null if still pending or rejected)

    def __repr__(self):
        return f"<Friendship {self.sender_id} -> {self.recipient_id} ({self.status})>"


# Holds groups | We'll use another table to hold user_ids.
class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_name = db.Column(db.String(500), nullable=False)
    # Need to hold list of user_ids...
    # Many to many relationship with users

    def __repr__(self):
        return f"<Group {self.group_name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "group_name": self.group_name,
            "members": [user.to_dict() for user in self.members],
        }
    def is_member(self):
        # Checks if logged in user is a member of the group, used for authorisation on group routes
        return any(user.id == current_user.id for user in self.members)


# Association table for Many-Many relationship between User and Groups
user_group_association = db.Table(
    "user_group_association",
    db.Model.metadata,
    db.Column("user_id", db.ForeignKey("users.id"), primary_key=True),
    db.Column("group_id", db.ForeignKey("groups.id"), primary_key=True),
)

# Adds the relationships
User.groups = db.relationship(
    "Group", secondary=user_group_association, back_populates="members"
)
Group.members = db.relationship(
    "User", secondary=user_group_association, back_populates="groups"
)
