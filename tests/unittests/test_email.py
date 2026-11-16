import unittest

from app import create_app, db
from app.config import TestConfig
from app.models import User
from services import email


# Tests the email service. RESEND_API_KEY is never set in the test environment,
# so send_email always takes the no-key path: it logs the message to the console
# and returns True without making any network call. setUp pins the key to None
# so a developer's local .env can't change that.
class EmailTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestConfig())
        self.app.config['RESEND_API_KEY'] = None
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.user = User(username='gerald', email='sekai@hotmail.com')
        self.user.password = 'foo'
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

        # closes all SQLite connections (added due to ResourceWarning: unclosed database...)
        db.engine.dispose()

        self.app_context.pop()
        self.app = None
        self.app_context = None

    # --- send_email -------------------------------------------------------

    def test_send_email_without_key_returns_true(self):
        # No key -> logs instead of sending, reports success so the flow continues.
        self.assertTrue(email.send_email('to@x.com', 'Subj', '<p>hi</p>', 'hi'))

    # --- link building ----------------------------------------------------

    def test_link_joins_base_url_path_and_token(self):
        self.app.config['APP_BASE_URL'] = 'https://casync.dev'
        self.assertEqual(
            email._link(email._CONFIRM_PATH, 'TOK'),
            'https://casync.dev/confirm/TOK',
        )

    def test_link_strips_trailing_slash_on_base_url(self):
        # A trailing slash on APP_BASE_URL must not produce a double slash.
        self.app.config['APP_BASE_URL'] = 'https://casync.dev/'
        self.assertEqual(
            email._link(email._RESET_PATH, 'TOK'),
            'https://casync.dev/reset-password/TOK',
        )

    # --- confirm / reset helpers -----------------------------------------

    def test_send_confirmation_email_returns_true(self):
        self.assertTrue(email.send_confirmation_email(self.user))

    def test_send_password_reset_email_returns_true(self):
        self.assertTrue(email.send_password_reset_email(self.user))

    def test_confirmation_email_renders_link_and_username(self):
        # Capture what the helper hands to send_email so we can inspect the
        # rendered templates without sending anything.
        captured = {}

        def fake_send(to, subject, html, text):
            captured.update(to=to, subject=subject, html=html, text=text)
            return True

        self.app.config['APP_BASE_URL'] = 'https://casync.dev'
        original = email.send_email
        email.send_email = fake_send
        try:
            self.assertTrue(email.send_confirmation_email(self.user))
        finally:
            email.send_email = original

        self.assertEqual(captured['to'], self.user.email)
        self.assertIn('Confirm', captured['subject'])
        # Both bodies must carry a confirmation link and the username.
        self.assertIn('https://casync.dev/confirm/', captured['html'])
        self.assertIn('https://casync.dev/confirm/', captured['text'])
        self.assertIn(self.user.username, captured['text'])

    def test_reset_email_renders_link_and_username(self):
        captured = {}

        def fake_send(to, subject, html, text):
            captured.update(to=to, subject=subject, html=html, text=text)
            return True

        self.app.config['APP_BASE_URL'] = 'https://casync.dev'
        original = email.send_email
        email.send_email = fake_send
        try:
            self.assertTrue(email.send_password_reset_email(self.user))
        finally:
            email.send_email = original

        self.assertEqual(captured['to'], self.user.email)
        self.assertIn('Reset', captured['subject'])
        self.assertIn('https://casync.dev/reset-password/', captured['html'])
        self.assertIn('https://casync.dev/reset-password/', captured['text'])
        self.assertIn(self.user.username, captured['text'])


if __name__ == '__main__':
    unittest.main()
