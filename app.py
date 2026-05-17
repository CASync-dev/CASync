from app import create_app
from app.config import DeploymentConfig

# Alternatively, you can run via:
# flask run --debug
# ie. using the CLI tool.

if __name__ == '__main__':
    app = create_app(DeploymentConfig())
    app.run(debug=True, port=8080)
