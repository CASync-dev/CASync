// Schedule page — sets dynamic dates and renders events into the weekly calendar grid

// ── Grid constants
// These define the visible time range shown in the HTML grid.
// The grid runs from 07:00 am to 06:00 pm — that's 12 one-hour slots.
const GRID_START_HOUR = 7;
const GRID_TOTAL_SLOTS = 12;

// ── Color themes
// Each event has a color name (e.g. "blue"). This maps that name to the three
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
// Each event needs: id, title, date (YYYY-MM-DD), startTime, endTime (24h HH:MM), color.
// Dates are generated relative to the current week so events always appear on load.
/* 
  Eventually this will be parsed from icals but that will need the backend server
  This should be entirley overhauld, it works for testing visuals but doesnt actually handle the dates well
    nor does it handle multiple events on the same day, or overlapping events, etc.
  Colours should be defined dyunamicly based on subject in the futre
*/
const events = buildSampleEvents();

function buildSampleEvents() {
  // Find the Monday of the current week so we can anchor all event dates to it.
  const today = new Date();
  const currentDay = today.getDay(); // 0 = Sunday, 1 = Monday, ...
  const daysFromMonday = currentDay === 0 ? -6 : 1 - currentDay;
  const monday = new Date(today);
  monday.setDate(today.getDate() + daysFromMonday);

  // Helper: returns the ISO date string (YYYY-MM-DD) for a given offset from Monday.
  // e.g. weekDate(0) = Monday, weekDate(2) = Wednesday
  function weekDate(dayOffset) {
    const d = new Date(monday);
    d.setDate(monday.getDate() + dayOffset);
    return d.toISOString().slice(0, 10);
  }

  // Sample events mirriing my own schedlue for testin
  // Each subject has a consistent color across the week:
  return [
    // Monday
    {
      id: 1,
      title: 'Continental Philosophy',
      date: weekDate(0),
      startTime: '14:00',
      endTime: '15:00',
      color: 'rose',
    },
    {
      id: 2,
      title: 'Moral Theory',
      date: weekDate(0),
      startTime: '16:00',
      endTime: '18:00',
      color: 'amber',
    },

    // Tuesday
    {
      id: 3,
      title: 'Continental Philosophy',
      date: weekDate(1),
      startTime: '15:00',
      endTime: '16:00',
      color: 'rose',
    },
    {
      id: 4,
      title: 'Continental Philosophy',
      date: weekDate(1),
      startTime: '16:00',
      endTime: '18:00',
      color: 'rose',
    },

    // Wednesday
    {
      id: 5,
      title: 'Data Structures & Algorithms',
      date: weekDate(2),
      startTime: '14:00',
      endTime: '15:00',
      color: 'blue',
    },
    {
      id: 6,
      title: 'Moral Theory',
      date: weekDate(2),
      startTime: '15:00',
      endTime: '17:00',
      color: 'amber',
    },
    {
      id: 7,
      title: 'Agile Web Development',
      date: weekDate(2),
      startTime: '16:00',
      endTime: '18:00',
      color: 'green',
    },

    // Thursday
    {
      id: 8,
      title: 'Agile Web Development',
      date: weekDate(3),
      startTime: '12:00',
      endTime: '14:00',
      color: 'green',
    },

    // Friday
    {
      id: 9,
      title: 'Agile Web Development',
      date: weekDate(4),
      startTime: '10:00',
      endTime: '12:00',
      color: 'green',
    },
    {
      id: 10,
      title: 'Data Structures & Algorithms',
      date: weekDate(4),
      startTime: '11:00',
      endTime: '13:00',
      color: 'blue',
    },
  ];
}

// ── Time helpers

// Converts a "HH:MM" string to total minutes from midnight.
// Used to calculate event positions and durations numerically.
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
  const colors = COLOR_MAP[event.color] || COLOR_MAP.indigo;
  const timeLabel = `${formatTime(event.startTime)} – ${formatTime(event.endTime)}`;

  // The card sits inside the grid cell using absolute positioning.
  // A small inset (left-0.5 / right-0.5 / top-0.5) keeps grid lines visible around it.
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

  // Time label — only shown if the card is tall enough to fit it
  if (heightPx >= 40) {
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
  if (!grid) return;

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
function getWeekDates() {
  const today = new Date();
  const currentDay = today.getDay();
  const daysFromMonday = currentDay === 0 ? -6 : 1 - currentDay;
  const monday = new Date(today);
  monday.setDate(today.getDate() + daysFromMonday);

  return Array.from({ length: 5 }, (_, i) => {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    return d.toISOString().slice(0, 10);
  });
}

// ── Set calendar header dates
// Updates the page title ("Today, Wed March 11") and the five column headers
// (Mon 9, Tue 10, …). Today's column is highlighted in indigo.
function setCalendarDates() {
  const today = new Date();

  const monthNames = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December',
  ];
  const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'];

  // Update the "Today, Day Month Date" title at the top of the page
  const titleElement = document.getElementById('calendar-title');
  if (titleElement) {
    titleElement.textContent = `Today, ${dayNames[today.getDay() === 0 ? 6 : today.getDay() - 1]} ${monthNames[today.getMonth()]} ${today.getDate()}`;
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

// ── Initialise
// Run everything in order: dates first so the grid is labelled, then events.
setCalendarDates();
renderDesktopEvents();
