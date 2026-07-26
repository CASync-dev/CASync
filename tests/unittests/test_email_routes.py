import unittest

from app import create_app, db
from app.config import TestConfig
from app.models import User
from app.loggedout import loggedout as loggedout_module
from services import tokens


# Route-level tests for the email-driven flows wired up in app/loggedout:
# registration confirmation, login gating, resend-confirmation, and the
# forgot-password / reset-password pair. The token and email service layers are
# covered separately (test_tokens.py, test_email.py); here we exercise the HTTP
# routes and their side effects.
class EmailRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestConfig())
        self.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF during tests
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # A confirmed account (can log in) and an unconfirmed one (cannot).
        self.confirmed = User(username='gerald', email='confirmed@example.com')
        self.confirmed.password = 'P@ssw01d'
        self.confirmed.email_confirmed = True

        self.unconfirmed = User(username='newbie', email='newbie@example.com')
        self.unconfirmed.password = 'P@ssw01d'
        self.unconfirmed.email_confirmed = False

        db.session.add_all([self.confirmed, self.unconfirmed])
        db.session.commit()

        self.client = self.app.test_client()

        # Capture outgoing emails instead of sending them. The routes import these
        # names into their own module namespace, so patch them there.
        self.sent = []
        self._orig_confirm = loggedout_module.send_confirmation_email
        self._orig_reset = loggedout_module.send_password_reset_email
        loggedout_module.send_confirmation_email = lambda user: self.sent.append(('confirm', user.email))
        loggedout_module.send_password_reset_email = lambda user: self.sent.append(('reset', user.email))

    def tearDown(self):
        loggedout_module.send_confirmation_email = self._orig_confirm
        loggedout_module.send_password_reset_email = self._orig_reset

        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()
        self.app = None
        self.app_context = None

    # --- login gating -----------------------------------------------------

    def test_login_blocked_until_confirmed(self):
        response = self.client.post('/login', data={
            'username': 'newbie', 'password': 'P@ssw01d',
        }, follow_redirects=True)
        self.assertEqual(response.request.path, '/login')
        self.assertIn('confirm your email', response.get_data(as_text=True).lower())

    def test_login_succeeds_when_confirmed(self):
        response = self.client.post('/login', data={
            'username': 'gerald', 'password': 'P@ssw01d',
        }, follow_redirects=True)
        self.assertEqual(response.request.path, '/dash')

    # --- registration sends a confirmation email --------------------------

    def test_register_sends_confirmation_and_lands_on_login(self):
        response = self.client.post('/register', data={
            'username': 'bob', 'email': 'bob@example.com',
            'password': 'P@ssw01d', 'repeat_password': 'P@ssw01d',
        }, follow_redirects=True)
        self.assertEqual(response.request.path, '/login')
        # New account is created unconfirmed and a confirm email is dispatched.
        user = User.query.filter_by(username='bob').first()
        self.assertIsNotNone(user)
        self.assertFalse(user.email_confirmed)
        self.assertIn(('confirm', 'bob@example.com'), self.sent)

    # --- confirm email ----------------------------------------------------

    def test_confirm_email_with_valid_token(self):
        token = tokens.make_confirm_token(self.unconfirmed)
        response = self.client.get(f'/confirm/{token}', follow_redirects=True)
        self.assertEqual(response.request.path, '/dash')  # auto-logged in
        self.assertTrue(db.session.get(User, self.unconfirmed.id).email_confirmed)

    def test_confirm_email_with_invalid_token(self):
        response = self.client.get('/confirm/not-a-real-token', follow_redirects=True)
        # A dead link lands on the page that can mint a fresh one, not the
        # dashboard (which would just bounce an anonymous visitor to login).
        self.assertEqual(response.request.path, '/resend_confirmation')
        self.assertIn('invalid or has expired', response.get_data(as_text=True).lower())
        # Nothing got confirmed.
        self.assertFalse(db.session.get(User, self.unconfirmed.id).email_confirmed)

    def test_confirm_email_already_confirmed(self):
        token = tokens.make_confirm_token(self.confirmed)
        response = self.client.get(f'/confirm/{token}', follow_redirects=True)
        self.assertEqual(response.request.path, '/login')
        self.assertIn('already confirmed', response.get_data(as_text=True).lower())

    # --- resend confirmation ----------------------------------------------

    def test_resend_confirmation_get_renders_form(self):
        response = self.client.get('/resend_confirmation')
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="email"', response.get_data(as_text=True))

    def test_resend_confirmation_for_unconfirmed_sends_email(self):
        response = self.client.post('/resend_confirmation', data={
            'email': 'newbie@example.com',
        }, follow_redirects=True)
        self.assertEqual(response.request.path, '/login')
        self.assertIn(('confirm', 'newbie@example.com'), self.sent)

    def test_resend_confirmation_for_confirmed_does_not_send(self):
        # Already-confirmed account: same generic response, but no email sent.
        response = self.client.post('/resend_confirmation', data={
            'email': 'confirmed@example.com',
        }, follow_redirects=True)
        self.assertEqual(response.request.path, '/login')
        self.assertEqual(self.sent, [])

    def test_resend_confirmation_for_unknown_email_does_not_send(self):
        response = self.client.post('/resend_confirmation', data={
            'email': 'nobody@example.com',
        }, follow_redirects=True)
        self.assertEqual(response.request.path, '/login')
        self.assertEqual(self.sent, [])

    # --- forgot password --------------------------------------------------

    def test_forgot_password_get_renders_form(self):
        response = self.client.get('/forgot_password')
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="email"', response.get_data(as_text=True))

    def test_forgot_password_known_email_sends_reset(self):
        response = self.client.post('/forgot_password', data={
            'email': 'confirmed@example.com',
        }, follow_redirects=True)
        self.assertEqual(response.request.path, '/login')
        self.assertIn(('reset', 'confirmed@example.com'), self.sent)

    def test_forgot_password_unknown_email_does_not_send(self):
        response = self.client.post('/forgot_password', data={
            'email': 'nobody@example.com',
        }, follow_redirects=True)
        self.assertEqual(response.request.path, '/login')
        self.assertEqual(self.sent, [])

    # --- reset password ---------------------------------------------------

    def test_reset_password_get_with_valid_token_renders_form(self):
        token = tokens.make_reset_token(self.confirmed)
        response = self.client.get(f'/reset-password/{token}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('name="new_password"', response.get_data(as_text=True))

    def test_reset_password_get_with_invalid_token_redirects(self):
        response = self.client.get('/reset-password/not-a-real-token', follow_redirects=True)
        self.assertEqual(response.request.path, '/forgot_password')

    def test_reset_password_changes_password_and_is_single_use(self):
        token = tokens.make_reset_token(self.confirmed)
        response = self.client.post(f'/reset-password/{token}', data={
            'new_password': 'N3w@Pass!', 'repeat_new': 'N3w@Pass!',
        }, follow_redirects=True)
        self.assertEqual(response.request.path, '/login')

        # The new password works.
        user = db.session.get(User, self.confirmed.id)
        self.assertTrue(user.verify_password('N3w@Pass!'))

        # The token is single-use: it stopped verifying once the password changed.
        response = self.client.get(f'/reset-password/{token}', follow_redirects=True)
        self.assertEqual(response.request.path, '/forgot_password')

    def test_reset_password_rejects_mismatched_passwords(self):
        token = tokens.make_reset_token(self.confirmed)
        response = self.client.post(f'/reset-password/{token}', data={
            'new_password': 'N3w@Pass!', 'repeat_new': 'different',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('Passwords must match', response.get_data(as_text=True))
        # Password unchanged.
        self.assertTrue(db.session.get(User, self.confirmed.id).verify_password('P@ssw01d'))


if __name__ == '__main__':
    unittest.main()
