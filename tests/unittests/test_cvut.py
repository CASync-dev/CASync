import unittest
from unittest.mock import patch

from icalendar import Calendar as ICalendar

from app import create_app, db
from app.config import TestConfig
from app.models import User, Event, Calendar
from services.ical import (
    import_ical,
    parse_ical_event,
    detect_source,
    _cvut_course_code,
    _color_for_course,
)

# Minimal CVUT (SIRIUS) feed: Europe/Prague VTIMEZONE + two VEVENTs, each with a
# course-code CATEGORIES and an activity-type CATEGORIES, mirroring the real feed.
CVUT_ICS = """BEGIN:VCALENDAR\r
VERSION:2.0\r
PRODID:icalendar-ruby\r
CALSCALE:GREGORIAN\r
BEGIN:VTIMEZONE\r
TZID:Europe/Prague\r
BEGIN:DAYLIGHT\r
DTSTART:20140330T030000\r
TZOFFSETFROM:+0100\r
TZOFFSETTO:+0200\r
RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=3\r
TZNAME:CEST\r
END:DAYLIGHT\r
BEGIN:STANDARD\r
DTSTART:20131027T020000\r
TZOFFSETFROM:+0200\r
TZOFFSETTO:+0100\r
RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=10\r
TZNAME:CET\r
END:STANDARD\r
END:VTIMEZONE\r
BEGIN:VEVENT\r
UID:3675569872@sirius.fit.cvut.cz\r
DTSTART;TZID=Europe/Prague:20260921T091500\r
DTEND;TZID=Europe/Prague:20260921T104500\r
DESCRIPTION:Architectures of Computer Systems\r
LOCATION:JP:B-570\r
SUMMARY:BIE-APS.21 1. přednáška (1)\r
CATEGORIES:BIE-APS.21\r
CATEGORIES:přednáška\r
END:VEVENT\r
BEGIN:VEVENT\r
UID:3675568386@sirius.fit.cvut.cz\r
DTSTART;TZID=Europe/Prague:20260921T161500\r
DTEND;TZID=Europe/Prague:20260921T193000\r
DESCRIPTION:Czech Language for Foreigners II\r
LOCATION:T9:302\r
SUMMARY:BIE-CZ1.21 1. cvičení (101)\r
CATEGORIES:BIE-CZ1.21\r
CATEGORIES:cvičení\r
END:VEVENT\r
END:VCALENDAR\r
""".encode("utf-8")

CVUT_URL = "https://sirius.fit.cvut.cz/api/v1/people/cervelia/events.ical?access_token=test-token"


class _FakeResponse:
    """Streamed-requests stand-in, mirroring test_ical.py's fake."""

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


class ProviderDetectionTests(unittest.TestCase):
    def test_detect_cvut(self):
        assert detect_source(CVUT_URL) == "cvut"

    def test_detect_uwa(self):
        url = "https://apps.cas.uwa.edu.au/even/rest/calendar/ical/abc-123"
        assert detect_source(url) == "uwa"

    def test_detect_generic(self):
        assert detect_source("https://example.com/calendar.ics") == "generic"

    def test_detect_subdomain_matches_suffix(self):
        # a subdomain of cvut.cz should still be treated as CVUT
        assert detect_source("https://other.fit.cvut.cz/cal.ics") == "cvut"


class CvutParsingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cal = ICalendar.from_ical(CVUT_ICS)
        cls.events = [c for c in cal.walk() if c.name == "VEVENT"]

    def test_course_code_from_categories(self):
        # the category containing a digit is the course code, not the activity type
        assert _cvut_course_code(self.events[0]) == "BIE-APS.21"
        assert _cvut_course_code(self.events[1]) == "BIE-CZ1.21"

    def test_color_is_stable_per_course(self):
        assert _color_for_course("BIE-APS.21") == _color_for_course("BIE-APS.21")

    def test_parse_cvut_event_maps_fields_and_color(self):
        parsed = parse_ical_event(self.events[0], user_id=1, cal_id=1, source="cvut")
        assert parsed["title"].startswith("BIE-APS.21")
        assert parsed["description"] == "Architectures of Computer Systems"
        assert parsed["location"] == "JP:B-570"
        assert parsed["color"] == _color_for_course("BIE-APS.21")
        # Prague is UTC+2 in late September: 09:15 -> 07:15 UTC.
        assert parsed["start_time"].isoformat() == "2026-09-21T07:15:00+00:00"

    def test_parse_generic_event_has_no_color(self):
        parsed = parse_ical_event(self.events[0], user_id=1, cal_id=1, source="generic")
        assert "color" not in parsed or parsed.get("color") is None


class CvutImportTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestConfig())
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        user = User(username="cvut-user", email="cvut@example.com")
        user.password = "foo"
        user.email_confirmed = True
        db.session.add(user)
        db.session.commit()
        self.user_id = user.id

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()

    def test_import_cvut_stores_source_and_colors(self):
        with patch("services.ical.validate_url", return_value=None), \
             patch("services.ical.requests.get", return_value=_FakeResponse([CVUT_ICS])):
            result, error = import_ical(CVUT_URL, self.user_id)

        assert error is None
        assert result == {"imported": 2}
        cal = Calendar.query.filter_by(user_id=self.user_id).one()
        assert cal.source == "cvut"

        events = Event.query.order_by(Event.id).all()
        assert len(events) == 2
        # Same course -> same colour; different course -> (possibly) different.
        assert events[0].color == _color_for_course("BIE-APS.21")
        assert events[1].color == _color_for_course("BIE-CZ1.21")
        assert events[0].description == "Architectures of Computer Systems"

    def test_import_generic_does_not_set_color(self):
        url = "https://example.com/calendar.ics"
        with patch("services.ical.validate_url", return_value=None), \
             patch("services.ical.requests.get", return_value=_FakeResponse([CVUT_ICS])):
            result, error = import_ical(url, self.user_id)

        assert error is None
        cal = Calendar.query.filter_by(user_id=self.user_id).one()
        assert cal.source == "generic"
        assert Event.query.first().color is None
