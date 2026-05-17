from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.systemtests.base import BaseSeleniumTest, localHost

# extends the BaseSeleniumTest class, which sets up the testing var for selenium
class PublicSeleniumTests(BaseSeleniumTest):
    """Selenium tests for routes accessible without authentication."""

    def test_index(self):
        self.driver.get(localHost)  # Gets homepage url

    def test_faq(self):
        self.driver.get(localHost)  # Gets homepage url
        self.driver.find_element(By.ID, 'faq').click()  # Clicks FAQ link
        # check url is correct
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/faq")
        )
        faqTitle = self.driver.find_element(By.TAG_NAME, "h1")
        assert faqTitle.text == "Frequently Asked Questions"

    def test_contact_us(self):
        self.driver.get(localHost)  # Gets homepage url
        self.driver.find_element(By.ID, 'contactus').click()  # Clicks Contact Us link
        # check url is correct
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/contactus")
        )
        contactTitle = self.driver.find_element(By.TAG_NAME, "h1")
        assert contactTitle.text == "Contact Us"

    def test_register(self):
        self.driver.get(localHost)  # Gets homepage url
        self.driver.find_element(By.ID, 'register').click()  # Clicks the register link
        # check url is correct
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/register")
        )
        # Register a new user
        self.driver.find_element(By.ID, 'email').send_keys("newuser@example.com")
        self.driver.find_element(By.ID, 'username').send_keys("newuser")
        self.driver.find_element(By.ID, 'password').send_keys("Newpassword1234!")
        self.driver.find_element(By.ID, 'repeat_password').send_keys("Newpassword1234!")
        self.driver.find_element(By.ID, 'log').click()
        # check url is dash
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/dash")
        )
        # check that the greeting is correct
        greeting = self.driver.find_element(By.ID, 'title_username')
        self.assertEqual(greeting.text, 'Hello, newuser!')
        # Logout the new user
        self.driver.find_element(By.ID, 'logout').click()
        # check url is login
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/login")
        )

    def test_loginlogout(self):
        self.driver.get(localHost + "login")  # Gets login url

        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'login'))
        )

        self.driver.find_element(By.ID, 'username').send_keys("gerald")
        self.driver.find_element(By.ID, 'password').send_keys("P@ssw01d")
        self.driver.find_element(By.ID, 'log').click()

        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'title_username'))
        )

        greeting = self.driver.find_element(By.ID, 'title_username')
        self.assertEqual(greeting.text, 'Hello, gerald!')

        self.driver.find_element(By.ID, 'logout').click()

        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'login'))
        )
        msg = self.driver.find_element(By.ID, 'msg')
        self.assertEqual(msg.text, 'You have been logged out.')

    def test_register_fail(self):
        self.driver.get(localHost + "register")

        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'register'))
        )

        # Test Case: Fail to fill all fields required.
        # The unittests go into a lot more checking on different types of errors, but
        # Here, we're just making sure we've been redirected/stopped correctly.

        self.driver.find_element(By.ID, 'log').click()

        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'register'))
        )
        error = self.driver.find_element(By.ID, 'error')
        self.assertEqual(error.text, 'All fields are required.')

    def test_login_incorrect(self):
        self.driver.get(localHost + "login")  # Gets login url

        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'login'))
        )

        self.driver.find_element(By.ID, 'username').send_keys("gerald")
        self.driver.find_element(By.ID, 'password').send_keys("bar")
        self.driver.find_element(By.ID, 'log').click()

        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'login'))
        )

        error = self.driver.find_element(By.ID, 'msg')
        self.assertEqual(error.text, 'Invalid username or password')

        self.driver.find_element(By.ID, 'username').send_keys("fakeuser")
        self.driver.find_element(By.ID, 'password').send_keys("bar")
        self.driver.find_element(By.ID, 'log').click()

        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'login'))
        )

        error = self.driver.find_element(By.ID, 'msg')
        self.assertEqual(error.text, 'Invalid username or password')
