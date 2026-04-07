// Schedule page — sets dynamic dates and renders events into the weekly calendar grid
// ── Constants

// Grid Constants: adjust these if you change the grid layout in the HTML/CSS (maybe dynamic later)
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
  orange: {
    bg: 'bg-orange-100',
    border: 'border-orange-500',
    text: 'text-orange-800',
  },
  red: { bg: 'bg-red-100', border: 'border-red-500', text: 'text-red-800' },
  purple: {
    bg: 'bg-purple-100',
    border: 'border-purple-500',
    text: 'text-purple-800',
  },
  gray: { bg: 'bg-gray-100', border: 'border-gray-500', text: 'text-gray-800' },
};
event_color_map = {};

// ── Event data
// This is the list of events that get rendered onto the calendar.
// At the moment we just call the API to get all events and render them
// Should be smarter later, idk if here or in the api request
// We
let user_id = 1; // TODO: get this from the server or auth context instead of hardcoding
// Will also have to change it to retrieve other users events when we have that functionality
fetch(`/api/events/${user_id}`)
  .then((response) => response.json())
  .then((data) => {
    events = data;
    renderDesktopEvents(); // render events after loading
  })
  .catch((error) => {
    console.error('Error loading events:', error);
  });

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

// Get a list of ISO date strings for Monday through Friday of the current week, adjusted by weekOffset.
function getWeekDates() {
  // Always start from the real current date so navigation never accumulates errors
  const base = new Date();
  const currentDay = base.getDay();
  // Calculate how many days to shift back to get to Monday (or forward if it's Sunday)
  const daysFromMonday = currentDay === 0 ? -6 : 1 - currentDay;

  // Find Monday of the real current week, then shift by weekOffset weeks
  const monday = new Date(base);
  monday.setDate(base.getDate() + daysFromMonday + weekOffset * 7);

  // Generate ISO date strings for Monday through Friday of this week
  const weekDates = [];
  for (let i = 0; i < 5; i++) {
    // Loop from 0 to 4 to get dates for Monday through Friday
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    // Use local date parts to avoid UTC timezone shifting the date
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    weekDates.push(`${year}-${month}-${day}`);
  }
  // console.log(weekDates); // Uncomment to see the generated week dates in the console
  return weekDates;
}

// -- State tracker
// A var to track how many week are offset from the real current week.
let weekOffset = 0;
// The list of events loaded from the API. Each event should have at least:
// { title, date (ISO string), startTime ("HH:MM"), endTime ("HH:MM"), location, subject_code }
let events = [];

// ── Event card builder
// Creates and returns a styled event card DOM element.
// The card is positioned absolutely inside its host cell and sized to span
// the correct number of rows based on the event duration.
function buildEventCard(event, heightPx, id) {
  event_class = event.title.split(',')[0].toLowerCase(); // get the first part of the title as the class (e.g. "CS 101, Lecture" → "cs 101")
  if (!event_color_map[event_class]) {
    // If this class doesn't have a color assigned yet, assign the next available color from COLOR_MAP
    const usedColors = new Set(Object.values(event_color_map));
    const availableColors = Object.keys(COLOR_MAP).filter(
      // find the first color in COLOR_MAP that hasn't been used yet
      (color) => !usedColors.has(color),
    );
    event_color_map[event_class] = availableColors[0] || 'gray'; // default to gray if we run out of colors, later we can do generating new colors
  }
  const timeLabel = `${formatTime(event.startTime)} – ${formatTime(event.endTime)}`; // e.g. "9:00 am – 10:30 am"

  // The card sits inside the grid cell using absolute positioning.
  // A small pad (left-0.5 / right-0.5 / top-0.5) keeps the grid lines visible around it.
  const card = document.createElement('div');
  card.id = id;
  colors = COLOR_MAP[event_color_map[event_class]];
  card.className = [
    'absolute left-0.5 right-0.5 top-0.5 rounded-md border-l-4 overflow-hidden',
    'cursor-pointer transition-shadow hover:shadow-md select-none z-10', // TODO: we should add some on hover info here in futre
    colors.bg,
    colors.border,
  ].join(' ');
  card.style.height = `${heightPx - 4}px`;
  // we can store the caluclated hight in a data attribute on the div so we can restore it on collapsed behvaiour later
  card.dataset.collapsedHeight = `${heightPx - 4}px`;
  // Store the collapsed height in a data attribute so we can restore it when collapsing  // Event title — always shown
  const title = document.createElement('p');
  title.className = `text-xs font-semibold leading-tight px-1.5 pt-1 truncate ${colors.text}`;
  title.textContent = event.title;
  card.appendChild(title);

  const time = document.createElement('p');
  time.className = `text-xs leading-tight px-1.5 ${colors.text} opacity-75`;
  time.textContent = timeLabel;
  card.appendChild(time);
  // Location - show only if card is big enough, or if the location is exceptionay large, requrie an even bigger card
  if ((heightPx >= 75 && event.location.length <= 50) || heightPx >= 100) {
    const location = document.createElement('p');
    location.className = `text-xs leading-tight px-1.5 text-bold ${colors.text} opacity-75`;
    location.textContent = event.location;
    card.appendChild(location);
  }

  // Extra details — hidden until the card is expanded
  const details = document.createElement('div');
  details.className = 'event-details hidden mt-1 px-1.5 pb-1 ';
  details.innerHTML = `
    <p class="text-xs ${colors.text} opacity-60 font-mono">This is where there will be some more info about the event like who else is in class.</p>
  `;
  card.appendChild(details);

  return card;
}

