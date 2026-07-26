from werkzeug.middleware.proxy_fix import ProxyFix

from app import create_app
from app.config import DeploymentConfig

app = create_app(DeploymentConfig())

# Two trusted hops in front of the container: Cloudflare (the proxied edge, which
# terminates client TLS) and Caddy (which serves the Cloudflare Origin cert and
# reverse-proxies to gunicorn). X-Forwarded-For arrives as "<client>, <cf ip>",
# so x_for=2 unwinds both to leave REMOTE_ADDR as the real client. This is only
# safe because the origin refuses non-Cloudflare traffic (inbound 80/443 is
# restricted to Cloudflare's IP ranges); otherwise a direct hit could forge the
# second-from-right XFF entry. x_proto/x_host/x_prefix stay at 1.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=2, x_proto=1, x_host=1, x_prefix=1)
