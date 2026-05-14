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
        updated = db.session.get(Event, self.event.id)
        assert updated.title == 'Updated event'
        assert updated.location == 'New room'

    def test_delete_event(self):
        self.login_as(self.user)

        response = self.client.delete(f'/api/events/{self.event.id}')

        assert response.status_code == 200
        assert response.json['message'] == 'Event deleted'
        assert db.session.get(Event, self.event.id) is None

# ----------------------- create event edge cases -----------------------
    def test_create_event_missing_fields(self):
        self.login_as(self.user)

        response = self.client.post('/api/events', json={
            'title': '',
            'description': 'Created in test',
            'date': '2026-05-13',
            'start_time': '14:00',
            'end_time': '15:00',
            'location': 'Library',
            'color': 'emerald',
        })

        assert response.status_code == 400
        assert 'Please fill in all required fields.' in response.json['error']
    
    

        response = self.client.post('/api/events', json={
            'title': 'new event',
            'description': 'Created in test',
            'date': '',
            'start_time': '14:00',
            'end_time': '15:00',
            'location': 'Library',
            'color': 'emerald',
        })

        assert response.status_code == 400
        assert 'Please fill in all required fields.' in response.json['error']

        response = self.client.post('/api/events', json={
            'title': 'new event',
            'description': 'Created in test',
            'date': '2026-05-13',
            'start_time': '',
            'end_time': '15:00',
            'location': 'Library',
            'color': 'emerald',
        })

        assert response.status_code == 400
        assert 'Please fill in all required fields.' in response.json['error']

        response = self.client.post('/api/events', json={
            'title': 'new event',
            'description': 'Created in test',
            'date': '2026-05-13',
            'start_time': '14:00',
            'end_time': '',
            'location': 'Library',
            'color': 'emerald',
        })

        assert response.status_code == 400
        assert 'Please fill in all required fields.' in response.json['error']

    def test_create_event_end_time_before_start_time(self):
        self.login_as(self.user)

        response = self.client.post('/api/events', json={
            'title': 'new event',
            'description': 'Created in test',
            'date': '2026-05-13',
            'start_time': '15:00',
            'end_time': '14:00',
            'location': 'Library',
            'color': 'emerald',
        })

        assert response.status_code == 400
        assert 'End time must be after start time.' in response.json['error']

# ----------------------- delete event edge cases -----------------------

    def test_delete_event_not_found(self):
        self.login_as(self.user)

        response = self.client.delete(f'/api/events/{99999999}')

        assert response.status_code == 404
        assert response.json['error'] == 'Event not found'
        assert db.session.get(Event, self.event.id).title == 'Existing event'

    def test_delete_event_unauthorized(self):
        self.login_as(self.other_user)  # login as the OTHER user
        
        # try to delete self.event which belongs to self.user
        response = self.client.delete(f'/api/events/{self.event.id}')
        
        assert response.status_code == 403
        assert response.json['error'] == 'Unauthorized'
        assert db.session.get(Event, self.event.id) is not None  # event still exists

    
    def test_delete_imported_event(self):
        self.login_as(self.user)

        imported_event = Event(
            title='Imported event',
            description='Seeded imported event',
            date=date(2026, 5, 13),
            start_time=time(12, 0),
            end_time=time(13, 0),
            location='Room 202',
            color='blue',
            user_id=self.user.id,
            ical_id=1,
        )
        db.session.add(imported_event)
        db.session.commit()

        response = self.client.delete(f'/api/events/{imported_event.id}')

        assert response.status_code == 400
        assert response.json['error'] == 'Cannot delete imported events'
        assert db.session.get(Event, imported_event.id) is not None

