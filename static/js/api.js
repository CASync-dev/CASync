// ── Mock API module
// Simulates backend API calls using static JSON files.
//
// HOW TO USE
//   <script src="/static/js/api.js"></script>
//   api.getEvents().then(events => { ... });
//

const BASE_URL = '/static/data';

const api = {
  // GET /api/user/me — the logged-in user's profile
  getUser: () => fetch(`${BASE_URL}/user.json`).then((r) => r.json()),

  // GET /api/events — all calendar events for the current user
  getEvents: () => fetch(`${BASE_URL}/events.json`).then((r) => r.json()),

  // GET /api/friends — friends list, each with their events and online status
  getFriends: () => fetch(`${BASE_URL}/friends.json`).then((r) => r.json()),

  // GET /api/groups — groups the user belongs to, with members and events
  getGroups: () => fetch(`${BASE_URL}/groups.json`).then((r) => r.json()),
};
