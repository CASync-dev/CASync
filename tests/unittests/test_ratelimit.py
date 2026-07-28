import unittest

from app import create_app, db, limiter
from app.config import RateLimitedTestConfig
from app.models import User
from app.loggedout import loggedout as loggedout_module


# The rate limits are off in the normal TestConfig so the other suites can post to
# these routes freely; RateLimitedTestConfig turns them back on so we can prove the
# throttles actually fire. Limits are per-IP and the test client always presents
# 127.0.0.1, so every request here shares one bucket — reset it between tests.
class RateLimitTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=RateLimitedTestConfig())
        self.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF during tests
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        limiter.reset()

        user = User(username='gerald', email='gerald@example.com')
        user.password = 'P@ssw01d'
        user.email_confirmed = True
        db.session.add(user)
        db.session.commit()

        self.client = self.app.test_client()

        # Never hand a real email off to the service layer from here.
        self._orig_confirm = loggedout_module.send_confirmation_email
        self._orig_reset = loggedout_module.send_password_reset_email
        loggedout_module.send_confirmation_email = lambda user: True
        loggedout_module.send_password_reset_email = lambda user: True

    def tearDown(self):
        loggedout_module.send_confirmation_email = self._orig_confirm
        loggedout_module.send_password_reset_email = self._orig_reset

        limiter.reset()
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()
        self.app = None
        self.app_context = None

    def _post_until_limited(self, path, data, attempts):
        '''POST `attempts` times, returning the status code of each response.'''
        return [self.client.post(path, data=data).status_code for _ in range(attempts)]

    # --- the email-sending routes: 5 per hour -----------------------------

    def test_forgot_password_is_limited(self):
        codes = self._post_until_limited('/forgot_password', {'email': 'gerald@example.com'}, 6)
        self.assertEqual(codes[:5], [302] * 5)  # Five go through (redirect to login)...
        self.assertEqual(codes[5], 429)         # ...the sixth is throttled.

    def test_resend_confirmation_is_limited(self):
        codes = self._post_until_limited('/resend_confirmation', {'email': 'gerald@example.com'}, 6)
        self.assertEqual(codes[:5], [302] * 5)
        self.assertEqual(codes[5], 429)

    # --- login: 20 per 5 minutes -----------------------------------------

    def test_login_is_limited(self):
        data = {'username': 'gerald', 'password': 'wrong-password'}
        codes = self._post_until_limited('/login', data, 21)
        self.assertEqual(codes[:20], [200] * 20)  # Failed logins re-render the form.
        self.assertEqual(codes[20], 429)

    # --- register: 10 per hour -------------------------------------------

    def test_register_is_limited(self):
        # Each attempt reuses the same details; validation failures still count
        # against the budget, which is the point — they cost us work either way.
        data = {
            'username': 'gerald', 'email': 'gerald@example.com',
            'password': 'P@ssw01d', 'repeat_password': 'P@ssw01d',
        }
        codes = self._post_until_limited('/register', data, 11)
        self.assertNotIn(429, codes[:10])
        self.assertEqual(codes[10], 429)

    # --- what must NOT be limited ----------------------------------------

    def test_get_requests_are_not_limited(self):
        # The forms themselves must always render, however many times they're hit.
        for _ in range(25):
            self.assertEqual(self.client.get('/forgot_password').status_code, 200)
            self.assertEqual(self.client.get('/login').status_code, 200)

    def test_limit_response_uses_the_429_page(self):
        for _ in range(5):
            self.client.post('/forgot_password', data={'email': 'gerald@example.com'})
        response = self.client.post('/forgot_password', data={'email': 'gerald@example.com'})
        self.assertEqual(response.status_code, 429)
        self.assertIn('Too many attempts', response.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
