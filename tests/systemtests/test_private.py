import os
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.systemtests.base import BaseSeleniumTest, localHost

from app import db
from app.models import Event, User, Friendship
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
        # delete any users created during the test except for gerald (id=1) who is needed to log in and access the authenticated pages
        User.query.filter(User.id != 1).delete()
        # delete any friendships created during the test
        Friendship.query.delete()
        
        db.session.commit()
        # logout after each test to ensure a clean slate for the next one
        self.driver.find_element(By.ID, 'logout').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/login")
        )

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
        # if skipping sat or sun, need to navigate to next week then check for the event there, otherwise check for it in the current week
        today = datetime.now()
        target = today + timedelta(days=1)
        # add days until the target is a weekday
        while target.weekday() >= 5:  # 5=Sat, 6=Sun
            target += timedelta(days=1)
        # Determine if target falls outside the currently displayed calendar week (Mon–Sun)
        week_monday = today - timedelta(days=today.weekday())
        week_sunday = week_monday + timedelta(days=6)
        is_next_week = target.date() > week_sunday.date()
        # set start and end time to target day at noon and 1pm, formatted as YYYY-MM-DDTHH:MM for the datetime-local input
        start_dt = target.replace(hour=12, minute=0, second=0, microsecond=0)
        end_dt = start_dt + timedelta(hours=1)
        start_str = start_dt.strftime("%Y-%m-%dT%H:%M")
        end_str = end_dt.strftime("%Y-%m-%dT%H:%M")
        # use JS to set the values of the datetime-local inputs since send_keys doesn't work well with them
        self.driver.find_element(By.ID, 'event-title').send_keys("Selenium Test Event")
        self.driver.execute_script("document.getElementById('event-start').value = arguments[0]", start_str)
        self.driver.execute_script("document.getElementById('event-end').value = arguments[0]", end_str)
        self.driver.find_element(By.ID, 'submit-event-btn').click()
        # check modal closes
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element((By.ID, 'drawer'))
        )
        # navigate to next week if the event was created there
        if is_next_week:
            self.driver.find_element(By.ID, 'btn-next-week').click()
        # always wait for the event to appear before asserting
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

    def test_friends_search(self):
        self.driver.find_element(By.ID, 'nav-friends').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/friends")
        )
        # add two friends to test database for gerald, then refresh the page and check that they appear in the search results when typing their names into the search box
        user2 = User(username="Mkgee", email="mkgee@example.com", id=67, password="foo")
        user3 = User(username="Soul Wun", email="soulwun@example.com", id=69, password="foo")
        db.session.add(user2)
        db.session.add(user3)
        db.session.commit()
        friendship1 = Friendship(sender_id=1, recipient_id=user2.id,status='accepted')
        friendship2 = Friendship(sender_id=user3.id, recipient_id=1,status='accepted')
        db.session.add(friendship1)
        db.session.add(friendship2)
        db.session.commit()
        self.driver.refresh()
        #check friends load
        friends = self.driver.find_elements(By.CSS_SELECTOR, ".friend")
        self.assertEqual(len(friends), 2)
        # check that the search box is present and can be typed into
        search_box = self.driver.find_element(By.ID, 'friend-search-input')
        search_box.send_keys("Mkgee")
        self.assertEqual(search_box.get_attribute("value"), "Mkgee")
        #check only the searched friend appears
        visible_friends = self.driver.find_elements(By.CSS_SELECTOR, ".friend:not(.hidden)")

        self.assertIn("Mkgee", visible_friends[0].text)
        #clear search and check both friends appear again
        search_box.clear()
        friends = self.driver.find_elements(By.CSS_SELECTOR, ".friend")
        self.assertEqual(len(friends), 2)
        #search for the other friend and check it appears
        search_box.send_keys("Soul Wun")
        self.assertEqual(search_box.get_attribute("value"), "Soul Wun")
        visible_friends = self.driver.find_elements(By.CSS_SELECTOR, ".friend:not(.hidden)")
        self.assertEqual(len(visible_friends), 1) # only soul wun should appear
        self.assertIn("Soul Wun", visible_friends[0].text)

    def test_friends_add(self):
        self.driver.find_element(By.ID, 'nav-friends').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/friends")
        )
        # add a user to the test database
        user2 = User(username="Mkgee", email="mkgee@example.com", id=67, password="foo")
        db.session.add(user2)
        db.session.commit()
        #open add friend modal
        self.driver.find_element(By.ID, 'add-friend-menu-btn').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'add-friend-modal'))
        )
        # type user email and submit search
        self.driver.find_element(By.ID, 'user-search-input').send_keys("mkgee@example.com")
        self.driver.find_element(By.ID, 'submit-search-friends-btn').click()
        # wait for search results to appear and check that the searched user appears
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".friend-result"))
        )
        friend_results = self.driver.find_elements(By.CSS_SELECTOR, ".friend-result")
        self.assertEqual(len(friend_results), 1)
        self.assertIn("Mkgee", friend_results[0].text)
        # refresh the page and reopen the modal to search for the users username instead of email, check the search still works
        self.driver.refresh()
        self.driver.find_element(By.ID, 'add-friend-menu-btn').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'add-friend-modal'))
        )
        self.driver.find_element(By.ID, 'user-search-input').send_keys("Mkgee")
        self.driver.find_element(By.ID, 'submit-search-friends-btn').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".friend-result"))
        )
        friend_results = self.driver.find_elements(By.CSS_SELECTOR, ".friend-result")
        self.assertEqual(len(friend_results), 1)
        self.assertIn("Mkgee", friend_results[0].text)

        # click the add friend button and check it changes to sent
        add_btn = friend_results[0].find_element(By.XPATH, ".//button[contains(@id, 'add-friend-btn')]")
        add_btn.click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.text_to_be_present_in_element((By.XPATH, ".//button[contains(@id, 'add-friend-btn')]"), "Request Sent")
        )
        self.assertEqual(add_btn.text, "Request Sent")
        # close the friend modal 
        self.driver.find_element(By.ID, 'close-add-friend-modal-btn').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element((By.ID, 'add-friend-modal'))
        )
        # set the friendship to accepted in the database, refresh the page, and check that the new friend appears in the friends list
        friendship = Friendship(sender_id=1, recipient_id=user2.id,status='accepted')
        db.session.add(friendship)
        db.session.commit()
        self.driver.refresh()
        friends = self.driver.find_elements(By.CSS_SELECTOR, ".friend")
        self.assertEqual(len(friends), 1)
        self.assertIn("Mkgee", friends[0].text)

    def test_friends_requests(self):
        self.driver.find_element(By.ID, 'nav-friends').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/friends")
        )
        # add a user and a pending friend request to the test database, then refresh the page and check that the friend request appears in the friend requests section
        user2 = User(username="Mkgee", email="mkgee@example.com", id=67, password="foo")
        db.session.add(user2)
        db.session.commit()
        friendship = Friendship(sender_id=user2.id, recipient_id=1, status='pending')
        db.session.add(friendship)
        db.session.commit()
        self.driver.refresh()
        # open friend request modal)
        self.driver.find_element(By.ID, 'friend-requests-btn').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'friend-requests-modal'))
        )
        # check that the friend request appears with the correct username
        request_elements = self.driver.find_elements(By.CSS_SELECTOR, ".friend-request")
        
        self.assertEqual(len(request_elements), 1)
        self.assertIn("Mkgee", request_elements[0].text)
        # click the accept button and check that the request is removed from the pending requests and appears in the friends list
        self.driver.find_element(By.ID,'accept-friend-request-btn').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element(request_elements[0])
        )
        # check modal closes
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element((By.ID, 'friend-requests-modal'))
        )
        friends = self.driver.find_elements(By.CSS_SELECTOR, ".friend")
        self.assertEqual(len(friends), 1)
        self.assertIn("Mkgee", friends[0].text)
        # set another pending friend request in the database, refresh, click the reject button
        user3 = User(username="Soul Wun", email="soulwun@example.com", id=68, password="foo")
        db.session.add(user3)
        db.session.commit()
        friendship2 = Friendship(sender_id=user3.id, recipient_id=1, status='pending')
        db.session.add(friendship2)
        db.session.commit()
        self.driver.refresh()
        self.driver.find_element(By.ID, 'friend-requests-btn').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'friend-requests-modal'))
        )
        request_elements = self.driver.find_elements(By.CSS_SELECTOR, ".friend-request")
        self.assertEqual(len(request_elements), 1)
        self.assertIn("Soul Wun", request_elements[0].text)
        self.driver.find_element(By.ID,'reject-friend-request-btn').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element(request_elements[0])
        )
        # close modal and check the rejected friend does not appear in the friends list
        self.driver.find_element(By.ID, 'close-friend-requests-modal-btn').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element((By.ID, 'friend-requests-modal'))
        )
        friends = self.driver.find_elements(By.CSS_SELECTOR, ".friend")
        self.assertEqual(len(friends), 1) # only mkgee should be in the friends list, soul wun should be rejected
        self.assertIn("Mkgee", friends[0].text)

    def test_friends_remove(self):
        self.driver.find_element(By.ID, 'nav-friends').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/friends")
        )
        # add a friend to the test database, refresh the page, check that they appear in the friends list, click the remove button, and check that they are removed from the friends list
        user2 = User(username="Mkgee", email="mkgee@example.com", id=67, password="foo")
        db.session.add(user2)
        db.session.commit()
        friendship = Friendship(sender_id=1, recipient_id=user2.id,status='accepted')
        db.session.add(friendship)
        db.session.commit()
        self.driver.refresh()
        friends = self.driver.find_elements(By.CSS_SELECTOR, ".friend")
        self.assertEqual(len(friends), 1)
        self.assertIn("Mkgee", friends[0].text)
        self.driver.find_element(By.ID, 'remove-friend-btn').click()
        #check confirmation modal appears, click confirm, and check modal closes
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'remove-confirmation'))
        )
        self.driver.find_element(By.ID, 'confirm-delete-btn').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element((By.ID, 'remove-confirmation'))
        )
        # check friend is gone
        friends = self.driver.find_elements(By.CSS_SELECTOR, ".friend")
        self.assertEqual(len(friends), 0)

    def test_friends_schedule(self):
        # nav to friedns page
        self.driver.find_element(By.ID, 'nav-friends').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/friends")
        )
        # add a friend and an event for that friend to the test database
        user2 = User(username="Mkgee", email="mkgee@example.com", id=67, password="foo")
        db.session.add(user2)
        db.session.commit()
        friendship = Friendship(sender_id=1, recipient_id=user2.id,status='accepted')
        db.session.add(friendship)
        db.session.commit()
        now = datetime.now(timezone.utc)
        monday = now - timedelta(days=now.weekday())
        start_time = (monday + timedelta(days=2)).replace(hour=12, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(hours=1)
        event = Event(title="Mkgee's Event", start_time=start_time, end_time=end_time, user_id=user2.id)
        db.session.add(event)
        db.session.commit()
        self.driver.refresh()
        # check the friend appears in the friends list and click the button to view their schedule
        friends = self.driver.find_elements(By.CSS_SELECTOR, ".friend")
        self.assertEqual(len(friends), 1)
        self.assertIn("Mkgee", friends[0].text)
        self.driver.find_element(By.ID, 'view-schedule-btn').click()
        # check modal opens
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'friend-schedule-modal'))
        )
        # check the modal title contains the friends name
        self.assertIn("Mkgee's Schedule", self.driver.find_element(By.ID, 'friend-schedule-title').text)
        # check the event appears in the friend's schedule
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#friend-schedule-modal [data-event-id][data-col]"))
        )
        events = self.driver.find_elements(By.CSS_SELECTOR, "#friend-schedule-modal [data-event-id][data-col]")
        self.assertEqual(len(events), 1)
        self.assertIn("Mkgee's Event", events[0].text)
        # close the modal and check it closes
        self.driver.find_element(By.ID, 'close-friend-schedule-btn').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element((By.ID, 'friend-schedule-modal'))
        )
        
    # ------------------------------------------------------------------------------------------------------- #
    # GROUPS #

    '''
    Quick test command:
    python -m unittest -v tests.systemtests.test_private.PrivateSeleniumTests.<test_function>
    ''' 

    # ---------------- #
    # Helper functions #
    # ---------------- #

    def go_to_groups_page(self):
        self.driver.find_element(By.ID, 'nav-groups').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains('/groups')
        )

    # Opens the create group modal (assumes user is on groups page)
    def open_create_group_modal(self):
        self.driver.find_element(By.ID, 'btn-create-group').click()
        return WebDriverWait(self.driver, timeout=10).until(
                EC.visibility_of_element_located((By.ID, 'create-group'))
            ) 
    
    # Closes the create group modal (assumes the create group modal is open)
    def close_create_group_modal(self):
        self.driver.find_element(By.ID, 'btn-close-create-group').click()
        return WebDriverWait(self.driver, timeout=10).until(
                EC.invisibility_of_element_located((By.ID, 'create-group'))
            )
    
    # Opens the select friend modal (opens the group modal within it, assumes group modal was initially closed)
    def open_select_friend_modal(self):
        create_group_modal = self.open_create_group_modal()
        group_name_input = create_group_modal.find_element(By.ID, 'group-name-input')

        group_name = 'My Group'
        group_name_input.clear()
        group_name_input.send_keys(group_name)
        self.driver.find_element(By.ID, 'group-name-next').click()

        return WebDriverWait(self.driver, timeout=10).until(
                EC.visibility_of_element_located((By.ID, 'select-friend'))
            )
    
    # Closes the select friends modal (assumes the modal is open)
    def close_select_friend_modal(self):
        self.driver.find_element(By.ID, 'btn-close-select-friend').click()
        return WebDriverWait(self.driver, timeout=10).until(
                EC.invisibility_of_element_located((By.ID, 'select-friend'))
            )
    
    def add_friends_to_user(self):
        # Add two friends to test database for gerald, then refresh the page (Yoinked from friends test)
        user2 = User(username="Mkgee", email="mkgee@example.com", id=67, password="foo")
        user3 = User(username="Soul Wun", email="soulwun@example.com", id=69, password="foo")
        db.session.add(user2)
        db.session.add(user3)
        db.session.commit()
        friendship1 = Friendship(sender_id=1, recipient_id=user2.id,status='accepted')
        friendship2 = Friendship(sender_id=user3.id, recipient_id=1,status='accepted')
        db.session.add(friendship1)
        db.session.add(friendship2)
        db.session.commit()
        self.driver.refresh()

        return user2, user3

    # ---------------- #       

    # Check that clicking links/buttons correctly takes users to Groups page
    def test_groups_navigation(self):
        # Click on groups link/page
        self.driver.find_element(By.ID, 'nav-groups').click()

        # Check url is groups
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains('/groups')
        )

        self.assertIn('/groups', self.driver.current_url)

        # Check that there are no groups created (for new user)
        ul_groups_list = self.driver.find_element(By.ID, 'groups-list')
        li_groups = ul_groups_list.find_elements(By.TAG_NAME, 'li') 
        self.assertFalse(li_groups)

    # Check that creating a group works (single person only, no friends yet)
    def test_groups_create_group_with_single_user(self):
        # Go to groups page
        self.go_to_groups_page()

        # Check that the 'Create Group' button works
        create_group_modal = self.open_create_group_modal()
        self.assertTrue(create_group_modal.is_displayed())
        self.assertIn("Create a Group", create_group_modal.text)
        self.assertIn("Name your new group", create_group_modal.text)

        # Check input works
        group_name_input = create_group_modal.find_element(By.ID, 'group-name-input')
        
        # Check typing into input works
        group_name = 'My Group'
        group_name_input.clear()
        group_name_input.send_keys(group_name)
        self.assertEqual(group_name_input.get_attribute("value"), group_name)
        
        # Check closing and reopening the modal
        self.close_create_group_modal()

        # Check going to select friends modal
        select_friend_modal = self.open_select_friend_modal()
        self.assertTrue(select_friend_modal.is_displayed())
        self.assertIn("Create a Group", select_friend_modal.text)
        self.assertIn(f"Add your friends to {group_name}!", select_friend_modal.text)

        # Check closing select friends modal
        self.close_select_friend_modal()
        
        # Check 'Complete' button works in select friends modal to create group
        self.open_select_friend_modal()
        self.driver.find_element(By.ID, 'friend-search-submit').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element_located((By.ID, 'select-friend'))
        )

        # Check if group with only current user is created
        myGroupId = 1 # first group created, should have id = 1
        myGroup = WebDriverWait(self.driver, timeout=10).until(
            EC.visibility_of_element_located((By.ID, f'group-{myGroupId}'))
        )

        self.assertIn(group_name, myGroup.text)

        buttons = myGroup.find_elements(By.TAG_NAME, 'button')
        button_texts = [btn.text for btn in buttons]
        self.assertEqual(len(buttons), 3)
        self.assertIn("Leave", button_texts)
        self.assertIn("Schedule", button_texts)

        for btn in buttons:
            self.assertTrue(btn.is_displayed())
            self.assertTrue(btn.is_enabled())

        # Check if avatars of each member exists
        # group_avatars = self.driver.find_element(By.ID, 'group-member-avatars')
        member_avatars = WebDriverWait(self.driver, 10).until(
            lambda d: d.find_element(By.ID, "group-member-avatars").find_elements(By.TAG_NAME, "img")
        )

        avatar_id = [img.get_attribute("id") for img in member_avatars]

        self.assertEqual(len(member_avatars), 1)
        self.assertIn('gerald-avatar', avatar_id)

        # Check if avatars are visible
        for avatar in member_avatars:
            self.assertTrue(avatar.is_displayed())
        
    def test_groups_leave_group(self):
        # Create a group
        self.go_to_groups_page()
        self.open_select_friend_modal()
        self.driver.find_element(By.ID, 'friend-search-submit').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element_located((By.ID, 'select-friend'))
        )

        myGroupId = 1 # first group created, should have id = 1
        myGroup = WebDriverWait(self.driver, timeout=10).until(
            EC.visibility_of_element_located((By.ID, f'group-{myGroupId}'))
        )
        
        # Go to Leave button
        leave_button = myGroup.find_element(By.ID, f"btn-leave-group-{myGroupId}")
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'})", leave_button)
        WebDriverWait(self.driver, timeout=10).until(
            EC.element_to_be_clickable((By.ID, f"btn-leave-group-{myGroupId}"))
        )
        leave_button.click()

        leave_group_modal = WebDriverWait(self.driver, timeout=10).until(
                EC.visibility_of_element_located((By.ID, 'remove-confirmation'))
            )
        self.assertTrue(leave_group_modal.is_displayed())

        # Confirm leaving group
        self.driver.find_element(By.ID, 'confirm-delete-btn').click()
        WebDriverWait(self.driver, timeout=10).until(
                EC.invisibility_of_element_located((By.ID, 'remove-confirmation'))
            )
        
        # Check that group has been removed from screen
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element_located((By.ID, f'group-{myGroupId}'))
        )

    def test_group_create_with_friends(self):
        # Go to groups page and add friends to gerald
        self.go_to_groups_page()
        user2, user3 = self.add_friends_to_user()

        # Open select friend modal and wait until friends pop up in search results
        self.open_select_friend_modal()
        WebDriverWait(self.driver, timeout=10).until(
            lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "#friend-search-results li")) > 0
        )
        friends_search_result = self.driver.find_element(By.ID, 'friend-search-results')

        # Add friends to group
        friends_search_result.find_element(By.ID, user2.username).click()
        friends_search_result.find_element(By.ID, user3.username).click()

        # Create the group
        self.driver.find_element(By.ID, 'friend-search-submit').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element_located((By.ID, 'select-friend'))
        )

        # Check if group is created
        group_name = 'My Group'
        group_id = 1 # first group created, should have id = 1
        my_group = WebDriverWait(self.driver, timeout=10).until(
            EC.visibility_of_element_located((By.ID, f'group-{group_id}'))
        )

        self.assertIn(group_name, my_group.text)

        buttons = my_group.find_elements(By.TAG_NAME, 'button')
        button_texts = [btn.text for btn in buttons]
        self.assertEqual(len(buttons), 3)
        self.assertIn("Leave", button_texts)
        self.assertIn("Schedule", button_texts)

        for btn in buttons:
            self.assertTrue(btn.is_displayed())
            self.assertTrue(btn.is_enabled())

        # Check if avatars of each member exists
        # group_avatars = self.driver.find_element(By.ID, 'group-member-avatars')
        member_avatars = WebDriverWait(self.driver, 10).until(
            lambda d: d.find_element(By.ID, "group-member-avatars").find_elements(By.TAG_NAME, "img")
        )

        avatar_id = [img.get_attribute("id") for img in member_avatars]

        self.assertEqual(len(member_avatars), 3)
        self.assertIn('gerald-avatar', avatar_id)
        self.assertIn(f'{user2.username}-avatar', avatar_id)
        self.assertIn(f'{user3.username}-avatar', avatar_id)

        # Check if avatars are visible
        for avatar in member_avatars:
            self.assertTrue(avatar.is_displayed())

    def test_group_details(self):
        # Go to groups page and add friends to gerald
        self.go_to_groups_page()
        user2, user3 = self.add_friends_to_user()

        # Open select friend modal and wait until friends pop up in search results
        self.open_select_friend_modal()
        WebDriverWait(self.driver, timeout=10).until(
            lambda driver: len(driver.find_elements(By.CSS_SELECTOR, "#friend-search-results li")) > 0
        )
        friends_search_result = self.driver.find_element(By.ID, 'friend-search-results')

        # Add friends to group
        friends_search_result.find_element(By.ID, user2.username).click()
        friends_search_result.find_element(By.ID, user3.username).click()

        # Create the group
        self.driver.find_element(By.ID, 'friend-search-submit').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element_located((By.ID, 'select-friend'))
        )

        # Check if group is created
        group_name = 'My Group'
        group_id = 1 # first group created, should have id = 1
        my_group = WebDriverWait(self.driver, timeout=10).until(
            EC.visibility_of_element_located((By.ID, f'group-{group_id}'))
        )
        self.assertIn(group_name, my_group.text)

        # Check if buttons exist
        buttons = my_group.find_elements(By.TAG_NAME, 'button')
        for btn in buttons:
            self.assertTrue(btn.is_displayed())
            self.assertTrue(btn.is_enabled())

        # Go to group details
        self.driver.find_element(By.ID, f'btn-groups-details-{group_id}').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.visibility_of_element_located((By.ID, 'group-details'))
        )

        # Wait until all members pop up
        WebDriverWait(self.driver, timeout=10).until(
            lambda driver: len(driver.find_elements(By.CSS_SELECTOR, '#add-members-list li')) == 3
        )

        members_list = self.driver.find_element(By.ID, 'add-members-list').find_elements(By.TAG_NAME, 'li')
        self.assertEqual(len(members_list), 3)


        # Check if image is displayed
        for li in members_list:
            self.assertTrue(li.find_element(By.TAG_NAME, 'img').is_displayed)

        # Close group details
        self.driver.find_element(By.ID, 'btn-close-group-details').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element_located((By.ID, 'group-details'))
        )

    def test_groups_adding_friends_to_existing_group(self):
        # Create a group
        self.go_to_groups_page()
        user2, user3 = self.add_friends_to_user()

        self.open_select_friend_modal()
        self.driver.find_element(By.ID, 'friend-search-submit').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element_located((By.ID, 'select-friend'))
        )

        # Wait for group to pop up
        group_name = 'My Group'
        group_id = 1 # first group created, should have id = 1
        my_group = WebDriverWait(self.driver, timeout=10).until(
            EC.visibility_of_element_located((By.ID, f'group-{group_id}'))
        )
        self.assertIn(group_name, my_group.text)

        # Go to group details
        self.driver.find_element(By.ID, f'btn-groups-details-{group_id}').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.visibility_of_element_located((By.ID, 'group-details'))
        )

        # Wait until all members pop up
        WebDriverWait(self.driver, timeout=10).until(
            lambda driver: len(driver.find_elements(By.CSS_SELECTOR, '#add-members-list li')) == 1
        )

        # Open add member modal
        self.driver.find_element(By.ID, 'btn-add-member-modal').click()
        add_member_modal = WebDriverWait(self.driver, timeout=10).until(
                EC.visibility_of_element_located((By.ID, 'select-friend'))
            )
        self.assertIn("Add Members to Group", add_member_modal.text)
        self.assertIn(f"Add your friends to {group_name}", add_member_modal.text)

        # Wait until buttons pop up and add friends to group
        WebDriverWait(self.driver, timeout=10).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, '#friend-search-list li button')) >= 2
        )
        self.driver.find_element(By.ID, user2.username).click()
        self.driver.find_element(By.ID, user3.username).click()
        self.driver.find_element(By.ID, 'friend-search-submit').click()

        # Wait for modal to close and group details to update
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element_located((By.ID, 'select-friend'))
        )

        WebDriverWait(self.driver, timeout=10).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, '#add-members-list li')) == 3
        )

        # Check to see that group details has updated
        members = self.driver.find_elements(By.CSS_SELECTOR, '#add-members-list li')
        member_texts = [member.text for member in members]
        self.assertEqual(len(member_texts), 3)


        avatar_imgs = self.driver.find_elements(By.CSS_SELECTOR, '#group-member-avatars img')
        self.assertEqual(len(avatar_imgs), 3)

        # Close group details
        self.driver.find_element(By.ID, 'btn-close-group-details').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element_located((By.ID, 'group-details'))
        )
        






        

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
        syncmsg = WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'syncmsg'))
        )
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

    def test_settings_delacc(self):
        '''
        Tests account deletion api.
        Since not having the base acc will break everything,
        we'll create a new account for the purposes of deleting it :)
        '''
        self.driver.find_element(By.ID, 'logout').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/login")
        )
        self.driver.find_element(By.ID, 'register').click() # Navigate to register; we're going to make a new acc to delete!
        self.driver.find_element(By.ID, 'email').send_keys("newuser@example.com")
        self.driver.find_element(By.ID, 'username').send_keys("newuser")
        self.driver.find_element(By.ID, 'password').send_keys("Newpassword1234!")
        self.driver.find_element(By.ID, 'repeat_password').send_keys("Newpassword1234!")
        self.driver.find_element(By.ID, 'log').click()
        # check url is dash
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/dash")
        )
        self.driver.find_element(By.ID, 'nav-settings').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/settings")
        )
        self.driver.find_element(By.ID, 'delaccbutton').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.visibility_of_element_located((By.ID, 'deleteacc-modal'))
        )
        self.driver.find_element(By.ID, 'closeaccdelbutton').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element((By.ID, 'deleteacc-modal'))
        )
        self.driver.find_element(By.ID, 'delaccbutton').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.visibility_of_element_located((By.ID, 'deleteacc-modal'))
        )
        self.driver.find_element(By.ID, 'accdelemail').send_keys("newuser@example.com")
        self.driver.find_element(By.ID, 'accdeluser').send_keys("newuser")
        self.driver.find_element(By.ID, 'accdelpass').send_keys("Newpassword1234!")

        self.driver.find_element(By.ID, 'accdelsubmit').click()

        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/login")
        )
        msg = self.driver.find_element(By.ID, 'msg')
        self.assertEqual(msg.text, 'Your account has been deleted.')

        # Check if acc is really gone
        self.driver.find_element(By.ID, 'username').send_keys("newuser")
        self.driver.find_element(By.ID, 'password').send_keys("Newpassword1234!")

        self.driver.find_element(By.ID, 'log').click()

        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/login")
        )

        msg = self.driver.find_element(By.ID, 'msg')
        self.assertEqual(msg.text, 'Invalid username or password')

        # Login to base to continue with other tests.
        self.driver.find_element(By.ID, 'username').clear()
        self.driver.find_element(By.ID, 'password').clear()
        self.driver.find_element(By.ID, 'username').send_keys('gerald')
        self.driver.find_element(By.ID, 'password').send_keys('P@ssw01d')
        self.driver.find_element(By.ID, 'log').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/dash")
        )

    def test_settings_pfp(self):
        '''
        Tests pfps (Checking if pfp is showing, editting, removing..)
        '''
        self.driver.find_element(By.ID, 'nav-settings').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/settings")
        )
        # Check current pfp is a gravatar
        WebDriverWait(self.driver, timeout=10).until(
            EC.visibility_of_element_located((By.ID, 'pfp'))
        )
        pfpsrc = self.driver.find_element(By.ID, 'pfp').get_attribute("src")
        self.assertEqual(pfpsrc, 'https://www.gravatar.com/avatar/2de87236b26ee45d5a84ac6730c23f71?d=identicon&s=150')

        # Remove w/o pfp associated
        self.driver.find_element(By.ID, 'openpfpmodal').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.visibility_of_element_located((By.ID, 'changepfp-modal'))
        )
        self.driver.find_element(By.ID, 'delpfp').click()
        error = self.driver.find_element(By.ID, 'pfperror')
        self.assertEqual(error.text, 'Error: No profile picture associated with this account.')

        # Upload img as pfp
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, 'test_pfp.png')

        self.driver.find_element(By.ID, 'newpfp').send_keys(file_path)
        self.driver.find_element(By.ID, 'pfpupload').click()
        error = self.driver.find_element(By.ID, 'pfperror')
        self.assertEqual(error.text, 'Successfully changed your profile!')

        WebDriverWait(self.driver, timeout=10).until(
            EC.visibility_of_element_located((By.ID, 'pfp'))
        )

        pfpsrc = self.driver.find_element(By.ID, 'pfp').get_attribute("src")
        self.assertEqual(pfpsrc, localHost + 'static/avatars/1') # 1 = user id.

        # Remove custom pfp
        self.driver.find_element(By.ID, 'delpfp').click()
        error = self.driver.find_element(By.ID, 'pfperror')
        self.assertEqual(error.text, 'Successfully removed your profile!')

        WebDriverWait(self.driver, timeout=10).until(
            EC.visibility_of_element_located((By.ID, 'pfp'))
        )

        pfpsrc = self.driver.find_element(By.ID, 'pfp').get_attribute("src")
        self.assertEqual(pfpsrc, 'https://www.gravatar.com/avatar/2de87236b26ee45d5a84ac6730c23f71?d=identicon&s=150')

        self.driver.find_element(By.ID, 'pfpclose').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.invisibility_of_element((By.ID, 'changepfp-modal'))
        )

    def test_dash(self):
        '''
        Checks all elements are displaying properly. Relatively shorter test since no interactivity here
        '''
        self.driver.find_element(By.ID, 'nav-dash').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/dash")
        )
        #...
        greeting = self.driver.find_element(By.ID, 'title_username')
        self.assertIn('Hello, gerald!', greeting.text)

        # Checking clock
        actualtime = datetime.strftime(datetime.now(), '%I:%M')
        actualperiod = datetime.strftime(datetime.now(), '%p')

        time = self.driver.find_element(By.ID, 'time')
        self.assertEqual(actualtime, time.text)

        period = self.driver.find_element(By.ID, 'period')
        self.assertEqual(actualperiod, period.text)

        # Checking date

        actualweekday = datetime.strftime(datetime.now(), '%A')
        weekday = self.driver.find_element(By.ID, 'day')
        self.assertEqual(actualweekday, weekday.text)

        actualdate = datetime.strftime(datetime.now(), '%B %d, %Y')
        date = self.driver.find_element(By.ID, 'current-date')
        self.assertEqual(actualdate, date.text)

        # Checking events today (Should be none since we have no events!)
        eventstoday = self.driver.find_element(By.ID,  'big-card')
        self.assertEqual('All done! No more events today.', eventstoday.text)

        # Unfortunately it'd be pretty difficult to check events today are being rendered
        # (Esp. if the tests are run an hr from midnight)
        # Maybe test event thats happening now?
        start = datetime.now(tz=timezone.utc) - timedelta(minutes=2)
        end = datetime.now(tz=timezone.utc) + timedelta(minutes=2)
        self.event = Event(
            title='Existing event',
            description='Seeded event',
            start_time=start,
            end_time=end,
            location='Room 101',
            color='indigo',
            user_id=1,
        )
        db.session.add(self.event)
        db.session.commit()

        start = start.astimezone()
        end = end.astimezone()

        self.driver.refresh()

        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'big-card'))
        )

        untilMin = self.driver.find_element(By.ID, 'untilevent1')
        eventTitle = self.driver.find_element(By.ID, '1eventtitle')
        eventSpan = self.driver.find_element(By.ID, '1eventtimespan')

        self.assertIn('RIGHT NOW', untilMin.text)
        period = datetime.strftime(start, '%p')
        hr = start.hour
        if (start.hour > 12): # Scuffed way to getting 12 hour format for hour but it works.
            hr = start.hour-12
        starttimeformat = f'{hr}:{start.minute} {period}'
        period = datetime.strftime(end, '%p')
        hr = end.hour
        if (end.hour > 12): # Scuffed way to getting 12 hour format for hour but it works.
            hr = end.hour-12
        endtimeformat = f'{hr}:{end.minute} {period}'

        self.assertEqual('Existing event', eventTitle.text)
        span = "Starts at " + starttimeformat + ' and ends at ' + endtimeformat
        self.assertIn(span, eventSpan.text)
        self.assertIn('@ Room 101', eventSpan.text)

        # Rest of event rendering tests done in unittests.

        # Testing friends card
        friendavailable = self.driver.find_element(By.ID, 'friends-list')
        self.assertEqual('No friends :( add some friends in the friends section.', friendavailable.text)

        # Some db commits:
        friend = User(username='allen', email='friend@fun.net') # User to friend. id = 2
        friend.password = 'bar'
        db.session.add(friend)
        db.session.commit()

        fq = Friendship(sender_id=1, recipient_id=2, status='accepted', created_at=db.func.now(), accepted_at=db.func.now())
        db.session.add(fq)
        db.session.commit()

        self.driver.refresh()

        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'friend2'))
        )

        friendpfp = self.driver.find_element(By.ID, 'friend2pfp').get_attribute("src")
        self.assertEqual('https://www.gravatar.com/avatar/90dae26ca1e83875794c56b583a8f940?d=identicon&s=150', friendpfp)
        friendusername = self.driver.find_element(By.ID, 'friend2username')
        self.assertEqual('allen', friendusername.text)
        friendmail = self.driver.find_element(By.ID, 'friend2mail')
        self.assertEqual('friend@fun.net', friendmail.text)

        friendstatus = self.driver.find_element(By.ID, 'friend2status')
        self.assertEqual('No more classes today', friendstatus.text)

        # Testing multi-friend rendering
        friend = User(username='bob', email='chillguy@gmail.com') # User to friend. id = 3
        friend.password = 'bar'
        db.session.add(friend)
        db.session.commit()

        fq = Friendship(sender_id=1, recipient_id=3, status='accepted', created_at=db.func.now(), accepted_at=db.func.now())
        db.session.add(fq)
        db.session.commit()

        self.driver.refresh()
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'friend2'))
        )

        friendpfp = self.driver.find_element(By.ID, 'friend2pfp').get_attribute("src")
        self.assertEqual('https://www.gravatar.com/avatar/90dae26ca1e83875794c56b583a8f940?d=identicon&s=150', friendpfp)
        friendusername = self.driver.find_element(By.ID, 'friend2username')
        self.assertEqual('allen', friendusername.text)
        friendmail = self.driver.find_element(By.ID, 'friend2mail')
        self.assertEqual('friend@fun.net', friendmail.text)

        friendstatus = self.driver.find_element(By.ID, 'friend3status')
        self.assertEqual('No more classes today', friendstatus.text)

        friendpfp = self.driver.find_element(By.ID, 'friend3pfp').get_attribute("src")
        self.assertEqual('https://www.gravatar.com/avatar/0617ccc0cc6152aaf58197f9595c9e9d?d=identicon&s=150', friendpfp)
        friendusername = self.driver.find_element(By.ID, 'friend3username')
        self.assertEqual('bob', friendusername.text)
        friendmail = self.driver.find_element(By.ID, 'friend3mail')
        self.assertEqual('chillguy@gmail.com', friendmail.text)

        friendstatus = self.driver.find_element(By.ID, 'friend3status')
        self.assertEqual('No more classes today', friendstatus.text)

        

        # Test cases on friend status api done in unittest.
        # Test javascript rendering
        start = datetime.now(tz=timezone.utc) + timedelta(minutes=2)
        end = datetime.now(tz=timezone.utc) + timedelta(minutes=4)
        self.event = Event(
            title='Friend event 1',
            description='Seeded event',
            start_time=start,
            end_time=end,
            location='Room 101',
            color='indigo',
            user_id=2,
        )
        db.session.add(self.event)
        db.session.commit()

        start = start.astimezone()
        end = end.astimezone()

        self.driver.refresh()
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'friend2'))
        )
        friendstatus = self.driver.find_element(By.ID, 'friend2status')
        self.assertEqual('Next class in 1 min', friendstatus.text) # Accounts for time passed
        # Unfortunately we can't reliably check this if the system takes a whole min to process until here from event creation.

        start = datetime.now(tz=timezone.utc) - timedelta(minutes=2)
        end = datetime.now(tz=timezone.utc) + timedelta(minutes=2)
        self.event = Event(
            title='Friend event 2',
            description='Seeded event',
            start_time=start,
            end_time=end,
            location='Room 101',
            color='indigo',
            user_id=2,
        )
        db.session.add(self.event)
        db.session.commit()

        start = start.astimezone()
        end = end.astimezone()

        self.driver.refresh()
        WebDriverWait(self.driver, timeout=10).until(
            EC.presence_of_element_located((By.ID, 'friend2'))
        )
        friendstatus = self.driver.find_element(By.ID, 'friend2status')
        self.assertEqual('In class, Ending in 1 minutes', friendstatus.text)

        # Testing logo sends user to dash.
        self.driver.find_element(By.ID, 'logonavhome').click()
        WebDriverWait(self.driver, timeout=10).until(
            EC.url_contains("/dash")
        )



        


        
        

