import os
os.environ['DATABASE_URL'] = 'sqlite:///:memory'
# Do tests on this non-persistent database

from datetime import datetime, timezone, timedelta
import unittest
from app import app, db
from app.models import User
from app.loggedout.loggedout import register, login

# Tests User functionability: registering, logging, password hashing, etc.
class UserTestCase(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
