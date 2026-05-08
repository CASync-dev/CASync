import unittest
from app import create_app, db
from app.config import TestConfig
from app.models import User
from app.loggedout.loggedout import register, login

# Tests User functionability: registering, logging, password hashing, etc.
class UserTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(config_class=TestConfig())
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        self.app = None
        self.app_context = None
