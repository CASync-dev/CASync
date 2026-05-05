from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    # Secret key for session logic
    SECRET_KEY = os.getenv('SECRET_KEY')

    #Flag error if missing secret key environment var:
    if not SECRET_KEY:
        raise Exception("SECRET_KEY is not defined, check if you have the .env file!")
    # Configure the database URI and initialize the database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'

    # PFP vars
    MAX_CONTENT_LENGTH = 1024 * 1024 # Allow files up to 1MB
    UPLOAD_EXTENSIONS = ['.jpg', '.png']
    UPLOAD_PATH = 'static/avatars'

    # It's generally bad practice to hardcode a key even on the chance that environment variable is inaccessable.
    # If a SECRET_KEY can't be retrieved from env, the app should raise an error instead.