# ----------------------- update event edge cases -----------------------

    def test_update_event_not_found(self):
        self.login_as(self.user)

        response = self.client.put(f'/api/events/{99999999}', json={
            'title': 'Updated event',
            'description': 'Updated description',
            'date': '2026-05-14',
            'start_time': '16:00',
            'end_time': '17:00',
            'location': 'New room',
            'color': 'rose',
        })

        assert response.status_code == 404
        assert response.json['error'] == 'Event not found'
        assert db.session.get(Event, self.event.id).title == 'Existing event'  # event not updated

    # test updating an event that belongs to another user (should be unauthorized)
    def test_update_event_unauthorized(self):
        self.login_as(self.other_user)

        response = self.client.put(f'/api/events/{self.event.id}', json={
            'title': 'Malicious update',
            'description': 'should not work',
            'date': '2026-05-14',
            'start_time': '09:00',
            'end_time': '10:00',
            'location': 'Nowhere',
            'color': 'rose',
        })

        assert response.status_code == 403
        assert response.json['error'] == 'Unauthorized'
        assert db.session.get(Event, self.event.id).title == 'Existing event'

    # test updating an imported event form ical (should not be allowed)
    def test_update_imported_event(self):
        self.login_as(self.user)
        imported = Event(
            title='Imported edit',
            description='ical imported',
            date=date(2026, 5, 13),
            start_time=time(12, 0),
            end_time=time(13, 0),
            location='Room 2',
            color='blue',
            user_id=self.user.id,
            ical_id=77,
        )
        db.session.add(imported)
        db.session.commit()

        response = self.client.put(f'/api/events/{imported.id}', json={
            'title': 'Attempt edit imported',
            'date': '2026-05-13',
            'start_time': '12:00',
            'end_time': '13:00'
        })
        assert response.status_code == 400
        assert response.json['error'] == 'Cannot edit imported events'


    def test_update_event_missing_fields(self):
        self.login_as(self.user)

        response = self.client.put(f'/api/events/{self.event.id}', json={
            'title': '',
            'description': 'Updated in test',
            'date': '2026-05-13',
            'start_time': '14:00',
            'end_time': '15:00',
            'location': 'Library',
            'color': 'emerald',
        })

        assert response.status_code == 400
        assert 'Please fill in all required fields.' in response.json['error']
    
    

        response = self.client.put(f'/api/events/{self.event.id}', json={
            'title': 'new event',
            'description': 'Updated in test',
            'date': '',
            'start_time': '14:00',
            'end_time': '15:00',
            'location': 'Library',
            'color': 'emerald',
        })

        assert response.status_code == 400
        assert 'Please fill in all required fields.' in response.json['error']

        response = self.client.put(f'/api/events/{self.event.id}', json={
            'title': 'new event',
            'description': 'Updated in test',
            'date': '2026-05-13',
            'start_time': '',
            'end_time': '15:00',
            'location': 'Library',
            'color': 'emerald',
        })

        assert response.status_code == 400
        assert 'Please fill in all required fields.' in response.json['error']

        response = self.client.put(f'/api/events/{self.event.id}', json={
            'title': 'new event',
            'description': 'Updated in test',
            'date': '2026-05-13',
            'start_time': '14:00',
            'end_time': '',
            'location': 'Library',
            'color': 'emerald',
        })

        assert response.status_code == 400
        assert 'Please fill in all required fields.' in response.json['error']

    def test_update_event_end_time_before_start_time(self):
        self.login_as(self.user)

        response = self.client.put(f'/api/events/{self.event.id}', json={
            'title': 'Updated event',
            'description': 'Updated in test',
            'date': '2026-05-13',
            'start_time': '15:00',
            'end_time': '14:00',
            'location': 'Library',
            'color': 'emerald',
        })

        assert response.status_code == 400
        assert 'End time must be after start time.' in response.json['error']



# ----------------------- going/not going to event edge cases -----------------------


    def test_toggle_going_not_found(self):
        self.login_as(self.user)
        response = self.client.post('/api/events/99999999/toggle_going')
        assert response.status_code == 404
        assert response.json['error'] == 'Event not found'

    def test_toggle_going_unauthorized(self):
        self.login_as(self.other_user)
        response = self.client.post(f'/api/events/{self.event.id}/toggle_going')
        assert response.status_code == 403
        assert response.json['error'] == 'Unauthorized'

# ----------------------- events/me edge cases -----------------------

    def test_api_events_me_missing_params(self):
        self.login_as(self.user)
        response = self.client.get('/api/events/me')
        assert response.status_code == 400
        assert response.json['error'] == 'Missing start or end date'

    def test_api_events_me_invalid_date(self):
        self.login_as(self.user)
        response = self.client.get('/api/events/me?start=2026-99-99&end=2026-05-13')
        assert response.status_code == 400
        assert 'Invalid date format' in response.json['error']


# ----------------------- /api/events/<int:user_id> edge cases -----------------------

    def test_api_user_events_missing_params(self):
        self.login_as(self.user)
        response = self.client.get(f'/api/events/{self.user.id}')
        assert response.status_code == 400
        assert response.json['error'] == 'Missing start or end date'

    def test_api_user_events_invalid_date(self):
        self.login_as(self.user)
        response = self.client.get(f'/api/events/{self.user.id}?start=bad&end=also')
        assert response.status_code == 400
        assert 'Invalid date format' in response.json['error']