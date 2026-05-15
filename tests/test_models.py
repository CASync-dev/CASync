import os
from datetime import datetime, timezone

os.environ.setdefault("SECRET_KEY", "test-secret")

from app import app, db
from app.models import Event, User


def setup_function():
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
    )
    app.app_context().push()
    db.create_all()


def teardown_function():
    db.session.remove()
    db.drop_all()


def test_password_hashing_and_verification():
    user = User(username="tester", email="tester@example.com")
    user.password = "correct horse battery staple"

    assert user.password_hash != "correct horse battery staple"
    assert user.verify_password("correct horse battery staple")
    assert not user.verify_password("wrong password")


def test_event_to_dict_marks_naive_datetimes_as_utc():
    user = User(username="owner", email="owner@example.com")
    db.session.add(user)
    db.session.commit()

    event = Event(
        title="Tutorial",
        start_time=datetime(2026, 5, 1, 9, 0),
        end_time=datetime(2026, 5, 1, 10, 0, tzinfo=timezone.utc),
        user_id=user.id,
    )
    db.session.add(event)
    db.session.commit()

    data = event.to_dict()

    assert data["title"] == "Tutorial"
    assert data["username"] == "owner"
    assert data["startTime"] == "2026-05-01T09:00:00+00:00"
    assert data["endTime"] == "2026-05-01T10:00:00+00:00"
