'''
`URLSafeTimedSerializer(SECRET_KEY)` with per-purpose salts:

- **Confirm:** salt `email-confirm`, payload = user id, max-age **24h**.
- **Reset:** salt `password-reset:<user.password_hash>`, payload = user id,
  max-age **1h**. Binding the salt to the current password hash makes reset links
  **single-use** — once the password changes, the hash changes and old links stop
  verifying. No DB state needed.
- Functions: `make_confirm_token(user)`, `load_confirm_token(token)`,
  `make_reset_token(user)`, `load_reset_token(token)` → return user or None
  (None on expired/tampered/unknown).
'''

from flask import current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app import db
from app.models import User

# Salts namespace tokens by purpose so a token minted for one flow can't be
# replayed against another, even though both share the app SECRET_KEY.
_CONFIRM_SALT = 'email-confirm'
_RESET_SALT_PREFIX = 'password-reset:'

# Max ages in seconds.
_CONFIRM_MAX_AGE = 24 * 60 * 60  # 24 hours
_RESET_MAX_AGE = 60 * 60         # 1 hour


def _serializer():
    # Built lazily so SECRET_KEY is read from the live app config rather than
    # captured at import time.
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


def _reset_salt(user):
    # Binding the salt to the password hash makes a reset link single-use:
    # changing the password changes the hash, which invalidates the salt.
    return _RESET_SALT_PREFIX + (user.password_hash or '')


def make_confirm_token(user):
    '''Mint an email-confirmation token carrying the user id.'''
    return _serializer().dumps(user.id, salt=_CONFIRM_SALT)


def load_confirm_token(token):
    '''Return the User for a valid confirm token, else None.

    None on expired, tampered, malformed, or unknown-user tokens.
    '''
    try:
        user_id = _serializer().loads(
            token, salt=_CONFIRM_SALT, max_age=_CONFIRM_MAX_AGE
        )
    except (BadSignature, SignatureExpired):
        return None
    return db.session.get(User, user_id)


def make_reset_token(user):
    '''Mint a password-reset token carrying the user id.'''
    return _serializer().dumps(user.id, salt=_reset_salt(user))


def load_reset_token(token):
    '''Return the User for a valid reset token, else None.

    The token's salt is derived from the user's current password hash, so a
    token stops verifying once the password changes. None on expired, tampered,
    malformed, or unknown-user tokens.
    '''
    serializer = _serializer()
    # The salt depends on the user, but the user id lives inside the (signed)
    # payload. Recover the id without enforcing the salt first, then re-verify
    # with the user-bound salt to actually authenticate the token.
    try:
        user_id = serializer.loads_unsafe(token)[1]
    except BadSignature:
        return None
    if user_id is None:
        return None

    user = db.session.get(User, user_id)
    if user is None:
        return None

    try:
        serializer.loads(token, salt=_reset_salt(user), max_age=_RESET_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    return user