// ── Render events onto the desktop grid
// The desktop grid is a flat 6-column CSS grid (1 time col + 5 day cols).
// We iterate every cell, figure out which day and hour it belongs to,
// and store it in a lookup map. Then for each event we find its cell and
// inject an absolutely positioned card that spans the event's full duration.
function renderDesktopEvents() {
  const grid = document.getElementById('desktop-grid');

  // Clear any previously rendered event cards before re-rendering
  grid.querySelectorAll('[id^="event-"]').forEach((item) => item.remove());

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

  // we initialise some counters to store all the elements we have placed
  // so we can check if they overlapp
  number_of_events_counter = 0;
  const placed_cards = [];

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
    if (!cell) return; // something went wrong with our cell mapping

    // Calculate card height: duration in hours × height of one cell in pixels
    const durationHours = (endMinutes - startMinutes) / 60;
    const cardHeight = durationHours * cellHeight;

    // Make the cell a positioning context so the absolute card sits inside it
    cell.style.position = 'relative';
    cell.style.overflow = 'visible'; // allow the card to overflow into rows below

    // Create and insert the event card into the cell
    card = buildEventCard(
      event,
      cardHeight,
      `event-${number_of_events_counter}`,
    );
    // Store the day index in a data attribute on the card for later use when expanding
    card.dataset.col = dayIndex; // 0=Mon … 4=Fri
    cell.appendChild(card);

    // add them to the counters for second pass
    placed_cards.push({ card, dayIndex, startMinutes, endMinutes });
    number_of_events_counter++;
  });

  // Second Pass:
  // Check if the event has an item underneath it, if so we pad to the left slightly
  placed_cards.forEach(({ card, dayIndex, startMinutes }) => {
    // we check if there is any other card that starts above this one, but ends after this one starts (i.e. overlaps from above)
    const hasOverlapFromAbove = placed_cards.some((other) => {
      const isSameDay = other.dayIndex === dayIndex; // only check events in the same column
      const isDifferentCard = other.card !== card; // skip self
      const otherStartedFirst = other.startMinutes < startMinutes; // only check events that start above this one
      const otherStillActiveAtStart = other.endMinutes > startMinutes; // only check events that are still active when this one start
      // check all of the above conditions
      return (
        isDifferentCard &&
        isSameDay &&
        otherStartedFirst &&
        otherStillActiveAtStart
      );
    });
    if (hasOverlapFromAbove) {
      card.style.left = '0.5rem'; // push this card right so the card behind it is visible
    }
  });
}

