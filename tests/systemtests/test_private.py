import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.systemtests.base import BaseSeleniumTest, localHost

from app import db
from app.models import Event
from datetime import datetime, timedelta, timezone

# extends the BaseSeleniumTest class, which sets up the testing var for selenium
class PrivateSeleniumTests(BaseSeleniumTest):
    """Selenium tests for routes requiring a logged in session."""

    def setUp(self):
        # call setup from the base config
        super().setUp()
        # login as gerald to access authenticated pages for testing
        self.driver.get(localHost + "login")
        self.driver.find_element(By.ID, 'username').send_keys('gerald')
        self.driver.find_element(By.ID, 'password').send_keys('P@ssw01d')
        self.driver.find_element(By.ID, 'log').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/dash")
        )

    def tearDown(self):
        # delete any events created during the test so each test starts with a clean slate
        Event.query.delete()
        db.session.commit()
        # logout after each test to ensure a clean slate for the next one
        self.driver.find_element(By.ID, 'logout').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/login")
        )

    # ------------------------------------------------------------------------------------------------------- #
    # DASH #
    # ------------------------------------------------------------------------------------------------------- #

    def test_dash(self):
        pass

    # ------------------------------------------------------------------------------------------------------- #
    # SCHEDULE #
    # ------------------------------------------------------------------------------------------------------- #

    def test_schedule_navigation(self):
        # click schedule link
        self.driver.find_element(By.ID, 'nav-schedule').click()
        # check url is schedule
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/schedule")
        )
        # check calender title is todays date (Today, Day Mon DD)
        calendarTitle = self.driver.find_element(By.ID, 'calendar-title')
        today = time.strftime("%a %b %d")
        initialTitle = "Today, " + today
        self.assertEqual(calendarTitle.text, initialTitle)
        # check next week nav buttons work
        self.driver.find_element(By.ID, 'btn-next-week').click()
        calendarTitle = self.driver.find_element(By.ID, 'calendar-title')
        nextWeek = time.strftime("%a %b %d", time.localtime(time.time() + 7*24*60*60))
        expectedTitle = "Next Week, " + nextWeek
        self.assertEqual(calendarTitle.text, expectedTitle)
        # check today nav button works
        self.driver.find_element(By.ID, 'btn-today').click()
        calendarTitle = self.driver.find_element(By.ID, 'calendar-title')
        self.assertEqual(calendarTitle.text, initialTitle)
        # check previous week nav button works
        self.driver.find_element(By.ID, 'btn-last-week').click()
        calendarTitle = self.driver.find_element(By.ID, 'calendar-title')
        d = datetime.now() - timedelta(days=7)
        prev_week = d.strftime("%a %b ") + str(d.day)
        expected_title = "Last Week, " + prev_week
        self.assertEqual(calendarTitle.text, expected_title)
        # go back to current week so tearDown's logout has a clean state
        self.driver.find_element(By.ID, 'btn-today').click()

    def test_schedule_events_load(self):
        # navigate to schedule page
        self.driver.find_element(By.ID, 'nav-schedule').click()
        # check url is schedule
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/schedule")
        )
        # check that there are no events for the user (since we haven't added any to the test database yet)
        events = self.driver.find_elements(By.CSS_SELECTOR, "[data-event-id][data-col]")
        self.assertEqual(len(events), 0)
        # manually add an event to the test database for gerald, then refresh the page and check that it appears
        # Wednesday noon UTC of the current ISO week (Mon–Fri); always goes back to the past Monday
        now = datetime.now(timezone.utc)
        monday = now - timedelta(days=now.weekday())
        start_time = (monday + timedelta(days=2)).replace(hour=12, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        event = Event(title="Test Event", start_time=start_time, end_time=end_time, user_id=1)
        db.session.add(event)
        db.session.commit()
        self.driver.refresh()
        # events are rendered via JS fetch after page load, so wait for the card to appear
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-event-id][data-col]"))
        )
        events = self.driver.find_elements(By.CSS_SELECTOR, "[data-event-id][data-col]")
        self.assertEqual(len(events), 1)
        self.assertIn("Test Event", events[0].text)

    def test_schedule_event_create(self):
        self.driver.find_element(By.ID, 'nav-schedule').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/schedule")
        )
        # click the "create event" button to open the modal
        self.driver.find_element(By.ID, 'btn-create-event').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'drawer'))
        )
        # fill out form and submit
        #start and end need to be in the future for the calendar to accept them, so we set them to be 1 day in the future, skipping satuday and sunday.
        # if skipping sat or sun, need to navigate to next week then check for the event
        starts = time.time() + 24*60*60
        is_next_week = False
        if time.localtime(starts).tm_wday == 5: # saturday
            starts += 2*24*60*60
            is_next_week = True
        elif time.localtime(starts).tm_wday == 6: # sunday
            starts += 24*60*60
            is_next_week = True
        ends = starts + 60*60
        start_str = time.strftime("%Y-%m-%dT%H:%M", time.localtime(starts))
        end_str = time.strftime("%Y-%m-%dT%H:%M", time.localtime(ends))
        self.driver.find_element(By.ID, 'event-title').send_keys("Selenium Test Event")
        self.driver.execute_script("document.getElementById('event-start').value = arguments[0]", start_str)
        self.driver.execute_script("document.getElementById('event-end').value = arguments[0]", end_str)
        self.driver.find_element(By.ID, 'submit-event-btn').click()
        #check modal closes
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element((By.ID, 'drawer'))
        )
        # if the event is in the next week, navigate to next week and check for it there, otherwise check for it in the current week
        if is_next_week:
            self.driver.find_element(By.ID, 'btn-next-week').click()
            WebDriverWait(self.driver, timeout=10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-event-id][data-col]"))
            )
        events = self.driver.find_elements(By.CSS_SELECTOR, "[data-event-id][data-col]")
        self.assertEqual(len(events), 1)
        self.assertIn("Selenium Test Event", events[0].text)

    def test_schedule_event_edit(self):
        self.driver.find_element(By.ID, 'nav-schedule').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/schedule")
        )
        # manually add an event to the test database for gerald
        now = datetime.now(timezone.utc)
        monday = now - timedelta(days=now.weekday())
        start_time = (monday + timedelta(days=2)).replace(hour=12, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        event = Event(title="Test Event", start_time=start_time, end_time=end_time, user_id=1)
        db.session.add(event)
        db.session.commit()
        self.driver.refresh()
        # wait for event to load and click it to open the edit modal
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-event-id][data-col]"))
        )
        self.driver.find_element(By.CSS_SELECTOR, "[data-event-id][data-col]").click()
        self.driver.find_element(By.ID, 'edit-event-btn').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'edit-event-modal'))
        )
        # change the title and submit
        title_input = self.driver.find_element(By.ID, 'edit-event-title')
        title_input.clear()
        title_input.send_keys("Edited Test Event")
        self.driver.find_element(By.ID, 'save-edit-btn').click()
        # Wait for the modal to close
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element((By.ID, 'edit-event-modal'))
        )
        # wait for the calendar to re-render with the updated title (fetch is async)
        WebDriverWait(self.driver, timeout=10).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, "[data-event-id][data-col]"), "Edited Test Event")
        )
        events = self.driver.find_elements(By.CSS_SELECTOR, "[data-event-id][data-col]")
        self.assertEqual(len(events), 1)
        self.assertIn("Edited Test Event", events[0].text)
    
    def test_schedule_event_delete(self):
        self.driver.find_element(By.ID, 'nav-schedule').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/schedule")
        )
        # manually add an event to the test database for gerald
        now = datetime.now(timezone.utc)
        monday = now - timedelta(days=now.weekday())
        start_time = (monday + timedelta(days=2)).replace(hour=12, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        event = Event(title="Test Event", start_time=start_time, end_time=end_time, user_id=1)
        db.session.add(event)
        db.session.commit()
        self.driver.refresh()
        # wait for event to load and click it to expand it
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-event-id][data-col]"))
        )
        self.driver.find_element(By.CSS_SELECTOR, "[data-event-id][data-col]").click()
        self.driver.find_element(By.ID, 'delete-event-btn').click()
        #wait for modal to open
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'delete-confirmation'))
        )
        #confirm deletion
        self.driver.find_element(By.ID, 'confirm-delete-btn').click()
        # Wait for the modal to close
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element((By.ID, 'delete-confirmation'))
        )
        # wait for the calendar to re-render without the deleted event (fetch is async)
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element((By.CSS_SELECTOR, "[data-event-id][data-col]"))
        )
    
    def test_schedule_event_going(self):
        self.driver.find_element(By.ID, 'nav-schedule').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/schedule")
        )
        #manually add an event to the test database for gerald that has a guest, then check that the "going" button appears and can be clicked to rsvp to the event
        now = datetime.now(timezone.utc)
        monday = now - timedelta(days=now.weekday())
        start_time = (monday + timedelta(days=2)).replace(hour=12, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        event = Event(title="Test Event", start_time=start_time, end_time=end_time, user_id=1)
        db.session.add(event)
        db.session.commit()
        self.driver.refresh()
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-event-id][data-col]"))
        )
        self.driver.find_element(By.CSS_SELECTOR, "[data-event-id][data-col]").click()
        self.driver.find_element(By.ID, 'going-toggle-btn').click()
        # wait for the calendar to re-render with the updated going status (fetch is async)
        WebDriverWait(self.driver, timeout=10).until(
            EC.element_to_be_clickable((By.ID, 'going-toggle-btn'))
        )
        event = Event.query.filter_by(title="Test Event").first()
        self.assertFalse(event.going)


    # ------------------------------------------------------------------------------------------------------- #
    # FRIENDS #
    # ------------------------------------------------------------------------------------------------------- #

    def test_friends(self):
        pass

    # ------------------------------------------------------------------------------------------------------- #
    # GROUPS #

    def test_groups(self):
        pass

    # ------------------------------------------------------------------------------------------------------- #
    # SETTINGS #
    # ------------------------------------------------------------------------------------------------------- #
    
    def test_settings_changeusername(self):
        ''' Tests the change username api'''
        self.driver.find_element(By.ID, 'nav-settings').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/settings")
        )
        username = self.driver.find_element(By.ID, 'username')
        self.assertEqual(username.text, 'gerald')

        # I think this is probably bad practice? But it's the only way it works... :(
        element = self.driver.find_element(By.ID, 'changeuserbutton')
        self.driver.execute_script("arguments[0].scrollIntoView()", element)
        element.click()

        # Test case for empty field:
        self.driver.find_element(By.ID, 'newusersubmitbutton').click()
        msg = self.driver.find_element(By.ID, 'usererror')
        self.assertEqual(msg.text, 'New Username field is required.')

        # Actual changing of username:
        self.driver.find_element(By.ID, 'newuser').send_keys('gareld')
        self.driver.find_element(By.ID, 'newusersubmitbutton').click()

        msg = self.driver.find_element(By.ID, 'usererror')
        self.assertEqual(msg.text, 'Successfully changed your username!')

        # self.driver.find_element(By.ID, 'newuserclosebutton').click()
        newusername = self.driver.find_element(By.ID, 'username')
        self.assertEqual(newusername.text, 'gareld')

        # Restoring to old username 

        # self.driver.find_element(By.ID, 'changeuserbutton').click()
        self.driver.find_element(By.ID, 'newuser').clear()
        self.driver.find_element(By.ID, 'newuser').send_keys('gerald')
        self.driver.find_element(By.ID, 'newusersubmitbutton').click()

        msg = self.driver.find_element(By.ID, 'usererror')
        self.assertEqual(msg.text, 'Successfully changed your username!')
        self.driver.find_element(By.ID, 'newuserclosebutton').click()

        username = self.driver.find_element(By.ID, 'username')
        self.assertEqual(username.text, 'gerald')
        self.driver.find_element(By.ID, 'newuserclosebutton').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element((By.ID, 'changeuser-modal'))
        )

    def test_settings_changeemail(self):
        ''' Tests the change email api'''
        self.driver.find_element(By.ID, 'nav-settings').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/settings")
        )

        email = self.driver.find_element(By.ID, 'email')
        self.assertEqual(email.text, 'gerald@hotmail.com')

        # I think this is probably bad practice? But it's the only way it works... :(
        element = self.driver.find_element(By.ID, 'changeemailbutton')
        self.driver.execute_script("arguments[0].scrollIntoView()", element)
        element.click()
        
        # Test case; no field filled in
        self.driver.find_element(By.ID, 'newemailsubmitbutton').click()
        error = self.driver.find_element(By.ID, 'mailerror')
        self.assertEqual(error.text, 'New Email field is required.')

        # Actually changing email
        self.driver.find_element(By.ID, 'newemail').send_keys('gerald@gmail.com')
        self.driver.find_element(By.ID, 'newemailsubmitbutton').click()

        error = self.driver.find_element(By.ID, 'mailerror')
        self.assertEqual(error.text, 'Successfully changed your email!')

        email = self.driver.find_element(By.ID, 'email')
        self.assertEqual(email.text, 'gerald@gmail.com')

        # Reset email back to base
        self.driver.find_element(By.ID, 'newemail').clear()
        self.driver.find_element(By.ID, 'newemail').send_keys('gerald@hotmail.com')
        self.driver.find_element(By.ID, 'newemailsubmitbutton').click()

        error = self.driver.find_element(By.ID, 'mailerror')
        self.assertEqual(error.text, 'Successfully changed your email!')
        email = self.driver.find_element(By.ID, 'email')
        self.assertEqual(email.text, 'gerald@hotmail.com')

        self.driver.find_element(By.ID, 'newemailclosebutton').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element((By.ID, 'changemail-modal'))
        )

    def test_settings_icalimportedit(self):
        '''
        Tests ical import, sync and editting
        It should also check events are loaded in schedule maybe? 
        For now it just checks that the ui is working well ig
        Tests multiple icals as well.
        '''
        SAMPLE_ICAL1 = 'https://raw.githubusercontent.com/LVaclav/test-icals/refs/heads/main/cal-v1.ics'
        SAMPLE_ICAL2 = "https://raw.githubusercontent.com/LVaclav/test-icals/refs/heads/main/cal-v2.ics"

        self.driver.find_element(By.ID, 'nav-settings').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/settings")
        )
        lastsync = self.driver.find_element(By.ID, 'last-synced')
        self.assertEqual('Never', lastsync.text)
        self.driver.find_element(By.ID, 'ical_url').send_keys(SAMPLE_ICAL1)
        self.driver.find_element(By.ID, 'icalsubmit').click()

        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/settings")
        )
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'sync-button'))
        )
        msg = self.driver.find_element(By.ID, 'msgs')
        # Doing an assert in, in case of spaces
        self.assertIn('Imported 5 events, updated 0.', msg.text) # ical id = 1

        now = datetime.now().strftime("%d/%m/%y")
        lastsync = self.driver.find_element(By.ID, 'last-synced')
        self.assertEqual(now, lastsync.text)
        numcal = self.driver.find_element(By.ID, 'sync-button')
        self.assertIn('Sync (1) cals', numcal.text)
        self.driver.find_element(By.ID, 'sync-button').click()
        syncmsg = self.driver.find_element(By.ID, 'syncmsg')
        self.assertEqual(syncmsg.text, 'Successfully synced calendar. 0 events created, 0 events updated.')

        self.driver.find_element(By.ID, 'ical_url').clear()
        self.driver.find_element(By.ID, 'ical_url').send_keys(SAMPLE_ICAL2)
        self.driver.find_element(By.ID, 'icalsubmit').click()

        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/settings")
        )
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'sync-button'))
        )

        msg = self.driver.find_element(By.ID, 'msgs')
        self.assertIn('Imported 6 events, updated 0.', msg.text) # ical id = 2
        now = datetime.now().strftime("%d/%m/%y")
        lastsync = self.driver.find_element(By.ID, 'last-synced')
        self.assertEqual(now, lastsync.text)
        numcal = self.driver.find_element(By.ID, 'sync-button')
        self.assertIn('Sync (2) cals', numcal.text)

        # Editting ical links
        self.driver.find_element(By.ID, 'editicalbutton').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.visibility_of_element_located((By.ID, 'ical-modal'))
        )
        link1 = self.driver.find_element(By.ID, 'icallink1')
        self.assertIn('https://raw.githubusercontent.com/LVaclav/test-icals/refs/heads/main/cal-v1.ics', link1.text)
        link2 = self.driver.find_element(By.ID, 'icallink2')
        self.assertIn('https://raw.githubusercontent.com/LVaclav/test-icals/refs/heads/main/cal-v2.ics', link2.text)

        self.driver.find_element(By.ID, 'removeicallink2').click()
        msg = self.driver.find_element(By.ID, 'icalediterror')
        self.assertEqual('Succesfully removed iCal Link!', msg.text)

        self.driver.find_element(By.ID, 'closeediticalbutton').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element((By.ID, 'ical-modal'))
        )
        # Simulatng a refresh
        self.driver.find_element(By.ID, 'nav-dash').click()
        self.driver.find_element(By.ID, 'nav-settings').click()

        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'sync-button'))
        )
        numcal = self.driver.find_element(By.ID, 'sync-button')
        self.assertIn('Sync (1) cals', numcal.text)

        # Reset links for next tests.
        self.driver.find_element(By.ID, 'editicalbutton').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.visibility_of_element_located((By.ID, 'ical-modal'))
        )
        self.driver.find_element(By.ID, 'removeicallink1').click()
        msg = self.driver.find_element(By.ID, 'icalediterror')
        self.assertEqual('Succesfully removed iCal Link!', msg.text)
        self.driver.find_element(By.ID, 'closeediticalbutton').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element((By.ID, 'ical-modal'))
        )

    def test_settings_changepassword(self):
        '''
        Tests changing password api (form)
        '''
        self.driver.find_element(By.ID, 'nav-settings').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/settings")
        )
        self.driver.find_element(By.ID, 'changepasswordbutton').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.visibility_of_element_located((By.ID, 'changepass-modal'))
        )
        self.driver.find_element(By.ID, 'changepassclosebutton').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element((By.ID, 'changepass-modal'))
        )
        self.driver.find_element(By.ID, 'changepasswordbutton').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.visibility_of_element_located((By.ID, 'changepass-modal'))
        )
        # Fail test cases already done in unittest, so we'll only go through the actual process.
        self.driver.find_element(By.ID, 'current_password').send_keys('P@ssw01d')
        self.driver.find_element(By.ID, 'new_password').send_keys('r@nd0mp4SS!')
        self.driver.find_element(By.ID, 'repeat_new').send_keys('r@nd0mp4SS!')

        self.driver.find_element(By.ID, 'changepasssubmit').click()

        msg = self.driver.find_element(By.ID, 'msgs')
        self.assertEqual("Successfully changed user's password.", msg.text)

        # Testing logging in works with the new pass.
        self.driver.find_element(By.ID, 'logout').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/login")
        )
        self.driver.find_element(By.ID, 'username').send_keys('gerald')
        self.driver.find_element(By.ID, 'password').send_keys('r@nd0mp4SS!')
        self.driver.find_element(By.ID, 'log').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/dash")
        )
        self.driver.find_element(By.ID, 'nav-settings').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/settings")
        )

        # Reseting pass back for next tests.
        self.driver.find_element(By.ID, 'changepasswordbutton').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.visibility_of_element_located((By.ID, 'changepass-modal'))
        )
        self.driver.find_element(By.ID, 'current_password').send_keys('r@nd0mp4SS!')
        self.driver.find_element(By.ID, 'new_password').send_keys('P@ssw01d')
        self.driver.find_element(By.ID, 'repeat_new').send_keys('P@ssw01d')

        self.driver.find_element(By.ID, 'changepasssubmit').click()

        
        

