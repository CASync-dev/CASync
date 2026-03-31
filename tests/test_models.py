from app import create_app
from models import User, Calendar, Event
from extensions import db
from datetime import date, time
import unittest

app = create_app('testing')

class ModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # User 

    def test_user_creation(self):
        # Create a user and verify it was saved correctly
        user = User(username='testuser', email='test@example.com')
        db.session.add(user)
        db.session.commit()
        self.assertEqual(User.query.count(), 1)
        fetched = User.query.first()
        # Verify the fields were saved correctly
        self.assertEqual(fetched.username, 'testuser')
        self.assertEqual(fetched.email, 'test@example.com')
        self.assertIsNotNone(fetched.created_at)

    def test_user_unique_username(self):
        # Attempt to create two users with the same username should raise an exception
        db.session.add(User(username='dupe', email='a@example.com'))
        db.session.add(User(username='dupe', email='b@example.com'))
        with self.assertRaises(Exception):
            db.session.commit()

    def test_user_unique_email(self):
        # Attempt to create two users with the same email should raise an exception
        db.session.add(User(username='user1', email='same@example.com'))
        db.session.add(User(username='user2', email='same@example.com'))
        with self.assertRaises(Exception):
            db.session.commit()

    # Calendar

    def test_calendar_creation(self):
        # Create a user and a calendar, then verify the calendar was saved correctly
        user = User(username='testuser', email='test@example.com')
        db.session.add(user)
        db.session.commit()
        calendar = Calendar(user_id=user.id, ical_url='https://example.com/feed.ics')
        db.session.add(calendar)
        db.session.commit()
        self.assertEqual(Calendar.query.count(), 1)
        fetched = Calendar.query.first()
        self.assertEqual(fetched.user_id, user.id)
        self.assertEqual(fetched.ical_url, 'https://example.com/feed.ics')
        self.assertIsNotNone(fetched.synced_at)

    # Event

    def _make_user(self):
        # Helper method to create a user for testing
        user = User(username='testuser', email='test@example.com')
        db.session.add(user)
        db.session.commit()
        return user

    def _make_calendar(self, user):
        # Helper method to create a calendar for testing
        calendar = Calendar(user_id=user.id, ical_url='https://example.com/feed.ics')
        db.session.add(calendar)
        db.session.commit()
        return calendar

    def test_event_creation(self):
        # Create a user, calendar, and event, then verify the event was saved correctly
        user = self._make_user()
        calendar = self._make_calendar(user)
        event = Event(
            user_id=user.id,
            title='Team Meeting',
            date=date(2024, 6, 1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            ical_uid='uid-abc-123',
            ical_id=calendar.id,
        )
        db.session.add(event)
        db.session.commit()
        self.assertEqual(Event.query.count(), 1)
        fetched = Event.query.first()
        self.assertEqual(fetched.title, 'Team Meeting')
        self.assertEqual(fetched.user_id, user.id)
        self.assertEqual(fetched.ical_id, calendar.id)

    def test_event_optional_fields_default(self):
        # Create an event without optional fields and verify defaults are set correctly
        user = self._make_user()
        # Create an event without location and color
        event = Event(
            user_id=user.id,
            title='No Frills',
            date=date(2024, 6, 1),
            start_time=time(9, 0),
            end_time=time(10, 0),
        )
        db.session.add(event)
        db.session.commit()
        fetched = Event.query.first()
        self.assertIsNone(fetched.location)
        self.assertEqual(fetched.color, 'indigo')

    def test_event_to_dict(self):
        # Create an event with all fields and verify the to_dict method returns the correct dictionary representation
        user = self._make_user()
        event = Event(
            user_id=user.id,
            title='Dict Test',
            date=date(2024, 6, 1),
            start_time=time(14, 30),
            end_time=time(15, 0),
            location='Room 4',
            color='red',
            ical_uid='uid-xyz',
        )
        db.session.add(event)
        db.session.commit()
        d = Event.query.first().to_dict()
        self.assertEqual(d['title'], 'Dict Test')
        self.assertEqual(d['date'], '2024-06-01')
        self.assertEqual(d['startTime'], '14:30')
        self.assertEqual(d['endTime'], '15:00')
        self.assertEqual(d['location'], 'Room 4')
        self.assertEqual(d['color'], 'red')
        self.assertEqual(d['ical_uid'], 'uid-xyz')
