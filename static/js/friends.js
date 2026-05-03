// Temporary measure
const DEV_USERS = [
  'alice_wonder',
  'bob_builder',
  'charlie_chaplin',
  'diana_prince',
  'eve_online',
];

// Friends Search bar
document
  .getElementById('friend-search-input')
  .addEventListener('input', (e) => {
    // fo lowercase for stadnard search
    const query = e.target.value.toLowerCase();
    document.querySelectorAll('#friends-list li').forEach((li) => {
      const username = li.querySelector('p').textContent.toLowerCase();
      if (username.includes(query)) {
        li.classList.remove('hidden');
      } else {
        li.classList.add('hidden');
      }
    });
  });

function devsearchFriends() {
  const list = document.getElementById('friend-search-list');
  list.innerHTML = DEV_USERS.map(
    (u) => `
    <li class="flex items-center justify-between py-2 px-4 hover:bg-gray-100 rounded-md">
    <div class="flex items-center gap-3">
        <img src="https://placehold.co/200x200" class="h-8 w-8 rounded-full" />
        <span class="text-sm font-medium text-gray-800">${u}</span>
    </div>
    <button onclick="addFriend()" class="text-sm bg-green-600 text-white px-3 py-1 rounded-md hover:bg-green-700">Add</button>
    </li>`,
  ).join('');
  document.getElementById('friend-search-results').classList.remove('hidden');
}

// Handle displaying possible users to add
async function searchFriends() {
  let users;
  let results;
  // Reads CSRFtoken from token and sends with data.
  const token = document.querySelector('meta[name="csrf-token"]').content;
  const search = document.getElementById('user-search-input').value;
  if (search == '') {
    return;
  }
  try {
    const response = await fetch('/api/getusers', {
      method: 'POST',
      headers: { 'X-CSRFToken': token, 'Content-Type': 'application/json' },
      body: JSON.stringify({ search: search }),
    })
      .then((response) => response.json())
      .then((x) => {
        results = x;
      });
    // Debugging:
    users = results['results'];
  } catch (error) {
    console.error('Error:', error);
    return;
  }
  const list = document.getElementById('friend-search-list');
  if (users == 0) {
    // ie. no results
    list.innerHTML = '';
    const nores = document.createElement('li');
    nores.classList.add('flex', 'items-center', 'mx-auto');
    nores.innerText = 'No users found :( ';
    document.getElementById('friend-search-results').classList.remove('hidden');
    list.appendChild(nores);
    return;
  }

  // Like the dev vers, maps the response' user list to a list element
  // Ensure we add the user id to the button as a data attribute so we can send it with the friend request
  list.innerHTML = users
    .map(
      (u) => `
    <li class="flex items-center justify-between py-2 px-4 hover:bg-gray-100 rounded-md">
    <div class="flex items-center gap-3">
        <img src="https://placehold.co/200x200" class="h-8 w-8 rounded-full" />
        <span class="text-sm font-medium text-gray-800">${u.username}</span>
    </div>
    <button id="add-friend-btn-${u.id}" onclick="addFriend()" data-user-id="${u.id}" class="text-sm bg-green-600 text-white px-3 py-1 rounded-md hover:bg-green-700">Add</button>
    </li>`,
    )
    .join('');
  document.getElementById('friend-search-results').classList.remove('hidden');
  return;
}
// Sends a friend request to the requestfriend endpoint, with the username of the user to be added as a friend in the body.
function addFriend() {
  // Reads CSRFtoken from token and sends with data.
  const token = document.querySelector('meta[name="csrf-token"]').content;
  const userId = event.target.getAttribute('data-user-id');
  fetch('/api/requestfriend', {
    method: 'POST',
    headers: { 'X-CSRFToken': token, 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId }),
  })
    .then((response) => response.json())
    .then((data) => {
      // On success, disable the button and change text to "Request Sent"
      document.getElementById(`add-friend-btn-${userId}`).disabled = true;
      document.getElementById(`add-friend-btn-${userId}`).textContent =
        'Request Sent';
      document
        .getElementById(`add-friend-btn-${userId}`)
        .classList.remove('bg-green-600', 'hover:bg-green-700');
      document
        .getElementById(`add-friend-btn-${userId}`)
        .classList.add('bg-gray-400', 'cursor-not-allowed');
    })
    .catch((error) => {
      console.error('Error:', error);
    });
}

// Handle displaying a friends schedule in the modal
// offsetHeight returns 0 while the dialog is hidden, so card heights are wrong on first open.
// Re-render once the dialog becomes visible so cells have their real layout dimensions.
const scheduleModal = document.getElementById('friend-schedule-modal');
new MutationObserver(() => {
  if (scheduleModal.open) requestAnimationFrame(() => renderDesktopEvents());
}).observe(scheduleModal, { attributes: true, attributeFilter: ['open'] });

openFriendSchedule = (friendId, friendName) => {
  // reset the calendars data source and cache range
  calendarBaseUrl = `/api/events/${friendId}`;
  lastFetchedStart = null;
  lastFetchedEnd = null;
  // re-render the calendar with the new data source
  fetchAndRenderEvents();
  // set the modal title to the friends name
  document.getElementById('friend-schedule-title').textContent =
    `${friendName}'s Schedule`;
  // open the modal
  const modal = document.getElementById('friend-schedule-modal');
  modal.showModal();
};

function acceptFriendRequest(requestId) {
  const token = document.querySelector('meta[name="csrf-token"]').content;
  fetch('/api/acceptfriend', {
    method: 'POST',
    headers: { 'X-CSRFToken': token, 'Content-Type': 'application/json' },
    body: JSON.stringify({ request_id: requestId }),
  })
    .then((response) => response.json())
    .then((data) => {
      // On success, remove the friend request from the list
      document.getElementById(`friend-request-${requestId}`).remove();
    })
    .catch((error) => {
      console.error('Error:', error);
    });
}

function rejectFriendRequest(requestId) {
  const token = document.querySelector('meta[name="csrf-token"]').content;
  fetch('/api/rejectfriend', {
    method: 'POST',
    headers: { 'X-CSRFToken': token, 'Content-Type': 'application/json' },
    body: JSON.stringify({ request_id: requestId }),
  })
    .then((response) => response.json())
    .then((data) => {
      // On success, remove the friend request from the list
      document.getElementById(`friend-request-${requestId}`).remove();
    })
    .catch((error) => {
      console.error('Error:', error);
    });
}

function removeFriend(friendId) {
  // open the confirmation dialog
  const dialog = document.getElementById('remove-confirmation');
  dialog.showModal();
  // store the friendId in a data attribute on the confirm button so we can access it in the confirmRemoveFriend function
  document
    .getElementById('confirm-delete-btn')
    .setAttribute('data-friend-id', friendId);
}

function confirmRemoveFriend() {
  const token = document.querySelector('meta[name="csrf-token"]').content;
  const friendId = document
    .getElementById('confirm-delete-btn')
    .getAttribute('data-friend-id');
  fetch('/api/removefriend', {
    method: 'POST',
    headers: { 'X-CSRFToken': token, 'Content-Type': 'application/json' },
    body: JSON.stringify({ friend_id: friendId }),
  })
    .then((response) => response.json())
    .then((data) => {
      // On success, remove the friend from the list and close the dialog
      document.getElementById(`friend-${friendId}`).remove();
      document.getElementById('remove-confirmation').close();
    })
    .catch((error) => {
      console.error('Error:', error);
    });
}
