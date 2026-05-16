import unittest
from app import create_app, db
from app.config import TestConfig
from app.models import User, Event, Calendar

SAMPLE_V1 = "https://raw.githubusercontent.com/LVaclav/test-icals/refs/heads/main/cal-v1.ics"
SAMPLE_V2 = "https://raw.githubusercontent.com/LVaclav/test-icals/refs/heads/main/cal-v2.ics"

class CalTestCases(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestConfig())
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        #add a test user
        user = User(username='gerald', email='sekai@hotmail.com')
        user.password = 'foo'
        db.session.add(user)
        db.session.commit()
        self.client = self.app.test_client()
        #login
        self.client.post('/login', data={'username': 'gerald', 'password': 'foo'})

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        
        # closes all SQLite connections (added due to ResourceWarning: unclosed database...)
        db.engine.dispose()

        self.app_context.pop()
        self.app = None
        self.app_context = None

    # -- import-ical --

    def test_import_rejects_empty_url(self):
        response = self.client.post('/api/import-ical/', json={"url": ""})
        assert response.status_code == 400
        assert "error" in response.get_json()

    def test_import_rejects_invalid_url(self):
        response = self.client.post('/api/import-ical/', json={"url": "not a url"})
        assert response.status_code == 400
        assert "error" in response.get_json()

    def test_import_creates_events(self):
        # A valid ical feed should succeed and persist events to the db
        response = self.client.post('/api/import-ical/', json={"url": SAMPLE_V1})
        assert response.status_code == 200
        data = response.get_json()
        assert "imported" in data
        assert data["imported"] > 0
        assert Event.query.count() > 0

    def test_reimport_no_duplicates(self):
        # Importing the same calendar again should not create duplicate events
        self.client.post('/api/import-ical/', json={"url": SAMPLE_V1})
        count_after_first = Event.query.count()
        response = self.client.post('/api/import-ical/', json={"url": SAMPLE_V1})
        assert response.status_code == 200
        data = response.get_json()
        assert data["created"] == 0
        assert Event.query.count() == count_after_first

    def test_import_updates_changed_events(self):
        # Importing a newer version of the same calendar should create new events and update changed ones
        # cal-v2 has one new event and one modified event compared to cal-v1
        self.client.post('/api/import-ical/', json={"url": SAMPLE_V1})
        cal = Calendar.query.first()
        cal.ical_url = SAMPLE_V2
        db.session.commit()
        response = self.client.post('/api/import-ical/', json={"url": SAMPLE_V2})
        assert response.status_code == 200
        data = response.get_json()
        assert data["created"] == 1  # one new event in v2
        assert data["updated"] == 1  # one event changed in v2

    # -- remove-cal --

    def test_remove_cal_deletes_events(self):
        # Deleting a calendar should also delete all its associated events
        self.client.post('/api/import-ical/', json={"url": SAMPLE_V1})
        cal = Calendar.query.first()
        response = self.client.post('/api/remove-cal/', json={"id": cal.id})
        assert response.status_code == 200
        assert Calendar.query.first() is None
        assert Event.query.count() == 0

    # -- sync-cal --

    def test_sync_with_no_calendars(self):
        # Syncing with no calendars should succeed but do nothing
        response = self.client.post('/api/sync-cal/')
        assert response.status_code == 200
        data = response.get_json()
        assert data["created"] == 0
        assert data["updated"] == 0

    def test_sync_no_duplicates(self):
        # Syncing a calendar that hasn't changed should not create or update anything
        self.client.post('/api/import-ical/', json={"url": SAMPLE_V1})
        response = self.client.post('/api/sync-cal/')
        assert response.status_code == 200
        data = response.get_json()
        assert data["created"] == 0
        assert data["updated"] == 0

    def test_sync_picks_up_changes(self):
        # Syncing after the calendar URL changes to a newer version should reflect those changes
        self.client.post('/api/import-ical/', json={"url": SAMPLE_V1})
        cal = Calendar.query.first()
        cal.ical_url = SAMPLE_V2
        db.session.commit()
        response = self.client.post('/api/sync-cal/')
        assert response.status_code == 200
        data = response.get_json()
        assert data["created"] == 1
        assert data["updated"] == 1