import unittest
from datetime import date, time

from app import create_app, db
from app.config import TestConfig
from app.models import Event, User

# Event creation...
class EventsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestConfig())
        self.app.config['WTF_CSRF_ENABLED'] = False # Disables CSRF during tests
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.populate_db()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        self.app = None
        self.app_context = None

    def populate_db(self):
        self.user = User(username='eventuser', email='eventuser@example.com')
        self.user.password = 'Password1!'
        self.other_user = User(username='otheruser', email='otheruser@example.com')
        self.other_user.password = 'Password1!'

        db.session.add(self.user)
        db.session.add(self.other_user)
        db.session.commit()

        self.event = Event(
            title='Existing event',
            description='Seeded event',
            date=date(2026, 5, 13),
            start_time=time(10, 0),
            end_time=time(11, 0),
            location='Room 101',
            color='indigo',
            user_id=self.user.id,
        )
        db.session.add(self.event)
        db.session.commit()

    def login_as(self, user):
        with self.client.session_transaction() as session:
            session['_user_id'] = str(user.id)
            session['_fresh'] = True

    def test_create_event(self):
        self.login_as(self.user)

        response = self.client.post('/api/events', json={
            'title': 'New event',
            'description': 'Created in test',
            'date': '2026-05-13',
            'start_time': '14:00',
            'end_time': '15:00',
            'location': 'Library',
            'color': 'emerald',
        })

        assert response.status_code == 201
        assert response.json['title'] == 'New event'
        assert response.json['user_id'] == self.user.id
        assert Event.query.filter_by(title='New event', user_id=self.user.id).first() is not None

    def test_fetch_current_user_events(self):
        self.login_as(self.user)

        response = self.client.get('/api/events/me?start=2026-05-13&end=2026-05-13')

        assert response.status_code == 200
        assert str(self.user.id) in response.json
        assert response.json[str(self.user.id)]['events']
        first_event = next(iter(response.json[str(self.user.id)]['events'].values()))
        assert first_event['title'] == 'Existing event'

    def test_fetch_all_events(self):
        self.login_as(self.user)

        response = self.client.get('/api/events/')

        assert response.status_code == 200
        assert str(self.user.id) in response.json
        assert str(self.event.id) in response.json[str(self.user.id)]['events']

    def test_update_event(self):
        self.login_as(self.user)

        response = self.client.put(f'/api/events/{self.event.id}', json={
            'title': 'Updated event',
            'description': 'Updated description',
            'date': '2026-05-14',
            'start_time': '16:00',
            'end_time': '17:00',
            'location': 'New room',
            'color': 'rose',
        })

        assert response.status_code == 200
        assert response.json['title'] == 'Updated event'
        updated = Event.query.get(self.event.id)
        assert updated.title == 'Updated event'
        assert updated.location == 'New room'

    def test_delete_event(self):
        self.login_as(self.user)

        response = self.client.delete(f'/api/events/{self.event.id}')

        assert response.status_code == 200
        assert response.json['message'] == 'Event deleted'
        assert Event.query.get(self.event.id) is None