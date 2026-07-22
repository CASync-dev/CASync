import unittest
from unittest.mock import patch

from app import create_app, db
from app.config import TestConfig
from app.models import User, Event, Calendar
from services.ical import import_ical, fetch_ical_events, IcalFeedError

SAMPLE_V1 = "https://raw.githubusercontent.com/LVaclav/test-icals/refs/heads/main/cal-v1.ics"
SAMPLE_V2 = "https://raw.githubusercontent.com/LVaclav/test-icals/refs/heads/main/cal-v2.ics"


class _FakeResponse:
    """
    Minimal stand-in for a streamed `requests` response, so the iCal fetch/error
    tests don't touch the network. Mimics the context-manager + iter_content API
    that fetch_ical_events uses.
    """

    def __init__(self, chunks=()):
        self._chunks = list(chunks)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size=65536):
        yield from self._chunks

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

    def test_import_another_ical(self):
        # Importing a second, different calendar should work and create events from that calendar without affecting the first one
        self.client.post('/api/import-ical/', json={"url": SAMPLE_V1})
        count_after_first = Event.query.count()
        response = self.client.post('/api/import-ical/', json={"url": SAMPLE_V2})
        assert response.status_code == 200
        data = response.get_json()
        assert 'imported' in data
        assert data["imported"] > 0
    
    def test_sync_multiple_calendars(self):
        # Syncing when the user has multiple calendars should sync all of them and aggregate the results correctly
        self.client.post('/api/import-ical/', json={"url": SAMPLE_V1})
        self.client.post('/api/import-ical/', json={"url": SAMPLE_V2})
        response = self.client.post('/api/sync-cal/')
        assert response.status_code == 200
        data = response.get_json()
        assert data["created"] >= 0
        assert data["updated"] >= 0
    
    def test_delete_one_calendar_does_not_affect_others(self):
        # Deleting one calendar when multiple exist should only delete events from that calendar and not affect the others
        self.client.post('/api/import-ical/', json={"url": SAMPLE_V1})
        self.client.post('/api/import-ical/', json={"url": SAMPLE_V2})
        cal_to_delete = Calendar.query.filter_by(ical_url=SAMPLE_V1).first()
        response = self.client.post('/api/remove-cal/', json={"id": cal_to_delete.id})
        assert response.status_code == 200
        remaining_cal = Calendar.query.filter_by(ical_url=SAMPLE_V2).first()
        assert remaining_cal is not None
        assert Event.query.filter_by(ical_id=remaining_cal.id).count() > 0

    # -- empty / unusable feed error handling --

    def test_fetch_empty_feed_raises_ical_feed_error(self):
        # A 200 response with no body must raise IcalFeedError, not fall through
        # to the opaque icalendar parser error.
        with patch('services.ical.requests.get', return_value=_FakeResponse([])):
            with self.assertRaises(IcalFeedError) as ctx:
                fetch_ical_events('https://example.com/empty.ics')
        assert 'empty' in str(ctx.exception).lower()

    def test_fetch_whitespace_only_feed_raises(self):
        # Whitespace-only bodies are just as unusable as truly empty ones.
        with patch('services.ical.requests.get', return_value=_FakeResponse([b'  \r\n\t '])):
            with self.assertRaises(IcalFeedError):
                fetch_ical_events('https://example.com/blank.ics')

    def test_import_empty_feed_returns_friendly_error(self):
        # import_ical should surface the clear message, NOT the raw parser text.
        user_id = User.query.filter_by(username='gerald').first().id
        with patch('services.ical.validate_url', return_value=None), \
             patch('services.ical.requests.get', return_value=_FakeResponse([])):
            result, error = import_ical('https://example.com/empty.ics', user_id)
        assert result is None
        assert error is not None
        assert 'empty' in error.lower()
        # Must not leak the internal parser error or the generic parse prefix.
        assert 'Found no components' not in error
        assert 'could not parse' not in error.lower()

    def test_import_endpoint_empty_feed_returns_400(self):
        # End-to-end through the API route, network mocked.
        with patch('services.ical.validate_url', return_value=None), \
             patch('services.ical.requests.get', return_value=_FakeResponse([])):
            response = self.client.post('/api/import-ical/', json={"url": "https://example.com/empty.ics"})
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'empty' in data['error'].lower()

    def test_import_malformed_feed_still_reports_parse_error(self):
        # Non-empty but junk content should still hit the generic parse branch,
        # confirming we didn't swallow real parse failures.
        with patch('services.ical.validate_url', return_value=None), \
             patch('services.ical.requests.get', return_value=_FakeResponse([b'this is not ical'])):
            user_id = User.query.filter_by(username='gerald').first().id
            result, error = import_ical('https://example.com/junk.ics', user_id)
        assert result is None
        assert error is not None
        assert 'parse' in error.lower()