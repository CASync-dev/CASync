import os
import threading
import unittest
from werkzeug.serving import make_server
from selenium import webdriver
from app import create_app, db
from app.config import TestConfig
from app.models import User
from dotenv import load_dotenv
load_dotenv()

# localhost url to be passed to driver.
# If Github won't run the app at this port since something else is using it, change the port until it does.
localHost = "http://127.0.0.1:9000/"

# Set HEADLESS=0 to watch the browser run the tests; defaults to headless for CI.
HEADLESS = os.environ.get("HEADLESS", "1").strip().lower() not in ("0", "false", "no")


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
            cls.driver.set_window_size(1440, 900)
        except Exception:
            return

        # Set up Flask app context and database for testing
        cls.app = create_app(config_class=TestConfig)
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

        # Create all tables and populate with initial data for testing
        db.create_all()
        cls.populate_db()

        # Use make_server instead of app.run() so we can call server.shutdown() in tearDownClass,
        # allowing the next test class to bind port 9000 with a fresh app and clean DB.
        cls.server = make_server('127.0.0.1', 9000, cls.app)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever)
        cls.server_thread.daemon = True # ensures the server thread will automatically close when the main thread finishes, even if something goes wrong with the tests
        cls.server_thread.start() # Start the Flask app in a separate thread so that it can handle requests from the Selenium WebDriver during testing

    @classmethod
    def tearDownClass(cls):
        # Shut down the browser, stop the server, and wipe the DB so the next test class starts clean.
        if cls.driver:
            cls.driver.quit()
        if hasattr(cls, 'server'):
            cls.server.shutdown()
            cls.server_thread.join()
        db.drop_all()
        cls.app_context.pop()

    @classmethod
    def populate_db(cls):
        user = User(username='gerald', email='gerald@hotmail.com')  # userid = 1
        user.password = 'P@ssw01d'
        user.email_confirmed = True  # seeded account is already confirmed so it can log in
        db.session.add(user)
        db.session.commit()

    def setUp(self):
        if not self.driver:
            self.skipTest('Web browser not available')
