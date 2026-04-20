// ── API module
// Calls Flask backend routes defined in app.py.
//
// HOW TO USE
//   <script src="/static/js/api.js"></script>
//   api.getEvents().then(events => { ... });
//

const api = {
  // GET /api/user — the logged-in user's profile - obviosuly dont work rn
  getUser: () => fetch("/api/user").then((r) => r.json()),

  // GET /api/events — all calendar events for the current user
  getEvents: () => fetch("/api/events").then((r) => r.json()),
};
