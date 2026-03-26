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

4. Seed the database with mock data (run once)

   ```bash
   python seed.py
   ```

   This creates `instance/app.db` and populates it with a test user and events from `static/data/events.json`. It is safe to run again — it skips seeding if the database already has data.

5. Start the app

   In one terminal, watch for Tailwind CSS changes:

   ```bash
   npm run watch:css
   ```

   In another terminal, run the Flask dev server:

   ```bash
   python app.py
   ```

   The app will be available at `http://localhost:8080`.

## Docs

Go to the /docs directory for explantions for how the app works.
