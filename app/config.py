from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    # Secret key for session logic
    SECRET_KEY = os.getenv('SECRET_KEY')

    # Removed below so github actions can run the tests as well.
    #Flag error if missing secret key environment var:
    #if not SECRET_KEY:
    #    raise Exception("SECRET_KEY is not defined, check if you have the .env file!")
    # Configure the database URI and initialize the database

    # PFP vars
    MAX_CONTENT_LENGTH = 5120 * 5120 # Allow files up to 5MB
    UPLOAD_EXTENSIONS = ['.jpg', '.png']
    UPLOAD_PATH = 'static/avatars'

    # It's generally bad practice to hardcode a key even on the chance that environment variable is inaccessable.
    # If a SECRET_KEY can't be retrieved from env, the app should raise an error instead.

    # Resend API key for email confirmation
    RESEND_API_KEY = os.getenv('RESEND_API_KEY')
    MAIL_FROM = 'noreply@mail.casync.dev'
    # Base URL used to build absolute links in emails. Default matches run.py's
    # port (8080). Override with APP_BASE_URL in .env to match how you run the app.
    # Note: avoid port 5000 on macOS — AirPlay Receiver occupies it and returns 403.
    APP_BASE_URL = os.getenv('APP_BASE_URL', 'http://localhost:8080')

class DeploymentConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'

class TestConfig(Config):
    # This is our config used for running any tests.

    # Creates a non persistent database in the memory
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' #'sqlite://' should also work but will stick to :memory for now
    SECRET_KEY = 'DEV-TEST' # This is a secret key only used for testing.
    TESTING = True

    RESEND_API_KEY = None  # Don't attempt to send real emails during tests
    MAIL_FROM = 'noreply@mail.casync.dev'
    APP_BASE_URL = 'http://localhost:5000'
