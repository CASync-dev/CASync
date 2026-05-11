// simple function to update the time and date on the dashboard every second
function updateTime() {
  // Get the current date and time each time this runs
  const now = new Date();

  // Update the day and date text on the page
  document.getElementById("day").innerText = now.toLocaleDateString("en-US", {
    weekday: "long",
  });
  document.getElementById("current-date").innerText = now.toLocaleDateString(
    "en-US",
    { month: "long", day: "numeric", year: "numeric" },
  );

  // Format the time into hour/minute and AM/PM parts
  let time = now.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });
  let timeParts = time.split(" ");

  // Update the time and period separately
  document.getElementById("time").innerText = timeParts[0] ?? "";
  document.getElementById("period").innerText = timeParts[1] ?? "";
}

// dynamic stuff for the calendar events -------------------------------------

// craft the url for fetching events: format is /api/events/me?start=2026-05-06&end=2026-05-07
function getCalendarBaseUrl() {
  let apiUrl = "/api/events/me";
  const now = new Date();

  const fmt = (d) => d.toLocaleDateString("en-CA");
  apiUrl += `?start=${fmt(now)}&end=${fmt(now)}`;

  return apiUrl;
}

//  GET /api/events/me?start=2026-05-06&end=2026-05-07
let events = null;
async function loadEvents() {
  try {
    const res = await fetch(getCalendarBaseUrl());
    if (!res.ok) throw new Error(res.statusText);
    events = await res.json(); // store it here
    // renderCalendar(events);
    return events;
  } catch (err) {
    console.error("fetch error", err);
  }
}

// helper: parse "HH:MM" to minutes since midnight
function parseTimeToMinutes(hhmm = "00:00") {
  const [h, m] = hhmm.split(":").map(Number);
  return (h || 0) * 60 + (m || 0);
}

/*
    {
        "1": {
            "events": {
                "1": {
                    "title": "Event Title",
                    "description": "Event Description",
                    "date": "2024-07-01",
                    "startTime": "14:00",
                    "endTime": "15:00",
                    "user_id": 1,
                    "username": "exampleuser",
                    "location": "Event Location",
                    "color": "indigo",
                    "ical_id": null,
                    "ical_uid": null,
                    "id": 1
                },
                ...
*/

// process raw API JSON into useful structures
function processEvents(eventsData) {
  if (!eventsData) return { flat: [], byDate: {} };

  // 1) flatten all users' events into an array
  const flat = Object.values(eventsData)
    .flatMap((user) => Object.values(user.events))
    .map((e) => {
      const dateISO = e.date; // e.g. "2026-05-06"
      const start = e.startTime ?? e.start_time ?? e.start ?? "00:00";
      const end = e.endTime ?? e.end_time ?? e.end ?? "00:00";
      return {
        ...e,
        dateISO,
        dateObj: new Date(dateISO + "T00:00"),
        startMinutes: parseTimeToMinutes(start),
        endMinutes: parseTimeToMinutes(end),
      };
    })
    .sort((a, b) => a.startMinutes - b.startMinutes);

  // 2) group by date and sort each day's events by start time
  const byDate = flat.reduce((acc, ev) => {
    (acc[ev.dateISO] ??= []).push(ev);
    return acc;
  }, {});
  Object.values(byDate).forEach((arr) =>
    arr.sort((a, b) => a.startMinutes - b.startMinutes),
  );

  return { flat, byDate };
}

// Convert 24-hour time (HH:MM) to 12-hour format with AM/PM
function formatHHMM(hhmm = "00:00") {
  const [h, m] = (hhmm || "00:00").split(":").map(Number);
  const period = (h || 0) < 12 ? "AM" : "PM";
  const hour = (h || 0) % 12 || 12;
  return `${hour}:${String(m || 0).padStart(2, "0")} ${period}`;
}

// Convert minutes to human-readable time remaining (e.g., "45 minutes" or "1:30 minutes")
// for the big card event in minutes until the next event starts
function formatTime(totalMinutes) {
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  if (hours === 0 && minutes > 0) return `${minutes} minutes`;
  if (minutes === 0 && hours > 0) return `${hours} hour`;
  if (minutes === 0 && hours === 0) return `RIGHT NOW`;
  return `${hours}:${String(minutes).padStart(2, "0")} minutes`;
}

