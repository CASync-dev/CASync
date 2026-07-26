# How the Site Works

Initially we started with a janky raw JS page loading solution but we are now using a flask setup closer to how the production site will run. 

## The Structure

```python
.
├── .gitignore                      # files and folders git should ignore
├── agents.md                       # AI agent instructions for this project
├── app.py                          # Flask entry point, routes and db init
├── copilot-instructions.md         # Copilot context hints
├── extensions.py                   # SQLAlchemy db instance (imported by app and models)
├── LICENSE                         # project licence
├── models.py                       # SQLAlchemy User and Event table definitions
├── package-lock.json               # locked npm dependency versions
├── package.json                    # npm config (used for Tailwind)
├── plans                           # planning and design artefacts
│   ├── cas.ics                     # sample iCal file for testing
│   ├── cas.json                    # same calendar data as JSON
│   ├── CASync Idea.md              # original project concept notes
│   ├── casync-demo.html            # static UI mockup
│   ├── early-site-plan.md          # early planning doc
│   └── schema.dbml                 # database schema diagram source
├── README.md                       # project overview
├── requirements.txt                # Python dependencies
├── seed.py                         # populates the db from mock JSON data (run once)
├── static
│   ├── css
│   │   ├── input.css               # Tailwind source file
│   │   └── output.css              # compiled Tailwind output (do not edit)
│   ├── data
│   │   ├── events.json             # mock events data (used by seed and api.js)
│   │   ├── friends.json            # mock friends data
│   │   ├── groups.json             # mock groups data
│   │   └── user.json               # mock logged-in user data
│   └── js
│       ├── api.js                  # API module, wraps Flask /api/* routes
│       └── schedule.js             # schedule page logic and calendar rendering
└── templates
    ├── auth
    │   └── login.html              # login page
    ├── dash.html                   # dashboard page
    ├── errors
    │   └── 404.html                # 404 error page
    ├── friends.html                # friends page
    ├── groups.html                 # groups page
    ├── layout.html                 # base template, sidebar and shell
    ├── schedule.html               # weekly calendar view
    └── settings.html               # user settings page

```

## Tailwind (Initial) Setup

(This is basically documentation for me to understand how the files and folders came to be.)

When starting up a project for Tailwind, the first code that needs to be run is:

```bash
npm init -y
```

which will quickly create a `package.json` file with default settings (`-y` skips all the questions and uses default values).

