import multiprocessing
import unittest
from selenium import webdriver
from app import create_app, db
from app.config import TestConfig # Just to use the TestCase! Not really an unit test...

class SeleniumTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context
        self.app_context.push()
        db.create_all()
        self.populate_db()

        self.server_thread = multiprocessing.Process(target=self.app.run)
        self.server_thread.start()

        self.driver = webdriver.Chrome()
        self.driver.get(localHost)
        self.headlessMode() # Disable to enable creating browser window for test

    def headlessMode(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        self.driver = webdriver.Chrome(options=options)

    def tearDown(self):
        self.server_thread.terminate()
        self.driver.close()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    def populate_db(self):
        pass