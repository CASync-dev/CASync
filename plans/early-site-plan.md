# Early Site Plan

## The layout

We want to be able to play around with the site layout, page setup and general behaviour without a full backend or proper page serving. For now I set up a very basic static java script site. 

The core of it is one html file called `layout.html`. This has a all the head tags and such at the top and then the nav side bar aswell. It has a section called `main content area`. There is a script tag in this page that has the logic for the nav bar and some janky page lodaing script. Effectivly what is does is:

1. based on what nav item is hilighted, it finds and grabs the mapped html file and js file
2. It injects the html into the page and loads the java script

### HTML and the look

Now we split things up. The html for the main layout and all subpage live in a dir called `templates`. This is where we define the look of things. 

### Javascript

The java script lives in a directory called: `static/js`. This is where we define the js for each page. We seperate it to keep things clear and because we cant include a script tag in html we inject into the DOM so we load it separately. Each page gets a js file on top of an api script and a main file that hande the api and the site wide logic.

```
static
└── js
    ├── api.js
    ├── dashboard.js
    ├── main.js
    └── schedule.js
```

### CSS

Our css library of choice is tailwind. We import it via the tailwind cli. It takes an `input.css` file (contains config for tialwind and suchd) and creates an `output.css` file that we load on the site via `<link>`. Custom css can be put in `<style>` tags at the bottom of html pages.

```
static/css
├── input.css
└── output.css
```

## The Fake API

I wanted a way to simulate api endpoints so we can play with the logic of the site without having to rewrite loads of things. We wont employ a flask app setup until later in the unit so for now, I had a large set of mock data generated based on my own cal schedule. It is stored in json format in the static directory:

```
static/data
├── events.json
├── friends.json
├── groups.json
└── user.json
```

To load that data and to simulate the api structre, we have a simple js file:

### api.js

```javascript
// ── Mock API module
// Simulates backend API calls using static JSON files.
//
// HOW TO USE on any page:
//   <script src="/static/js/api.js"></script>
//   api.getEvents().then(events => { ... });
//
// SWITCHING TO THE REAL BACKEND:
//   Change BASE_URL below and update the path + options in each function.
//   All page code that calls api.* stays exactly the same.

const BASE_URL = '/static/data';

const api = {
  // GET /api/user/me — the logged-in user's profile
  getUser: () =>
    fetch(`${BASE_URL}/user.json`).then(r => r.json()),

  // GET /api/events — all calendar events for the current user
  getEvents: () =>
    fetch(`${BASE_URL}/events.json`).then(r => r.json()),

  // GET /api/friends — friends list, each with their events and online status
  getFriends: () =>
    fetch(`${BASE_URL}/friends.json`).then(r => r.json()),

  // GET /api/groups — groups the user belongs to, with members and events
  getGroups: () =>
    fetch(`${BASE_URL}/groups.json`).then(r => r.json()),
};

```

We import this into the main layout page with a script tag. Now all pages can access the api variable. Obiosuly this has no sense of security at all but it does the job. 



## Final Setup

So all together we have a janky dynamic page that loads our html and js onto the page when required. The we have a janky api that loads our fake data.

```json
.
├── AGENTS.md //Insturctions for ai asstiances (tell them to assist not write code)
├── copilot-instructions.md //Insturctions for ai asstiances (tell them to assist not write code)
├── LICENSE // The sites usage license
├── package-lock.json //Node Package Manager stuff
├── package.json //Node Package Manager stuff - tracks the dependencies
├── plans // our planning documents
│   ├── cas.ics
│   ├── cas.json
│   ├── CASync Idea.md
│   ├── casync-demo.html
│   ├── early-site-plan.md // this file
│   └── schema.dbml
├── README.md // README
├── static
│   ├── css // The css stuff (tailwind)
│   │   ├── input.css
│   │   └── output.css
│   ├── data // Mock Data
│   │   ├── events.json
│   │   ├── friends.json
│   │   ├── groups.json
│   │   └── user.json
│   └── js // All the js we import
│       ├── api.js
│       ├── dashboard.js
│       ├── main.js
│       └── schedule.js
└── templates // All the html we use
    ├── dash.html
    ├── layout.html
    ├── schedule.html
    └── settings.html
```

### The other stuff

There is of course some more files in here than that do general project stuff. 

# The schedule Page

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