Then, we install **Tailwind** and its dependencies. In this case, we installed Tailwind v4 via the CLI (Installation guide can be found in the [official website](https://tailwindcss.com/docs/installation/tailwind-cli)).

```bash
npm install tailwindcss @tailwindcss/cli
```

While running this command (or any `npm install` command really), a `node_modules` folder will be created (or updated), which is a folder that stores all the packages/dependencies the app uses.

Instead of the usual `./src/input.css`, we put the `input.css` in `static/css/input.css`, which will contain the following line to pull the entire Tailwind CSS framework into our stylesheet:

```css
@import "tailwindcss";
```

(*Note: Since we are using Tailwind v4, ignore the old v3 style if ever encountered online when learning how to use Tailwind.

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

)

After that, run this command: 

<a id="tailwind-run"></a>

```bash
npx @tailwindcss/cli -i ./static/css/input.css -o ./static/css/output.css --watch
```

which will generate an `output.css` file, which will be the main file that our HTML will use when linking it to a stylesheet (If you go to `/templates/layout`, you can find this under `<!-- Tailwind CSS -->`). 

After all of that, Tailwind can now be used in our HTML :D.

### Dependencies

If you notice under the `package.json` file, there are two types of dependencies: `"dependencies: {}"` and `"devDependencies: {}"`.

- `dependencies` are packages that our app needs to run in **production** (required at runtime)
- `devDependencies` are packages that are only needed during **development/build time**

Adding new packages/dependencies just requires running either of these commands:

```bash
npm install <package-name>     # runtime dependency
npm install -D <package-name>  # dev dependency
```

Some dependencies that have been added to our app are:

- `date-fns`: A Javascript library for dates and times for ease of manipulating, formatting, and calculating dates
- `concurrently`: A development tool that can run multiple commands at the same time in a single terminal
- `live-server`: An HTTP server that reloads automatically when files change

### Scripts

`"scripts": {}` is a section in `package.json` that defines shortcut commands for the app. By default, the only script that is included when `npm init -y` is run is the `"test"` placeholder script.

Currently, we have these scripts in the `package.json` file:

- `"build:css": "tailwindcss -i ./static/css/input.css -o ./static/css/output.css"`
- `"watch:css": "tailwindcss -i ./static/css/input.css -o ./static/css/output.css --watch"`
- `"serve": "live-server --port=8080 --entry-file=templates/layout.html"`
- `"dev": "concurrently \"npm run watch:css\" \"npm run serve\" --names \"CSS,SERVER\" --prefix-colors \"blue,green\""`

In `watch:css`, the flag `--watch` makes Tailwind stay running in the terminal and watches the `input.css` and `output.css` for changes, so that every time a file is saved, it will automatically rebuild the `output.css` (similar to live-server but for Tailwind). This is also just basically [this](#tailwind-run) command that was referred to in the previous section. This is why in the `README.md` we run the command:

```bash
npm run watch:css
```

## The Flask Setup

It's a great idea to check out `Flask Web Development 2nd Edition, by Michael Grinberg` as that is the source for the uni and what our project is based on. Think of  `app.py` as the central command section. It does the imports, defines and connects to the db and then defines our routes.

### Template Rendering

The concept that allows us to have dynamic pages is **Rendering Templates**. The `layout.html` still serves as our main html file that is loaded the whole time. We use flask template blocks defined in the other html pages to define the page specific layouts.

Effectively you define: 

- where the html will be rendered,
- what html will be rendered, and
- when to render that html.

**Example:**

You will find inside the main content section of the `layout.html` file the following brackets:

```html
<!-- Main Content Area -->
				<!-- Navbar content and such -->
        <!-- Scrollable Content -->
        <main class="flex-1 overflow-y-auto bg-gray-50">
          {% block content %}{% endblock %} 					<!-- this bit is where the pages get rendered-->
        </main>
      </div>
```

This is what one of our template html blocks look like:

```html
{% extends "layout.html" %}
{% block content %}
<div>
  	<p1>Some Html Content</p1>
</div>
{% endblock %}
```

And then in `app.py` we define the routes so that when the user is at a certain page, we are filling the content blocks with that page's content.

```python
@app.route("/")
def index():
    return render_template("dash.html")
```

And that's pretty much it. Flask handles a lot of the work. When a user goes to a defined route, the app checks what html page is associated with that route and populates the template block with the content defined in that html's template blocks.

### Defining Scripts

Prior to using flask we did some janky script imports. Flask does this way better.

Underneath the content blocks we define script blocks. The general rule is that if the js is under 20 ish lines, it's fine to just write within that block. If its over that size we define the js in a seperate js file under `static/js/{page-specifc-js}.js`.

Those blocks look like this:

```html
{% block scripts %}
<script src="{{ url_for('static', filename='js/schedule.js') }}"></script>
{% endblock %}
```

Here we are just calling a seperate file for the js but you can just write js there.

So for example the flow could look lke this

```txt
layout.html -> schedule.html -> schedule.js
```

This means all the js is attached directly to its accompanying html. Good for organisation and clarity.

## The API

We use SQLite + SQLAlchemy for data storage, with Flask routes that return JSON to the frontend. `api.js` in `static/js` is a thin wrapper that the page scripts call — it just fetches from the Flask routes and returns the parsed JSON.

The main concepts behind api usage in flask we have employed so far are `models`, `seeding`, and `api routes`.

### Defining the db

The following code in `app.py` define the db:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db.init_app(app)
with app.app_context():
    db.create_all()
```

This defines where the db file is, initialises it and then creates it. If there isn't a db file it will create one at `instance/app.db`.

### Models

`models.py` sits in the root of the project and is where we define our db structure.

For example, here we define a simple users table:

```python
class User(db.Model):
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(64), unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    events = db.relationship('Event', backref='owner', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'
```

Each `db.Column` is a column in the table. The type (`Integer`, `String`, `DateTime`) maps to a SQLite column type. `unique=True` and `nullable=False` are constraints. SQLAlchemy enforces these so we don't have to write validation ourselves. `created_at` uses a lambda so the timestamp is generated at insert time, not when the class is defined.

The `events` relationship is not a real column, it's a virtual link so you can do `user.events` to get all events for that user. `backref='owner'` means you can also go the other way: `event.owner` gives you the user. `lazy='dynamic'` means it returns a query object rather than loading everything immediately.

## Migrations

If you haven't run into migrations before, the quick summary is databases can get messy if you are jumping through branches with different versions that have made alterations or removed things to the db schema. So migrations are like stepped through actions to get though to a certain state of the db. So if you started with what he had now, added a whole bunch of stuff, the migration would update the db.

The book wants us to use a more script based migration method with the command `MigrateCommand`, but this was made obsolete. Now the aproach is to use the flask cli.

The process:

```bash
flask db init # initiliase the migration system
flask db migrate -m "inital migration" # do the frist migration
flask db upgrade # run the migration
```

So the flow from here will be:

1. When you change a model (add a column, new table, etc.)

    ```bash
    flask db migrate -m "describe what changed"
    ```

    This auto-generates a new file in migrations/versions/. It's a good idea to review it to make sure it looks right.

2. Apply the migration to the database

    ```bash
    flask db upgrade
    ```

3. If you need to undo the last migration

    ```bash
    flask db downgrade
    ```

**Please double check your migrations!**

Flask migrate doesn't detect *every* change, so it's important to make sure something you changed is present in the migrations. Otherwise things break quick.

### API Routes

*This is all a little janky right now, but it works and will be properly done later*

Routes that return JSON live in `app.py` alongside the page routes. They use `jsonify` to return Python objects. Models have a `to_dict()` method to keep the logic out of the route.

```python
@app.route("/api/events")
def api_events():
    events = Event.query.all()
    return jsonify([e.to_dict() for e in events])
```

Current routes:

| Route             | Returns                                |
| ----------------- | -------------------------------------- |
| `GET /api/events` | All events for the seeded user (kinda) |
| `GET /api/user`   | The current user's profile             |

`api.js` in `static/js` maps these to named functions so page scripts don't hardcode URLs:

```js
api.getEvents().then(events => { ... });
api.getUser().then(user => { ... });
```

The static JSON files in `static/data` are now only used by `seed.py` to populate the database.

### Seeding

Once the models exist, the db is empty. Seeding is a one-off script that populates it with test data. Ours is `seed.py`.

It creates a test user, loads events from `static/data/events.json`, and inserts everything:

```python
liam = User(username='liam', email='liam@student.uwa.edu.au')
db.session.add(liam)
db.session.flush()  # assigns liam an id before we attach events to it

for e in events:
    db.session.add(Event(..., user_id=liam.id))

db.session.commit()
```

`db.session` is a staging area — nothing hits the database until you call `commit()`. `flush()` is a partial commit that assigns IDs without fully committing, which we need here so `liam.id` exists before we reference it.

There's a guard at the top so running `python seed.py` twice won't duplicate data:

```python
if User.query.first():
    print('DB already seeded, skipping.')
    exit()
```

# Features

## Schedule Page

The weekly calendar view. Started from a Tailwind template and stripped it back, keeping the look of the event cards. All the logic lives in `schedule.js`.

### How it loads

On page load, it hits `GET /api/events/{user_id}` to pull down all events for the user, then calls `renderDesktopEvents()`. The `user_id` is currently hardcoded to `1`,  that'll need to change once auth is in.

### Week navigation

A `weekOffset` variable tracks how far we are from the current week (0 = this week, -1 = last week, etc.). The back/forward buttons just increment or decrement that offset and re-render. The "Today" button resets it to 0 and hides itself when you're already on the current week.

The `getWeekDates()` function always calculates from the real current date rather than accumulating offsets, so navigation can't drift over time. It returns ISO date strings for Monday through Friday of the target week.

The calendar title updates based on how far out you are:
- Offset 0: `"Today, Wednesday April 12"`
- Offset ±1: `"Last Week, ..."` / `"Next Week, ..."`
- Anything further: a date range like `"Mar 1 - Mar 5"`

Today's column header is highlighted in indigo.

### Rendering events

`renderDesktopEvents()` does the heavy lifting:

1. Builds a `cellMap`, a lookup table of `"dayIndex-hourIndex" → DOM element` from the flat CSS grid. Day 0 is Monday, hour 0 is 7:00 am.

2. For each event, finds which column (day) and row (hour) it belongs to, then calculates the card height in pixels based on event duration × the measured height of one grid cell.

3. Calls `buildEventCard()` to create the card element and drops it into the right cell using absolute positioning. The card overflows downward into adjacent rows to span its full duration.

4. **Second pass:** checks for overlapping events in the same column. If a card has an event starting above it that hasn't ended yet, it gets nudged right slightly (`left: 0.5rem`) so both cards remain visible.

### Event cards

Each card shows the event title, time range, and location (location is only shown if the card is tall enough). Colors are assigned per-class; the first part of the event title before the comma (e.g. `"CS 101, Lecture"` → `"cs 101"`) is used as the key. The first time a class is seen it gets the next available color from `COLOR_MAP`. If the event has a `color` field set explicitly, that takes priority.

Clicking a card expands it to show extra details and auto-sizes to fit the content. Clicking again collapses it back. Expanded cards get a fixed width of 280px and expand leftward, rightward, or centered depending on which column they're in so they don't clip off the edge of the grid.

### Adding events

There's a tailwind drawer (dialog element with id `drawer`) that contains the add event form. On submit it:

1. Validates that title, date, start time, and end time are all filled in, and that end time is after start time.
2. POSTs to `/api/events` with the event data as JSON.
3. On success: closes the drawer, resets the form, pushes the new event into the local `events` array, and re-renders the grid.

The color picker in the form is a row of colored buttons. Clicking one calls `selectColor()`, which updates the hidden `event-color` input and adds a ring to the selected button to indicate its selected. 

## ical Imports

In `app.py` we register an endpoint called `/api/import-ical`. It expects a post request with json body content:

```json
{ "url": "<ical feed url>", "user_id": <user id> }
```

So the settings page takes the ical, and submits it to that endpoint. For now, it doenst do anything with user id as there is no auth as of time of writing. 

The api endpoint passes the json to a seperate file `services/ical.py` to run the `import_ical()` function. This funcniton does 4 things:

1. Validate the URL
2. Fetch and parse the iCal feed
3. Convert each event to our format
4. Saves everything to the database

It returns a tuple: (result, error)

- On success: `({'imported': <count>}, None)`
- On failure: `(None, '<error message>')`

## Email System

The transactional emails the app sends *to users*: account confirmation and
password reset. It's **outbound only** — we don't run a mail server, and inbound
mail (e.g. a `support@` address) is handled separately and isn't part of this.

Delivery goes through [Resend](https://resend.com), a transactional email API.
The app makes one HTTPS call with the recipient, subject, and body; Resend signs
it with our domain's DKIM key and handles delivery. The free tier (3,000
emails/month on one custom domain) is well above what confirmations and resets
need.

### The pieces

It's split into two service modules plus templates, so the routes stay thin:

```txt
services/tokens.py   # mints + verifies signed, time-limited links
services/email.py    # builds the message and sends it via Resend
templates/email/     # confirm.html/.txt and reset.html/.txt bodies
```

### Tokens (`services/tokens.py`)

Links are **stateless** — there's no token table. We use `itsdangerous`'s
`URLSafeTimedSerializer` (signed with the app `SECRET_KEY`) to encode the user id
into the URL, with a different salt per purpose so a confirm link can't be
replayed as a reset link:

- **Confirm** — salt `email-confirm`, valid **24h**.
- **Reset** — salt `password-reset:<user.password_hash>`, valid **1h**. Binding
  the salt to the current password hash makes a reset link **single-use**: once
  the password changes the hash changes, so old links stop verifying. No DB state
  needed.

Each has a `make_*` / `load_*` pair. `load_*` returns the user, or `None` if the
token is expired, tampered, malformed, or points at an unknown user.

### Sending (`services/email.py`)

`send_email(to, subject, html, text) -> bool` is the low-level call.
`send_confirmation_email(user)` and `send_password_reset_email(user)` build the
link from `APP_BASE_URL` + token, render the templates in `templates/email/`, and
hand off to `send_email`.

The important dev convenience: **if `RESEND_API_KEY` is not set, nothing is
sent** — the full message (including the link) is logged to the console and the
function returns `True`, so the surrounding flow behaves as if delivery worked.
This means you can test the whole flow locally with zero email config: register,
read the link out of your terminal, and paste it into the browser. Failures
(bad key, unverified domain, network) are logged and return `False` — they never
crash the request.

### The flows (`app/loggedout/loggedout.py`)

| Route | Method | What it does |
| --- | --- | --- |
| `/register` | POST | Creates the user (`email_confirmed=False`), sends a confirmation email, redirects to login. |
| `/confirm/<token>` | GET | Verifies the token, sets `email_confirmed=True`, auto-logs-in. |
| `/login` | POST | **Blocks login until the email is confirmed** (links to resend). |
| `/resend_confirmation` | GET/POST | Re-sends a confirmation link. Only sends for an existing *unconfirmed* account; always flashes the same generic message. |
| `/forgot_password` | GET/POST | Emails a reset link. Always flashes the same generic message. |
| `/reset-password/<token>` | GET/POST | Verifies the token and sets a new password (which invalidates the link). Also marks the email confirmed — receiving the link proves the address is theirs. |

The `email_confirmed` flag lives on the `User` model (added via a migration in
`migrations/versions/`). Forgot-password and resend deliberately give the **same
response whether or not the email exists**, so the page can't be used to discover
which addresses have accounts.

### Configuration

| Variable | Purpose |
| --- | --- |
| `RESEND_API_KEY` | Auth for the Resend API. A secret — **never** commit it (it's in `.env`, which is gitignored). Unset = console-log mode (above). |
| `MAIL_FROM` | The verified sender address (e.g. `noreply@mail.casync.dev`). |
| `APP_BASE_URL` | Base for the absolute links in emails. Defaults to `http://localhost:8080` (matches `app.py`); override in `.env` to match how you run the app. |

> **macOS gotcha:** don't point `APP_BASE_URL` at port `5000`. macOS AirPlay
> Receiver occupies 5000 and answers with `403 Forbidden`, so confirmation links
> appear "broken" even though the app is fine. Use 8080 (or whatever port you
> actually run on).

Mail is sent from a dedicated subdomain so outbound sending reputation stays
isolated from the root domain's inbound mail. For real delivery, the domain must
be **Verified** in Resend, which needs DKIM + SPF (+ DMARC) DNS records added as
**DNS-only**. None of that is required for local development thanks to the
console-log fallback.

### Testing

The service layers are unit-tested directly (`tests/unittests/test_tokens.py`,
`test_email.py`) and the four flows have route-level coverage in
`test_email_routes.py`. `TestConfig` leaves `RESEND_API_KEY` unset, so tests
never hit the network. Because login now requires a confirmed email, test
fixtures that log in via the `/login` route seed their users with
`email_confirmed=True`.
