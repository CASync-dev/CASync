# This is a simple test file for the models
from models import User, Calendar, Event
from extensions import db
import unittest

class TestModels(unittest.TestCase):
    def setUp(self):
        # Set up a test database
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        db.create_all()

    def tearDown(self):
        # Drop the test database
        db.session.remove()
        db.drop_all()

    def test_user_model(self):
        user = User(username='testuser',