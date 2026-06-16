# System Emails (Resend)

Transactional email for casync — the emails the app sends *to users* as part of
normal operation: account confirmations, password resets, and similar
system-generated messages.

This is **outbound only**. Inbound mail (e.g. `support@casync.dev` forwarding to
a Gmail inbox) is handled separately by Cloudflare Email Routing and is not part
of this feature. The two systems are deliberately kept apart and do not share
configuration.

---

## What it is

A thin integration with [Resend](https://resend.com) that lets the app send
authenticated transactional email from our own domain.

Resend is a transactional email API. The app makes an HTTPS call with the
recipient, subject, and body; Resend handles delivery, signing, and
deliverability. We don't run a mail server.

**Why Resend:** the free tier covers 3,000 emails/month (permanent, not a trial)
on one custom domain, which is well above expected volume for confirmations and
password resets. Clean API, good fit for the Python/Flask backend.

---

## How it works

1. A user action triggers a transactional event (registers an account, requests
   a password reset, etc.).
2. The app generates any needed token/link (e.g. a signed, time-limited password
   reset token) and composes the message.
3. The app calls the Resend API over HTTPS with an API key, specifying the
   `from` address, `to` recipient, subject, and HTML/text body.
4. Resend signs the message with our domain's DKIM key and delivers it.
5. The recipient's mail provider validates SPF/DKIM/DMARC against our DNS and
   (assuming reputation is good) delivers to the inbox.

The app never connects to an SMTP server or handles delivery itself — it only
makes API calls. Delivery status, bounces, and logs are visible in the Resend
dashboard.

### Sending domain

Mail is sent from a dedicated **subdomain**, `send.casync.dev`, rather than the
root domain. This:

- keeps outbound sending isolated from the root domain's inbound mail
  (Cloudflare Email Routing on `casync.dev`), so the two never interfere; and
- isolates sending reputation to the subdomain, protecting the root domain.

Example `from` address: `noreply@send.casync.dev`.

---

## What it expects

### Configuration (environment)

| Variable | Purpose |
| --- | --- |
| `RESEND_API_KEY` | Auth for the Resend API. Stored as a secret / env var, **never** committed to code. |
| `MAIL_FROM` | The verified sender address, e.g. `noreply@send.casync.dev`. |
| `APP_BASE_URL` | Used to build absolute links (reset URLs, confirmation links) in email bodies. |

### DNS (added in Cloudflare, on `send.casync.dev`)

Resend issues these records when the domain is added. All must be **DNS-only
(grey cloud)** — mail records are never proxied through Cloudflare.

- **DKIM** record (signs outbound mail as genuinely from us).
- **SPF** record for the sending subdomain (authorises Resend to send on our
  behalf).
- **DMARC** record (recommended; a `p=none` policy on the root domain to start,
  for monitoring). Completes SPF + DKIM + DMARC so receiving providers trust the
  mail.

Sending only works once Resend reports the domain as **Verified**.

### Runtime expectations

- Outbound network access from the app to the Resend API endpoint.
- Each transactional flow (confirmation, reset) calls the send function with a
  valid recipient and a composed message.
- Failures (API errors, unverified domain, invalid key) should be handled
  gracefully — a failed reset email must not leave the user silently stuck.

---

## Setup status

**Done so far:**

- Domain added to Resend (`send.casync.dev`).

**Remaining:**

- [ ] Add the DKIM / SPF (and DMARC) DNS records in Cloudflare as DNS-only.
- [ ] Wait for Resend to show the domain as **Verified**.
- [ ] Generate a Resend API key and store it as `RESEND_API_KEY` in the app's
      environment/secrets.
- [ ] Decide and set the `MAIL_FROM` address.
- [ ] Wire the send call into the password-reset and account-confirmation flows.
- [ ] Send a test message end-to-end and confirm inbox delivery (check
      SPF/DKIM/DMARC pass in the received headers).

---

## Out of scope

- Inbound mail / receiving (handled by Cloudflare Email Routing).
- Marketing or bulk email (transactional only; keeping these separate protects
  deliverability).
