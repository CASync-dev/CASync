from werkzeug.middleware.proxy_fix import ProxyFix

from app import create_app
from app.config import DeploymentConfig

app = create_app(DeploymentConfig())

# Coolify fronts the container with a reverse proxy that terminates HTTPS.
# Without this, Flask sees the proxy's IP and treats requests as http://, which
# breaks Secure-cookie sessions on mobile browsers.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
