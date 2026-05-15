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

// ----------------------dynamic stuff for the friends list -------------------------------------

// craft the url for fetching events: format is /api/friends_status?now
function getFriendsBaseUrl() {
  // Send the real UTC instant (e.g. "2024-06-30T21:48:00.000Z"). The server
  // compares this against event times stored as naive UTC.
  return `/api/friendsstatus?now=${new Date().toISOString()}`;
}

async function getFriends_status() {
  let friends_status = null;
  try {
    const res = await fetch(getFriendsBaseUrl());
    if (!res.ok) throw new Error(res.statusText);
    friends_status = await res.json(); // store it here
    // renderCalendar(events);
    return friends_status;
  } catch (err) {
    console.error("fetch error", err);
  }
}

function displayTimeTillNextClass(mins) {
  // handle edge cases first
  if (mins === null || mins === undefined) return "No more classes today";
  if (mins < 0) return "In class, Ending in " + formatTime(-mins);

  // convert minutes to hours and minutes
  const h = Math.floor(mins / 60);
  const m = mins % 60;

  const parts = [];
  // handle pluralization, add "s" if not 1
  if (h > 0) parts.push(`${h} hr${h !== 1 ? "s" : ""}`);
  if (m > 0) parts.push(`${m} min${m !== 1 ? "s" : ""}`);
  if (parts.length === 0) return "Next class starting now";

  return `Next class in ${parts.join(" ")}`;
}

function renderFriendsStatus(friends_status) {
  const container = document.getElementById("friends-list");
  if (!container) return;
  container.innerHTML = "";

  if (!Array.isArray(friends_status) || friends_status.length === 0) {
    container.innerHTML =
      '<p class="text-sm text-gray-600">No friends :( add some friends in the friends section.</p>';
    return;
  }
  let isfree = false;
  for (const friend of friends_status) {
    if (friend.status === "offline") continue;
    isfree = true;

    const li = document.createElement("li");
    li.className =
      "py-4 flex items-center bg-blue-600 justify-between rounded-2xl mb-2 px-3 hover:ring-1 hover:shadow shadow-md ring-white transition duration-200";
    li.innerHTML = `
      <div class="flex items-center ">
        <img class="h-15 w-15 rounded-full" src="${friend.avatar_url}" alt="${friend.username}'s avatar" />
        <div class="ml-4">
          <p class="text-sm font-medium text-white">${friend.username}</p>
          <p class="hidden sm:block text-sm text-white">${friend.email}</p>
        </div>
      </div>

      <p class=" px-3 py-2 text-white text-sm sm:text-base">
        ${displayTimeTillNextClass(friend.minutes_until_next)}
      </p>
    `;
    container.appendChild(li);
  }
  if (!isfree) {
    container.innerHTML =
      '<p class="text-sm text-gray-600">No friends are free.</p>';
  }
}

// -------------------- dynamic stuff for the calendar events -------------------------------------

// craft the url for fetching events: format is /api/events/me?start=2026-05-06&end=2026-05-07
function getCalendarBaseUrl() {
  let apiUrl = "/api/events/me";
  const now = new Date();

  const fmt = (d) => d.toLocaleDateString("en-CA");
  apiUrl += `?start=${fmt(now)}&end=${fmt(now)}`;

  return apiUrl;
}

