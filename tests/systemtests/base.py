import os
import threading
import time
import unittest
from selenium import webdriver
from app import create_app, db
from app.config import TestConfig
from app.models import User

# localhost url to be passed to driver.
# If Github won't run the app at this port since something else is using it, change the port until it does.
localHost = "http://127.0.0.1:9000/"

# Set HEADLESS=0 to watch the browser run the tests; defaults to headless for CI.
HEADLESS = os.environ.get("HEADLESS", "1") != "0"


class BaseSeleniumTest(unittest.TestCase):
    """Shared Selenium class: starts Flask in a thread, spins up Firefox, seeds the test DB."""

    # We initialize the WebDriver as a class variable so that it can be shared across all test methods, which speeds up the testing process since we don't have to start a new browser for each test.
    driver = None

    @classmethod
    def setUpClass(cls):
        # Set up the test class by starting the Flask app in a separate thread and initializing the Selenium WebDriver.
        # We use a class method so that the setup is done once for all tests, which speeds up the testing process.
        options = webdriver.FirefoxOptions()
        # Default runs in headless mode, sometimes its fun to watch it tho
        if HEADLESS:
            options.add_argument("--headless")
        try:
            cls.driver = webdriver.Firefox(options=options)
        except Exception:
            return

        # Set up Flask app context and database for testing
        cls.app = create_app(config_class=TestConfig)
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

        # Create all tables and populate with initial data for testing
        db.create_all()
        cls.populate_db()

        # Start the Flask app in a separate thread so that it can handle requests from the Selenium WebDriver during testing
        # We set use_reloader=False to prevent the app from starting multiple times, and daemon=True so that it will automatically close when the main thread finishes.
        cls.server_thread = threading.Thread(
            target=cls.app.run,
            kwargs={'port': 9000, 'use_reloader': False},
            daemon=True,  # alternatively we could call driver.quit() in tearDownClass, but this is simpler and ensures the server will stop even if something goes wrong with the tests
        )
        cls.server_thread.start()

        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        # Quit the Selenium WebDriver and clean up the Flask app context and database after all tests have run
        if cls.driver:
            cls.driver.quit()
            db.session.remove()
            db.drop_all()
            cls.app_context.pop()

    @classmethod
    def populate_db(cls):
        user = User(username='gerald', email='gerald@hotmail.com')  # userid = 1
        user.password = 'foo'
        db.session.add(user)
        db.session.commit()

    def setUp(self):
        if not self.driver:
            self.skipTest('Web browser not available')
