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


    # It's generally bad practice to hardcode a key even on the chance that environment variable is inaccessable.
    # If a SECRET_KEY can't be retrieved from env, the app should raise an error instead.