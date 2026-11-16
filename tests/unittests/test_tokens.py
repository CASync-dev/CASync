import unittest

from app import create_app, db
from app.config import TestConfig
from app.models import User
from services import tokens


# Tests the token service: email-confirmation and password-reset links built on
# itsdangerous URLSafeTimedSerializer with per-purpose salts.
class TokenTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestConfig())
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

    # --- Confirm tokens ---------------------------------------------------

    def test_confirm_round_trip(self):
        token = tokens.make_confirm_token(self.user)
        loaded = tokens.load_confirm_token(token)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.id, self.user.id)

    def test_confirm_tampered_returns_none(self):
        token = tokens.make_confirm_token(self.user)
        self.assertIsNone(tokens.load_confirm_token(token + 'x'))

    def test_confirm_malformed_returns_none(self):
        self.assertIsNone(tokens.load_confirm_token('not-a-real-token'))

    def test_confirm_expired_returns_none(self):
        token = tokens.make_confirm_token(self.user)
        # Force expiry by shrinking the max age so any aged token is rejected.
        original = tokens._CONFIRM_MAX_AGE
        tokens._CONFIRM_MAX_AGE = -1
        try:
            self.assertIsNone(tokens.load_confirm_token(token))
        finally:
            tokens._CONFIRM_MAX_AGE = original

    # --- Reset tokens -----------------------------------------------------

    def test_reset_round_trip(self):
        token = tokens.make_reset_token(self.user)
        loaded = tokens.load_reset_token(token)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.id, self.user.id)

    def test_reset_tampered_returns_none(self):
        token = tokens.make_reset_token(self.user)
        self.assertIsNone(tokens.load_reset_token(token + 'x'))

    def test_reset_malformed_returns_none(self):
        self.assertIsNone(tokens.load_reset_token('not-a-real-token'))

    def test_reset_single_use_after_password_change(self):
        token = tokens.make_reset_token(self.user)
        # The salt is bound to the password hash, so changing the password must
        # invalidate any outstanding reset link.
        self.user.password = 'newpassword'
        db.session.commit()
        self.assertIsNone(tokens.load_reset_token(token))
        # A freshly minted token for the new password still works.
        new_token = tokens.make_reset_token(self.user)
        self.assertEqual(tokens.load_reset_token(new_token).id, self.user.id)

    def test_reset_expired_returns_none(self):
        token = tokens.make_reset_token(self.user)
        original = tokens._RESET_MAX_AGE
        tokens._RESET_MAX_AGE = -1
        try:
            self.assertIsNone(tokens.load_reset_token(token))
        finally:
            tokens._RESET_MAX_AGE = original

    # --- Cross-purpose isolation -----------------------------------------

    def test_confirm_token_not_usable_as_reset(self):
        token = tokens.make_confirm_token(self.user)
        self.assertIsNone(tokens.load_reset_token(token))

    def test_reset_token_not_usable_as_confirm(self):
        token = tokens.make_reset_token(self.user)
        self.assertIsNone(tokens.load_confirm_token(token))


if __name__ == '__main__':
    unittest.main()
