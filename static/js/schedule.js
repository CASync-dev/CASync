// Schedule page — sets dynamic dates and renders events into the weekly calendar grid
//any libraries neededed:
// ── Grid constants
// These define the visible time range shown in the HTML grid.
// The grid runs from 07:00 am to 06:00 pm
const GRID_START_HOUR = 7; // the first row of the grid is 7:00 am
const GRID_TOTAL_SLOTS = 12; // the grid has 12 rows, so the last row starts at 6:00 pm

// ── Color themes
// Each event has a color. This maps that name to the three
// Tailwind classes needed to style an event card: background, left border, text.
const COLOR_MAP = {
  indigo: {
    bg: 'bg-indigo-100',
    border: 'border-indigo-500',
    text: 'text-indigo-800',
  },
  blue: { bg: 'bg-blue-100', border: 'border-blue-500', text: 'text-blue-800' },
  green: {
    bg: 'bg-green-100',
    border: 'border-green-500',
    text: 'text-green-800',
  },
  rose: { bg: 'bg-rose-100', border: 'border-rose-500', text: 'text-rose-800' },
  amber: {
    bg: 'bg-amber-100',
    border: 'border-amber-500',
    text: 'text-amber-800',
  },
};

// ── Event data
// This is the list of events that get rendered onto the calendar.

// This sectionm is how i first simulate the data, to better simulate ap orper backend
// i have a bunch of json files with calender data to simulate what a db would have.
// It was created with cal to json parsing libraries that might be used in the bakcend in futre
// now we call api.js that directs to the files in the static/data folder to get the data for the events.
let events = [];
api.getEvents().then((data) => {
  events = data;
  // console.log(events);
  renderDesktopEvents(); // call the render function after events are loaded
});
// originaly this was done with a hard coded list of events in this file

// ── Time helpers

// Converts a "HH:MM" string to total minutes from midnight.
// Used to calculate event positions and durations on the grid
function parseTime(timeStr) {
  const [h, m] = timeStr.split(':').map(Number);
  return h * 60 + m;
}

// Converts a "HH:MM" 24h string to a readable label like "9:00 am" or "2:30 pm".
// Used in the event card time display.
function formatTime(timeStr) {
  const [h, m] = timeStr.split(':').map(Number);
  const period = h < 12 ? 'am' : 'pm';
  const hour = h % 12 || 12;
  return `${hour}:${String(m).padStart(2, '0')} ${period}`;
}

// ── Event card builder
// Creates and returns a styled event card DOM element.
// The card is positioned absolutely inside its host cell and sized to span
// the correct number of rows based on the event duration.
function buildEventCard(event, heightPx) {
  const colors = COLOR_MAP[event.color] || COLOR_MAP.indigo; // default to indigo if color not found
  const timeLabel = `${formatTime(event.startTime)} – ${formatTime(event.endTime)}`; // e.g. "9:00 am – 10:30 am"

  // The card sits inside the grid cell using absolute positioning.
  // A small pad (left-0.5 / right-0.5 / top-0.5) keeps the grid lines visible around it.
  const card = document.createElement('div');
  card.className = [
    'absolute left-0.5 right-0.5 top-0.5 rounded-md border-l-4 overflow-hidden',
    'cursor-pointer transition-shadow hover:shadow-md select-none z-10', // TODO: we should add some on hover info here in futre
    colors.bg,
    colors.border,
  ].join(' ');
  card.style.height = `${heightPx - 4}px`; // subtract 4px to account for the top inset (otherwise overflows down to next grid)

  // Event title — always shown
  const title = document.createElement('p');
  title.className = `text-xs font-semibold leading-tight px-1.5 pt-1 truncate ${colors.text}`;
  title.textContent = event.title;
  card.appendChild(title);

  // Time label and Location - show only if card is big enough
  if (heightPx >= 40) {
    // location
    const location = document.createElement('p');
    location.className = ` text-xs leading-tight px-1.5 text-bold ${colors.text} opacity-75`;
    location.textContent = event.location;
    card.appendChild(location);
    // time label
    const time = document.createElement('p');
    time.className = `text-xs leading-tight px-1.5 ${colors.text} opacity-75`;
    time.textContent = timeLabel;
    card.appendChild(time);
  }

  return card;
}

