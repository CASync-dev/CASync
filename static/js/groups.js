// Variables
let groupname = "My Group";
let grouplist = [];

// Functions for Group Dialog Modal
function loadCreateGroup() {
  const x = document.getElementById("create-group");
  x.showModal();
}
function closeLoadCreateGroup() {
  const x = document.getElementById("create-group");
  x.close();
}

// Functions for Friends Dialog Modal
function loadSelectFriends() {
  const x = document.getElementById("create-group");
  groupname = document.getElementById("group-name-input").value;
  x.close();
  const y = document.getElementById("select-friend");
  y.showModal();
  document.getElementById("gname").innerText = groupname;
}
function closeLoadSelectFriends() {
  const x = document.getElementById("select-friend");
  // Reset all saved values.
  groupname = "";
  grouplist = [];
  x.close();
}

// TODO: Remember to actually change this later so that groups will show up on page
// Dev function to check data
function testSubmit() {
  alert(groupname);
  alert(grouplist);
}

function submitGroupCreation() {
  let url = "/api/group/create";
  fetch(url, {
    method: "POST",
    body: JSON.stringify({ name: groupname, list: grouplist }),
  });
  // Gotta add a error catch here for any group creation issues!
}

// TODO: Yoinking Search Friends from the finished Friends Page
// Finding friends script courtesy of Liam
const DEV_USERS = [
  "alice_wonder",
  "bob_builder",
  "charlie_chaplin",
  "diana_prince",
  "eve_online",
];

// Displays current users friends
async function loadFriends() {
  // Reads CSRF token from token and sends with data
  const token = document.querySelector('meta[name="csrf-token"]').content;
  try {
    // Send HTTP GET request to Flask, runs api route
    const response = await fetch("api/group/friends", {
      method: 'GET',
      headers: { 'X-CSRFToken': token, 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      throw new Error("Could not load friends");
    }

    // Flask sends JSON, JS converts to JS object
    const data = await response.json();
    const friendsList = document.getElementById("friend-search-list")
    friendsList.innerHTML = "";

    data.friends.forEach(friend => {
      const friendDiv = document.createElement("div");
      friendDiv.innerHTML = `
        <li class="flex items-center justify-between py-2 px-4 hover:bg-gray-100 rounded-md">
        <div class="flex items-center gap-3">
          <img src="https://placehold.co/200x200" class="h-8 w-8 rounded-full" />
          <span class="text-sm font-medium text-gray-800">${friend.username}</span>
        </div>
        <button id = '${friend.username}' onclick="return added(this)" class="text-sm bg-primary text-white px-3 py-1 rounded-md hover:bg-blue-800 cursor-pointer">+</button>
      </li>
      `
      friendsList.appendChild(friendDiv);
      document.getElementById("friend-search-results").classList.remove("hidden");
    })
  } catch (err) {
      console.error('Error:', err);
  }
}

function searchFriends() {
  const list = document.getElementById("friend-search-list");
  list.innerHTML = DEV_USERS.map(
    (u) => `
      <li class="flex items-center justify-between py-2 px-4 hover:bg-gray-100 rounded-md">
        <div class="flex items-center gap-3">
          <img src="https://placehold.co/200x200" class="h-8 w-8 rounded-full" />
          <span class="text-sm font-medium text-gray-800">${u}</span>
        </div>
        <button id = '${u}' onclick="return added(this)" class="text-sm bg-primary text-white px-3 py-1 rounded-md hover:bg-blue-800 cursor-pointer">+</button>
      </li>`,
  ).join("");
  document.getElementById("friend-search-results").classList.remove("hidden");

  // Friends Search bar (from friends.js)
    document
    .getElementById('select-friend')
    .addEventListener('input', (e) => {
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
}

function added(button) {
  if (button.innerHTML == "+") {
    button.innerHTML = "-";
    button.classList.add("bg-red-600");
    button.classList.add("hover:bg-red-800");
    button.classList.remove("bg-primary");
    button.classList.remove("hover:bg-blue-800");
    const idToPush = String(button.id);
    grouplist.push(idToPush);
    return;
  }
  button.innerHTML = "+";
  button.classList.add("bg-primary");
  button.classList.add("hover:bg-blue-800");
  button.classList.remove("bg-red-600");
  button.classList.remove("hover:bg-red-800");
  const idToPop = String(button.id);
  grouplist.pop(idToPop);
}