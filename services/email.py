'''
- `send_email(to, subject, html, text) -> bool`:
  - No `RESEND_API_KEY` → log full message + any link to console, return True.
  - Else `POST https://api.resend.com/emails` with `Authorization: Bearer`,
    JSON `{from, to, subject, html, text}`, short timeout.
  - Wrap in try/except; log failures, return False (caller never crashes).
- `send_confirmation_email(user)` / `send_password_reset_email(user)`:
  build link from `APP_BASE_URL` + token, render templates, call `send_email`.
'''

import requests
from flask import current_app, render_template

from services.tokens import make_confirm_token, make_reset_token

_RESEND_URL = 'https://api.resend.com/emails'
_TIMEOUT = 10  # seconds; keep short so a slow provider never blocks a request

# Paths the email links point at. Kept here so the routes that eventually handle
# these tokens stay in sync with what we send out.
_CONFIRM_PATH = '/confirm/'
_RESET_PATH = '/reset-password/'


def send_email(to, subject, html, text):
    '''Send one email via Resend. Returns True on success, False on failure.

    When no RESEND_API_KEY is configured (local/dev/CI), nothing is sent: the
    message is logged to the console instead and we report success, so the
    surrounding flow behaves as if delivery worked.
    '''
    api_key = current_app.config.get('RESEND_API_KEY')

    if not api_key:
        current_app.logger.info(
            'RESEND_API_KEY not set — not sending email.\n'
            'To: %s\nSubject: %s\n%s',
            to, subject, text,
        )
        return True

    try:
        response = requests.post(
            _RESEND_URL,
            headers={'Authorization': f'Bearer {api_key}'},
            json={
                'from': current_app.config['MAIL_FROM'],
                'to': to,
                'subject': subject,
                'html': html,
                'text': text,
            },
            timeout=_TIMEOUT,
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        # Never let an email failure crash the caller — log and report failure.
        current_app.logger.error('Failed to send email to %s: %s', to, e)
        return False


def _link(path, token):
    # APP_BASE_URL has no trailing slash (see config); path carries its own.
    return current_app.config['APP_BASE_URL'].rstrip('/') + path + token


def send_confirmation_email(user):
    '''Mint a confirm token and email the user a confirmation link.'''
    link = _link(_CONFIRM_PATH, make_confirm_token(user))
    subject = 'Confirm your CASync account'
    html = render_template('email/confirm.html', user=user, link=link)
    text = render_template('email/confirm.txt', user=user, link=link)
    return send_email(user.email, subject, html, text)


def send_password_reset_email(user):
    '''Mint a reset token and email the user a password-reset link.'''
    link = _link(_RESET_PATH, make_reset_token(user))
    subject = 'Reset your CASync password'
    html = render_template('email/reset.html', user=user, link=link)
    text = render_template('email/reset.txt', user=user, link=link)
    return send_email(user.email, subject, html, text)
