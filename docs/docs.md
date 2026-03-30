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

## The Flask Setup

Its a great idea to check out `Flask Web Development 2nd Edition, by Michael Grinberg` as that is the source for the uni and what our project is based on. Think of  `app.py` as the central command section. It does the imports, defines and connects to the db and then defines our routes. 

### Template Rendering

The concept that allows us to have dynamic pages is **Rendering Templates **. The `layout.html` still serves as our main html file that is loaded the whole time, we use flask template blocks defined in the other html pages to define the page specific layouts.

Effectivly you define, where the html will be rendered, what html will be rendered, and when to render that html.

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

And then in `app.py` we define the routes so that when the user is at a certain page, we are filling the content blocks with that pages content.

```python
@app.route("/")
def index():
    return render_template("dash.html")
```

And thats pretty much it. Flask handles a lot of the work. When a user goes to a defined route, the app checks what html page is associated with that route and populates the tempalte block with the content defined in that htmls template blocks.

### Defining Scripts

Prior to using flask we did some janky script imports. Flask does this way better. 

Underneath the content blocks we define script blocks. The general rule is that if the js is under 20 ish lines, its fine to just write within that block. If its over that size we define the js in a seperate js file under `static/js/{page-specifc-js}.js`. 

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

## The Api

We use SQLite + SQLAlchemy for data storage, with Flask routes that return JSON to the frontend. `api.js` in `static/js` is a thin wrapper that the page scripts call — it just fetches from the Flask routes and returns the parsed JSON.

The main concepts behind api usage in flask we have employed so far are `models`, `seeding`, and `api routes`.

### Defining the db

The follwoing code in `app.py` define the db:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db.init_app(app)
with app.app_context():
    db.create_all()
```

This defines where the db file is, initialises it and then creates it. If there isnt a db file it will create one at `instance/app.db`. 

### Models

`models.py` sits in the root of the project and is where we define our db structre. 

For exmaple here we define a simple users table.

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

If you havnt run into migratione before, the quick summary is databses can get messy if you are jumping through branhces with different versions that have made alterations or removed thigns to the db schema. So migrations are like stepped through actions to get though to a certain state of the db. So if you started with what he had now, added a whole bunch off stuff, the migration would update the db. 

The book wants us to use a more scirpt based migration method with the command `MigrateCommand`, but this was made obsolute. Now the aproach is to use the flask cli. 

The process:
```bash
flask db init # initiliase the migration system
flask db migrate -m "inital migration" # do the frist migration
flask db upgrade # run the migration
```

So the flow from here will be:
1. When you change a model (add a column, new table, etc.)
```
flask db migrate -m "describe what changed"
```
This auto-generates a new file in migrations/versions/. Its a good idea to review it to make sure it looks right.
2. Apply the migration to the database
```
flask db upgrade
```
3. If you need to undo the last migration
```
flask db downgrade
```

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

Once the models exist the db is empty. Seeding is a one-off script that populates it with test data. Ours is `seed.py`.

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

This is where i have started playing with the tailwind and js. I grabbed a caldner tailwind template online and stripped it down. I made sure to hold onto the look they went for for their event item. In the js we:

1. Import the events from the json

2. Get the current day and populate the correct date on the today title and the day header columns

   a) I do this by figuring out how far away the current day is from the most recent Monday. 

   b) Then we retun an array of 5 dates for each day in the cal

   c) We set them as the column headers and hilight the one that is today.

3. We have a number of time formatting helper functions that figure out:

   a) How many minutes until midnite (sets the location and length of an event item)

   b) Converts the time to a nice am pm format.

4. We have a function that builds an event html element

   a) it creates a stadnard div with themeing

   b) it sets the color based on the event data {color:}

   c) sets the height of the box based on the duration we figured out earlier

5. Then we have a big `renderDesktopEvents()` function that:

   a) creates a cell map of the grid. This gives us a nice map that is effectily {row:column = div elemnt}

   b) now for each element we: 
   	i) check if the event is in this week

   ​	ii) if it is we determine its location based on the time and date. 

   ​	iii) Call the build event function and insert it into the right grid  

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
- On failure:` (None, '<error message>')`

