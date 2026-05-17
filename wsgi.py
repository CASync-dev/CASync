from werkzeug.middleware.proxy_fix import ProxyFix

from app import create_app
from app.config import DeploymentConfig

app = create_app(DeploymentConfig())

# Two trusted hops in front of the container: the host nginx (which terminates
# TLS and sets the original X-Forwarded-* headers) and Coolify's Traefik (which
# appends itself). x_for=2 unwinds both so REMOTE_ADDR ends up as the real
# client IP rather than nginx/Traefik. x_proto/x_host/x_prefix stay at 1 since
# those aren't chained headers — only the last (Traefik) value matters.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=2, x_proto=1, x_host=1, x_prefix=1)