// ── Render events onto the desktop grid
// The desktop grid is a flat 6-column CSS grid (1 time col + 5 day cols).
// We iterate every cell, figure out which day and hour it belongs to,
// and store it in a lookup map. Then for each event we find its cell and
// inject an absolutely positioned card that spans the event's full duration.
function renderDesktopEvents() {
  const grid = document.getElementById('desktop-grid');

  const cells = Array.from(grid.children);
  const cellsPerRow = 6; // column 0 = time labels, columns 1–5 = Mon–Fri

  // Build a map of "dayIndex-hourIndex" → cell element.
  // dayIndex: 0 = Mon, 1 = Tue, ... 4 = Fri
  // hourIndex: 0 = 07:00, 1 = 08:00, ... 11 = 06:00 pm
  const cellMap = {};
  cells.forEach((cell, i) => {
    const col = i % cellsPerRow;
    const row = Math.floor(i / cellsPerRow);
    if (col === 0) return; // skip the time label column
    cellMap[`${col - 1}-${row}`] = cell;
  });
  /*
    ^ This bit was a bit confusing but its like a python dict table. 
    We create a nice dictionary dictionary that maps the day and hour 
      index to the correct cell in the grid.
    Uncomment the console lof to see a nice table of the mapping in the console
  */
  // console.table(cellMap);

  // Measure the height of one cell from the DOM so we can size cards correctly.
  // This automatically adapts to whichever CSS breakpoint is active.
  const referenceCell = cellMap['0-0'];
  if (!referenceCell) return;
  const cellHeight = referenceCell.offsetHeight;

  // Get the ISO date strings for Mon–Fri of the current week.
  // Used to check which column each event belongs in.
  const weekDates = getWeekDates();

  // Place each event into the grid
  events.forEach((event) => {
    // Find which day column this event belongs to (0 = Mon … 4 = Fri)
    const dayIndex = weekDates.findIndex((d) => d === event.date);
    if (dayIndex === -1) return; // event is not in the current week — skip it

    // Find which row this event starts on, relative to the grid's start hour
    const startMinutes = parseTime(event.startTime);
    const endMinutes = parseTime(event.endTime);
    const hourIndex = Math.floor(startMinutes / 60) - GRID_START_HOUR;
    if (hourIndex < 0 || hourIndex >= GRID_TOTAL_SLOTS) return; // outside visible range

    //target cell is the cell that matches the indexs we just calculated
    const cell = cellMap[`${dayIndex}-${hourIndex}`];
    if (!cell) return;

    // Calculate card height: duration in hours × height of one cell in pixels
    const durationHours = (endMinutes - startMinutes) / 60;
    const cardHeight = durationHours * cellHeight;

    // Make the cell a positioning context so the absolute card sits inside it
    cell.style.position = 'relative';
    cell.style.overflow = 'visible'; // allow the card to overflow into rows below

    cell.appendChild(buildEventCard(event, cardHeight));
  });
}

// ── Date utility
// Returns an array of 5 ISO date strings [Mon, Tue, Wed, Thu, Fri]
// for the current calendar week.
// initialy i did this with a dictionary of monday: date,
// but this got annoying later so just 5 dates in an array is easier to work with.
function getWeekDates() {
  const today = new Date();
  const currentDay = today.getDay();
  let daysFromMonday; //decalre empty
  if (currentDay === 0) {
    // Sunday is 0, so we need to go back 6 days to get to Monday
    daysFromMonday = -6;
  } else {
    // For any other day, we calculate how many days to go back to get to Monday
    daysFromMonday = 1 - currentDay;
  }
  const monday = new Date(today);
  monday.setDate(today.getDate() + daysFromMonday); // Now we have the date for Monday of the current week

  const weekDates = [];
  for (let i = 0; i < 5; i++) {
    // Loop from 0 to 4 to get dates for Monday through Friday
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    weekDates.push(d.toISOString().slice(0, 10));
  }
  // console.log(weekDates); // Uncomment to see the generated week dates in the console
  return weekDates;
}

// ── Set calendar header dates
// Updates the page title ("Today, Wed March 11") and the five column headers
// (Mon 9, Tue 10, …). Today's column is highlighted in indigo.
function setCalendarDates() {
  const today = new Date();

  const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];

  // Update the "Today, Day Month Date" title at the top of the page
  const titleElement = document.getElementById('calendar-title');
  if (titleElement) {
    // Format: "Today, {Day}, {Moth} {dd}"
    titleElement.textContent = `Today, ${today.toLocaleString(undefined, { weekday: 'long' })}, ${today.toLocaleString(undefined, { month: 'long' })} ${today.getDate()}`;
  }

  // Update each of the five column header elements with the correct day and date.
  // Highlight today's column with indigo text.
  const weekDates = getWeekDates();
  weekDates.forEach((dateStr, i) => {
    const columnDate = new Date(dateStr);
    const columnElement = document.getElementById(`date-col-${i}`);
    if (columnElement) {
      columnElement.textContent = `${dayNames[i]} ${columnDate.getDate()}`;
      const isToday = dateStr === today.toISOString().slice(0, 10);
      columnElement.classList.toggle('text-indigo-600', isToday);
      columnElement.classList.toggle('text-gray-900', !isToday);
    }
  });
}

//-- Playing around with button
const new_eventbtn = document.getElementById('new-event-btn');
new_eventbtn.addEventListener('click', () => {
  alert('This button will open a form to create a new event. Coming soon!');
});

// innit
setCalendarDates();
