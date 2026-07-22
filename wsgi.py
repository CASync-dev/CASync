from werkzeug.middleware.proxy_fix import ProxyFix

from app import create_app
from app.config import DeploymentConfig

app = create_app(DeploymentConfig())

# One trusted hop in front of the container: Caddy, which terminates TLS and
# sets X-Forwarded-*. x_for=1 takes the single client value Caddy appends so
# REMOTE_ADDR is the real client IP; trusting more would let a client spoof its
# IP via a forged X-Forwarded-For. x_proto/x_host/x_prefix stay at 1 — Caddy
# sets each of those once.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