// function for renderign the big card on the dashboard with the next upcoming event
function bigCard(nextEvent) {
  const bigCardEl = document.getElementById("big-card");
  if (!bigCardEl) return;

  if (!nextEvent) {
    bigCardEl.innerHTML = '<p class="text-gray-600">No upcoming events.</p>';
    return;
  }

  const now = new Date();
  const nowMinutes = now.getHours() * 60 + now.getMinutes();
  let minutesUntil = nextEvent.startMinutes - nowMinutes;
  if (minutesUntil < 0) minutesUntil = 0; // in case the event is currently happening

  bigCardEl.innerHTML = `
      <h3 class="text-4xl font-medium text-dark space-y-4 mb-4">
              Next Event:
            </h3>
      <h4 class="text-3xl text-dark space-y-4 mb-4">
          in <span class="text-blue-600">${formatTime(minutesUntil)}</span> at ${formatHHMM(nextEvent.startTime ?? nextEvent.start_time)}
      </h4>
      <span class="text-3xl flex-1">${nextEvent.title}</span>
      <span class="text-lg text-gray-500 shrink-0">${formatHHMM(nextEvent.startTime ?? nextEvent.start_time)} – ${formatHHMM(nextEvent.endTime ?? nextEvent.end_time)}</span>
      ${nextEvent.going === false ? `<span class="text-lg text-red-500 shrink-0">[Not Going]</span>` : `<span class="text-lg text-gray-500 shrink-0">${nextEvent.location ? `@ ${nextEvent.location}` : ""}</span>`}
      
      <div class="flex"><!-- avatars --></div>
  `;
}

//renders events in the dashboard - specifically the next event and the list of today's sub events in the bottom left panel
function renderDashboardEvents(processed) {
  // put the username in the header (just take it from any event, since they should all be the same user)
  // could be an easier way to do it with ajax but it would give me <user tehei>

  // render the list of today's sub events in the bottom left panel
  const container = document.getElementById("dashboard-sub-events");
  if (!container) return;
  container.innerHTML = "";
  const todayISO = new Date().toISOString().slice(0, 10);
  const todays = processed.byDate[todayISO] || [];

  let events = [];
  const now = new Date();
  const nowMinutes = now.getHours() * 60 + now.getMinutes();

  // find the events that are still upcoming (if there is 5 min left of the class then display the next one) and put them in the events array
  for (const ev of processed.flat) {
    // if we are 10 mins past the start of the event dont up it in the list
    if (ev.startMinutes > nowMinutes - 10) {
      events.push(ev);
    }
  }
  events = events.slice(0, 5); // limit to 5 events for performance and to avoid overwhelming the user
  // call function to render data for the big card, or clear it if nothing is left
  if (events.length > 0) {
    bigCard(events[0]);
  } else {
    bigCard(null);
  }

  if (todays.length - 1 <= 0) {
    container.innerHTML =
      '<p class="text-sm text-gray-600">All done! No more events today.</p>';
    return;
  }
  events.slice(1).forEach((ev) => {
    const el = document.createElement("div");
    el.className = "flex items-center bg-slate-200 rounded-2xl p-6 gap-4";
    el.innerHTML = `
              <span class="text-xl font-medium flex-1"
                >${ev.title}</span
              >
              <span class="text-lg text-gray-500 w-50 text-right shrink-0"
                >${formatHHMM(ev.startTime ?? ev.start_time)} – ${formatHHMM(ev.endTime ?? ev.end_time)}</span
              >
              <div class="flex"><!-- avatars --></div>
    `;
    container.appendChild(el);
  });
}

let processedEvs = null;

// Every second — clock only
setInterval(updateTime, 1000);

// Every minute — re-render cards (handles event transitions)
setInterval(() => {
  if (processedEvs) renderDashboardEvents(processedEvs);
}, 60 * 1000);

// Every 5 minutes — re-fetch from API (handles new/changed events)
setInterval(
  async () => {
    const fresh = await loadEvents();
    processedEvs = processEvents(fresh);
    renderDashboardEvents(processedEvs);
  },
  5 * 60 * 1000,
);

// run once immediately on load
updateTime();
loadEvents().then((events) => {
  processedEvs = processEvents(events);
  renderDashboardEvents(processedEvs);
});
