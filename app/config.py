import os

class Config:
    # Secret key for session logic
    SECRET_KEY = os.getenv('SECRET_KEY') or 'dev-secret-key' # swap for real env var later
    # Configure the database URI and initialize the database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'


    # Moved from app.py but 
    # "it is in general a good practice to set configuration from environment variables, 
    # and provide a fallback value when the environment does not define the variable" - From Flask Mega Tutorial (my saviour)
    # Maybe something to think about when handling databases (Thanks flask mega tutorial)