# Will be following the unit test example from https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-viii-followers
# Since it requires less changing of files; This comment to be removed prior to merge.
import os
os.environ['DATABASE_URL'] = 'sqlite:///:memory'
# Do tests on this non-persistent database

from datetime import datetime, timezone, timedelta
import unittest
from app import app, db
from app.models import User, Event, Calendar, Friendship

# Tests User creation..?
class UserTestCase(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