//  GET /api/events/me?start=2026-05-06&end=2026-05-07
async function loadEvents() {
  let events = null;
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

let COLOR_MAP = {
  indigo: {
    bg: "bg-indigo-100",
    border: "border-indigo-500",
    text: "text-indigo-800",
  },
  blue: { bg: "bg-blue-100", border: "border-blue-500", text: "text-blue-800" },
  green: {
    bg: "bg-green-100",
    border: "border-green-500",
    text: "text-green-800",
  },
  rose: { bg: "bg-rose-100", border: "border-rose-500", text: "text-rose-800" },
  amber: {
    bg: "bg-amber-100",
    border: "border-amber-500",
    text: "text-amber-800",
  },
  orange: {
    bg: "bg-orange-100",
    border: "border-orange-500",
    text: "text-orange-800",
  },
  red: { bg: "bg-red-100", border: "border-red-500", text: "text-red-800" },
  purple: {
    bg: "bg-purple-100",
    border: "border-purple-500",
    text: "text-purple-800",
  },
  gray: { bg: "bg-gray-100", border: "border-gray-500", text: "text-gray-800" },
  yellow: {
    bg: "bg-yellow-100",
    border: "border-yellow-500",
    text: "text-yellow-800",
  },
};

// process raw API JSON into useful structures
function processEvents(eventsData) {
  if (!eventsData) return { flat: [], byDate: {} };

  // The API gives us full ISO datetimes for startTime/endTime. We pull out the
  // pieces we use elsewhere on the dashboard: the local date (YYYY-MM-DD) and
  // the minutes-since-midnight for the start and end of the event.
  const flat = Object.values(eventsData)
    .flatMap((user) => Object.values(user.events))
    .map((e) => {
      const startDate = new Date(e.startTime);
      const endDate = new Date(e.endTime);
      const yyyy = startDate.getFullYear();
      const mm = String(startDate.getMonth() + 1).padStart(2, "0");
      const dd = String(startDate.getDate()).padStart(2, "0");
      const dateISO = `${yyyy}-${mm}-${dd}`;
      const startHM = `${String(startDate.getHours()).padStart(2, "0")}:${String(startDate.getMinutes()).padStart(2, "0")}`;
      const endHM = `${String(endDate.getHours()).padStart(2, "0")}:${String(endDate.getMinutes()).padStart(2, "0")}`;
      return {
        ...e,
        // Replace ISO startTime/endTime with HH:MM so the renderers below stay simple.
        startTime: startHM,
        endTime: endHM,
        dateISO,
        dateObj: new Date(dateISO + "T00:00"),
        startMinutes: startDate.getHours() * 60 + startDate.getMinutes(),
        endMinutes: endDate.getHours() * 60 + endDate.getMinutes(),
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
  return `${hours}:${String(minutes).padStart(2, "0")} hours`;
}

// function for renderign the big card on the dashboard with the next upcoming event
function bigCard(nextEvent) {
  const bigCardEl = document.getElementById("big-card");
  if (!bigCardEl) return;

  if (!nextEvent) {
    bigCardEl.innerHTML =
      '<p class="text-gray-600">All done! No more events today.</p>';
    return;
  }

  const now = new Date();
  const nowMinutes = now.getHours() * 60 + now.getMinutes();
  let minutesUntil = nextEvent.startMinutes - nowMinutes;
  if (minutesUntil < 0) minutesUntil = 0; // in case the event is currently happening

  const startTime = formatHHMM(nextEvent.startTime ?? nextEvent.start_time);
  const endTime = formatHHMM(nextEvent.endTime ?? nextEvent.end_time);

  const evStart = nextEvent.startMinutes;
  const evEnd = nextEvent.endMinutes;
  const durationMinutes = Math.max(0, evEnd - evStart);

  const colors = COLOR_MAP[ev.color] ?? COLOR_MAP.gray;

  const dMin = Math.max(0, Math.round(durationMinutes || 0));
  const dH = Math.floor(dMin / 60);
  const dR = dMin % 60;
  let durationLabel = "";
  if (dH > 0) durationLabel += `${dH} hr${dH !== 1 ? "s" : ""}`;
  if (dR > 0) durationLabel += (durationLabel ? " " : "") + `${dR} min`;
  if (!durationLabel) durationLabel = `${dMin} min`;

  const locationOrStatus =
    nextEvent.going === false
      ? `<span class="text-lg text-red-500 shrink-0">Not Going</span>`
      : `<span class="text-lg text-gray-500 shrink-0">${nextEvent.location ? `@ ${nextEvent.location}` : ""}</span>`;

  // build the header time label: show "IN X" when upcoming, but just "RIGHT NOW" when ongoing
  const timeLabel =
    minutesUntil === 0
      ? `<span class="text-blue-600">RIGHT NOW</span>`
      : `IN <span class="ml-2 text-blue-600">${formatTime(minutesUntil)}</span>`;

  bigCardEl.innerHTML = `
    <div class="flex items-center justify-between gap-4 mb-2">
      <h3 class="text-lg font-medium text-gray-500">NEXT EVENT</h3>
      <p class="inline-flex items-center rounded-full bg-blue-50 px-3 py-1 text-lg text-gray-700 shrink-0">${timeLabel}</p>
    </div>
    <h2 class="text-4xl flex-1 mb-2">${nextEvent.title}</h2>
    <p class="text-xl text-gray-500 space-y-4 mb-4">
       Starts at ${startTime} and ends at ${endTime} <br />
      <span class="text-lg text-gray-500 shrink-0 bg-slate-200 rounded-2xl p-2">${durationLabel}</span>
      <span class="text-lg text-gray-500 shrink-0 bg-slate-200 rounded-2xl p-2">${locationOrStatus}</span>
    </p>
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
  // Build the key from local date parts to match how processEvents keys byDate;
  const d = new Date();
  const todayISO = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
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

  // call function to render data for the big card, or clear it if nothing is left
  if (events.length > 0) {
    bigCard(events[0]);
  } else {
    bigCard(null);
  }

  if (todays.length - 1 <= 0) {
    container.innerHTML = "";
    return;
  }
  events.slice(1).forEach((ev) => {
    const colors = COLOR_MAP[ev.color] ?? COLOR_MAP.gray;
    el.className = `flex items-center ${colors.bg} ${colors.border} p-6 rounded-2xl gap-4`;
    el.innerHTML = `
    <span class="text-xl ${colors.text} font-medium flex-1">${ev.title}</span>
    <span class="text-lg w-50 ${colors.text} text-center shrink-0  rounded-2xl px-2 py-1 leading-none">
      ${formatHHMM(ev.startTime ?? ev.start_time)} – ${formatHHMM(ev.endTime ?? ev.end_time)}
    </span>
    <div class="flex"></div>
  `;
    container.appendChild(el);
  });
}

let processedEvs = null;

// Every second — clock only
setInterval(updateTime, 1000);

// Every minute — re-render cards (handles event transitions)
setInterval(async () => {
  if (processedEvs) renderDashboardEvents(processedEvs);
  const status = await getFriends_status();
  renderFriendsStatus(status);
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
// run once friends status immediately on load
(async () => {
  const status = await getFriends_status();
  renderFriendsStatus(status);
})();
