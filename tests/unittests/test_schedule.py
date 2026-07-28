import unittest
from datetime import datetime
from unittest.mock import patch

from app import create_app, db
from app.config import TestConfig
from app.models import User

# The schedule page pre-fills the "Starts"/"Ends" inputs from the current time.
# It used to do that with datetime.replace(hour=now.hour+1, minute=now.minute+1),
# which raised ValueError whenever a component overflowed (issue #166: any XX:59).
class ScheduleTimeTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestConfig())
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.populate_db()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()
        self.app = None
        self.app_context = None

    def populate_db(self):
        self.user = User(username='scheduleuser', email='scheduleuser@example.com')
        self.user.password = 'Password1!'
        db.session.add(self.user)
        db.session.commit()

    def login_as(self, user):
        with self.client.session_transaction() as session:
            session['_user_id'] = str(user.id)
            session['_fresh'] = True

    def get_schedule_at(self, frozen_now):
        self.login_as(self.user)
        # loggedin.py calls datetime.now(), so patch datetime in that module only.
        with patch('app.loggedin.loggedin.datetime') as mock_datetime:
            mock_datetime.now.return_value = frozen_now
            response = self.client.get('/schedule')
        assert response.status_code == 200
        return response.get_data(as_text=True)

    def assert_defaults(self, frozen_now, expected_start, expected_end):
        html = self.get_schedule_at(frozen_now)
        assert f'value="{expected_start}"' in html, f'missing start {expected_start} for {frozen_now}'
        assert f'value="{expected_end}"' in html, f'missing end {expected_end} for {frozen_now}'

    # The original report: minute 59 pushed minute to 60.
    def test_minute_rollover(self):
        self.assert_defaults(
            datetime(2026, 5, 13, 10, 59),
            '2026-05-13T10:59',
            '2026-05-13T12:00',
        )

    # Reported as also failing at 11:59am, i.e. it was never about am/pm.
    def test_minute_rollover_before_noon(self):
        self.assert_defaults(
            datetime(2026, 5, 13, 11, 59),
            '2026-05-13T11:59',
            '2026-05-13T13:00',
        )

    # 23:xx used to be special-cased; make sure the shared path still handles it.
    def test_hour_rollover_into_next_day(self):
        self.assert_defaults(
            datetime(2026, 5, 13, 23, 30),
            '2026-05-13T23:30',
            '2026-05-14T00:31',
        )

    # Both hour and minute overflow at once.
    def test_hour_and_minute_rollover_into_next_day(self):
        self.assert_defaults(
            datetime(2026, 5, 13, 23, 59),
            '2026-05-13T23:59',
            '2026-05-14T01:00',
        )

    def test_rollover_into_next_month(self):
        self.assert_defaults(
            datetime(2026, 4, 30, 23, 59),
            '2026-04-30T23:59',
            '2026-05-01T01:00',
        )

    def test_rollover_into_next_year(self):
        self.assert_defaults(
            datetime(2026, 12, 31, 23, 59),
            '2026-12-31T23:59',
            '2027-01-01T01:00',
        )

    # 28 February on a non-leap year rolls to 1 March...
    def test_rollover_end_of_february_non_leap_year(self):
        self.assert_defaults(
            datetime(2026, 2, 28, 23, 59),
            '2026-02-28T23:59',
            '2026-03-01T01:00',
        )

    # ...but on a leap year it rolls to 29 February.
    def test_rollover_end_of_february_leap_year(self):
        self.assert_defaults(
            datetime(2028, 2, 28, 23, 59),
            '2028-02-28T23:59',
            '2028-02-29T01:00',
        )

    def test_rollover_from_leap_day(self):
        self.assert_defaults(
            datetime(2028, 2, 29, 23, 59),
            '2028-02-29T23:59',
            '2028-03-01T01:00',
        )

    def test_midnight_does_not_roll_over(self):
        self.assert_defaults(
            datetime(2026, 5, 13, 0, 0),
            '2026-05-13T00:00',
            '2026-05-13T01:01',
        )

    # Seconds are dropped by the %H:%M format, so they must not affect the values.
    def test_seconds_are_truncated(self):
        self.assert_defaults(
            datetime(2026, 5, 13, 10, 59, 59, 999999),
            '2026-05-13T10:59',
            '2026-05-13T12:00',
        )

    # Sweep every minute of the day: nothing should raise, whatever the clock says.
    def test_every_minute_of_the_day_renders(self):
        for hour in range(24):
            for minute in range(60):
                with self.subTest(hour=hour, minute=minute):
                    html = self.get_schedule_at(datetime(2026, 5, 13, hour, minute))
                    assert 'id="event-end"' in html


if __name__ == '__main__':
    unittest.main()
