# CASync

A platform for connecting timetables

A project by - UWA Agile Web 2026's 12:40pm Thursday Lab Group

| Name           | ID       | Git User |
| -------------- | -------- | -------- |
| Sze Ying Lin   | 24214052 | Stoveup  |
| Kelly Valencia | 24540356 | Kelly-Vl |
| Liam Cervenka  | 24083063 | LVaclav  |
| Tehei Cabanis  | 24467332 | Tehei01  |

------

CASync aims to connect students and their schedules. Users create an account, add their CAS (Class Allocation System) iCal link and connect with friends, join groups or create them. The primary feature is a comparative schedule to show availability amongst multiple students. 

**Tech Stack:**

- Python / Flask
- SQLite (via Flask-SQLAlchemy)
- JavaScript / JQuery
- CSS / Tailwind
- HTML / Jinja2 templates

Use the planning dir for plans

## Getting started

1. Clone the project

   ```bash
   git clone git@github.com:stoveup/AgileWeb2026.git
   cd AgileWeb2026
   ```

2. Set up the Python environment

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # For Your Filthy Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Install frontend dependencies (Tailwind CSS)

   ```bash
   npm install
   ```

4. Run any database migrations

   ```bash
   flask db upgrade # for going up a version
   flask db downgrade # for going down a version (regressing changes)
   ```

   This creates the db and applies any changes.

5. Run the seeding script

    ```bash
    python seed.py
    ```
    This 'seeds' your database with a bunch of fake data and users to use in dev.
    Should only really need to run once. 
    Optionily you can add the flag 'seed:events' to add a number of fake events based on one ical file.
    Otherwise use the settings display to import an ical.
6. Start the app

   In one terminal, watch for Tailwind CSS changes:

   ```bash
   npm run watch:css
   ```

   In another terminal, run the Flask dev server:

   ```bash
   python app.py
   ```

   Alternatively, you can run:
   ```bash
   npm run dev
   ```
   To run them both in one terminal.

   The app will be available at `http://localhost:8080`.


## Docs

Go to the /docs directory for explantions for how the app works.

# Plans And Structre

## Pages

- Homepage
    - Navigation menu
    - Logo
    - Sign up/log in
- Register
    - Enter account information (university email, password)
    - Enter iCal link
- Login
- Dashboard
    - Shows a snapshot of either the user's timetable or main friend group timetable 
- Settings
    - Update iCal profile
- Groups
    - Create group
    - Join group
    - Add person to group
- Friends
    - Add friend
    - Send friend request
- Help Page / Support

## User Stories

| #  | User Stories | 
| ---| ------------ | 
| 1  | As a student, I want to see when my friends are free so we can schedule hangouts. 
| 2  | As a student, I want to share my class schedule with my friends so they know when I am in class. 
| 3 | As a student, I want to see my friends' class schedule so I can see when they are in class.
| 4 | As a student, I want to let my friends know whether I will be attending certain classes or not so they know when to expect me.
| 5 | As a student, I want to create groups and add people to the group so we can coordinate with multiple people. 
| 6 | As a student, I want to give roles within groups. 
| 7 | As a student, I want to schedule group study sessions or meetings . 
| 8 | As a student, I want to add friends or send friend requests. 
| 9 | As a student, I want to accept friend requests. 
| 10 |  As a university club, I want to create events and see the availabilities of my committee so we can schedule event meetings. 