// ── Set calendar header dates
// Updates the page title ("Today, Wed March 11") and the five column headers
// (Mon 9, Tue 10, …). Today's column is highlighted in indigo.
function setCalendarDates() {
  /*
    
  */
  const now = new Date(); // real current date, for the title and today-highlight

  const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];

  // Update the "Today, Day Month Date" title at the top of the page
  const titleElement = document.getElementById('calendar-title');

  // Helper function to format a date as "Day Month Date" with customizable month style
  const fmt = (date, monthStyle) =>
    // e.g. "Wednesday March 11" or "Wed Mar 11"
    `${dayNames[date.getDay() - 1]} ${date.toLocaleString('default', { month: monthStyle })} ${date.getDate()}`;

  // Shorter format for column headers, e.g. "Mar 11"
  const fmtShort = (date) =>
    // e.g. "Mar 11"
    `${date.toLocaleString('default', { month: 'short' })} ${date.getDate()}`;

  // Helper to get a date offset by a certain number of days
  // from toda. used for the title when showing last/next week
  const offsetDate = (days) => {
    const d = new Date(now);
    d.setDate(now.getDate() + days);
    return d;
  };

  // Show relative week label for ±1 week, or a date range for anything further
  if (weekOffset === 0) {
    // if on the current week, show "Today, Month D"
    titleElement.textContent = `Today, ${fmt(now, 'long')}`;
  } else if (weekOffset === -1) {
    // if on the previous week, show "Last Week, Mon D"
    titleElement.textContent = `Last Week, ${fmt(offsetDate(-7), 'long')}`;
  } else if (weekOffset === 1) {
    // if on the next week, show "Next Week, Mon D"
    titleElement.textContent = `Next Week, ${fmt(offsetDate(7), 'long')}`;
  } else {
    // if on any other week, show a date range like "Mar 1 - Mar 5"
    const weekDates = getWeekDates();
    const startDate = new Date(weekDates[0]);
    const endDate = new Date(weekDates[4]);
    titleElement.textContent = `${fmtShort(startDate)} - ${fmtShort(endDate)}`;
  }

  // Update each of the five column header elements with the correct day and date.
  // Highlight today's column with indigo text.
  const weekDates = getWeekDates();
  weekDates.forEach((dateStr, i) => {
    const columnDate = new Date(dateStr);
    const columnElement = document.getElementById(`date-col-${i}`);
    if (columnElement) {
      columnElement.textContent = `${dayNames[i]} ${columnDate.getDate()}`;
      const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
      const isToday = dateStr === todayStr;
      columnElement.classList.toggle('text-indigo-600', isToday);
      columnElement.classList.toggle('text-gray-900', !isToday);
    }
  });
}

// -- Expand Event Items
// When content is loaded, ad a click lisnter that listens for clicks on any event card.
document.addEventListener('DOMContentLoaded', () => {
  document.addEventListener('click', (event) => {
    // Check if the id is event-#. All event have an id and a unique number
    const card = event.target.closest('[id^="event-"]');
    if (!card) return;

    //
    const isExpanded = card.classList.contains('expanded');
    const details = card.querySelector('.event-details');

    if (isExpanded) {
      // Collapse: restore original size and position
      card.classList.remove('expanded', 'shadow-lg', 'z-20');
      card.classList.add('overflow-hidden');
      card.style.height = card.dataset.collapsedHeight;
      // reset any style tags
      card.style.minHeight = '';
      card.style.width = '';
      card.style.left = '';
      card.style.right = '';
      card.style.transform = '';
      details.classList.add('hidden');
      card.children[0].classList.remove('text-wrap');
    } else {
      // Expand: auto height (but never shrink below collapsed size), fixed width anchored left or right based on column
      card.classList.add('expanded', 'shadow-lg', 'z-20');
      card.classList.remove('overflow-hidden');
      // Ensure the card doesn't shrink below its original height when expanding
      card.style.minHeight = card.dataset.collapsedHeight;
      card.style.height = 'auto';
      card.style.width = '280px';
      card.children[0].classList.add('text-wrap');
      // Use the stored day index to determine expand direction:
      //   if it's in the right-side columns, we anchor to the right edge and expand leftward,
      //   if it's in the left-side columns,
      //   we anchor to the left edge and expand rightward.
      const col = parseInt(card.dataset.col ?? '0');
      if (1 <= col && col <= 3) {
        // middle columns 1,2,3
        // middle column: expand centered form the middle, with some padding on both sides
        card.style.left = '50%';
        card.style.transform = 'translateX(-50%)';
        card.style.right = '';
      } else if (col >= 3) {
        // right-side columns: expand leftward'
        card.style.right = '2px';
        card.style.left = 'auto';
      } else {
        // left-side columns: expand rightward
        card.style.left = '2px';
        card.style.right = 'auto';
      }
      details.classList.remove('hidden');
    }
  });
});
//-- Playing around with button
document.getElementById('new-event-btn').addEventListener('click', () => {
  alert('This button will open a form to create a new event. Coming soon!');
});

function updateTodayButton() {
  // Hide the "Today" button if we're already on the current week, show it otherwise
  if (weekOffset === 0) {
    document.getElementById('btn-today').classList.add('hidden');
  } else {
    document.getElementById('btn-today').classList.remove('hidden');
  }
}

document.getElementById('btn-last-week').addEventListener('click', () => {
  weekOffset--;
  setCalendarDates();
  renderDesktopEvents();
  updateTodayButton();
});

document.getElementById('btn-today').addEventListener('click', () => {
  weekOffset = 0;
  setCalendarDates();
  renderDesktopEvents();
  updateTodayButton();
});

document.getElementById('btn-next-week').addEventListener('click', () => {
  weekOffset++;
  setCalendarDates();
  renderDesktopEvents();
  updateTodayButton();
});

// innit
setCalendarDates();
