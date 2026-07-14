// Variables
let groupname = document.getElementById("group-name-input").value;
let grouplist = [];

// Functions for Group Dialog Modal
function loadCreateGroup() {
  const createGroupModal = document.getElementById("create-group");
  createGroupModal.showModal();
}
function closeLoadCreateGroup() {
  const createGroupModal = document.getElementById("create-group");
  const errorMsg = document.getElementById("group-error-message");
  const groupNameInput = document.getElementById("group-name-input")

  errorMsg.textContent = "";
  groupNameInput.value = "";
  createGroupModal.close();
}

// Functions for Friends Dialog Modal
async function loadSelectFriends() {
  const GroupModal = document.getElementById("create-group");
  groupname = document.getElementById("group-name-input").value;
  const existingError = document.getElementById("group-name-error");

  // Remove previous error so only one error is shown
  if (existingError) existingError.remove();

  if (!window.addMemberMode) {
    // Validate empty group name
    if (!groupname) {
      const groupErrorDiv = document.getElementById("group-error-message");
      const errorMsg = document.getElementById("group-error-message");
      groupErrorDiv.className = "text-red-600 text-sm mt-3 sm:mt-2";
      errorMsg.textContent = "Please enter a group name";

      return false;
    }

    GroupModal.close();
  }

  const friendModal = document.getElementById("select-friend");
  friendModal.showModal();
  document.getElementById("gname").innerText = groupname;

  // Immediately loads and displays friends when switching modals
  await loadFriends();

  return false;
}

function closeLoadSelectFriends() {
  const selectFriendModal = document.getElementById("select-friend");
  // Reset all saved values.
  groupname = "";
  grouplist = [];
  window.addMemberMode = false; // reset flag
  selectFriendModal.close();
}

async function submitGroupCreation() {
  // Reads CSRF token from token and sends with data
  const token = document.querySelector('meta[name="csrf-token"]').content;

  try {
    // Send request to Flask
    const response = await fetch("/api/group/create", {
      method: "POST",
      headers: {
        "X-CSRFToken": token,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name: groupname,
        list: grouplist,
      }),
    });

    //  Flask returns JSON response
    const data = await response.json();

    // Error
    if (!response.ok) {
      throw new Error(data.error || "Something went wrong");
    }

    // // Add new group to page
    addGroupToPage(data.group);

    // // Close the modal to return back to groups page
    closeLoadSelectFriends();
  } catch (err) {
    // Gotta add a error catch here for any group creation issues!
    console.error(err);
    alert("Failed to create group"); // temporary error handling, will replace
  }
}

function addGroupToPage(group) {
  const groupList = document.getElementById("groups-list");
  const liGroup = document.createElement("li");
  liGroup.id = `group-${group.id}`;

  const memberAvatars = group.members
    .map((member) => {
      return `
      <img
        id = "${member.username}-avatar"
        src = "${member.pfp}"
        class = "w-8 h-8 rounded-full -ml-2 first:ml-0 border-2 border-dark"
        alt = "${member.username}'s profile picture"
        title = "${member.username}"
      />
    `;
    })
    .join("");

  liGroup.className = `
    py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between 
    bg-white border border-gray-300 rounded-2xl mb-2 px-3 shadow-xl
    hover:ring-1 hover:shadow hover:border-gray-400 hover:border-2 hover:cursor-pointer ring-white transition duration-200`;
  liGroup.innerHTML = `
    <div class="flex items-center">
      <div class="ml-4">
        <!-- Group Name -->
        <p class="text-xl font-medium">
          ${group.group_name}
        </p>

        <!-- Member Avatars -->
        <div id="group-member-avatars" class = "flex items-center my-2 group-avatars">
          ${memberAvatars}
        </div>
      </div>
    </div>

    <!-- Buttons -->
    <button
      id="btn-leave-group-${group.id}"
      class="btn-plain mt-2 px-3 sm:ml-auto py-2 bg-red-300 text-nearwhite rounded-lg hover:bg-red-400"
      onclick="leaveGroup(${group.id})"
    >
      <i class="fas fa-sign-out-alt"></i>
      Leave
    </button>
    <button
      id="btn-groups-schedule-${group.id}"
      class="btn-plain mt-2 px-3 py-2 bg-blue-300 text-nearwhite rounded-lg hover:bg-blue-400"
      onclick="openSchedule('${group.id}', '${group.group_name}')"
    >
      <i class="fas fa-calendar-alt"></i>
      Schedule
  </button>
  <button
    id="btn-groups-details-${group.id}"
    class = "btn-plain bg-dark rounded-lg sm:rounded-full px-4 py-3"
    onclick = "getGroupId(${group.id}); openGroupDetail(); loadGroupMembers()">
    <i class = "fas fa-info text-nearwhite text-center"></i>
    <div class = "text-nearwhite sm:hidden">
      Details
    </div>
  </button>
  `;

  groupList.appendChild(liGroup);
}

async function updateGroupAvatarsInPage(groupId) {
  try {
    const response = await fetch(`/api/group/${groupId}`);
    const group = await response.json();

    if (!response.ok) {
      throw new Error(group.error || "Could not fetch group members");
    }

    // Referencing addGroupToPage, but only for avatars
    const memberAvatars = group.members
      .map((member) => {
        return `
      <img
        src = "${member.pfp}"
        class = "w-8 h-8 rounded-full -ml-2 first:ml-0 border-2 border-dark"
        alt = "${member.username}'s profile picture"
        title = "${member.username}"
      />
    `;
      })
      .join("");

    // Updates the avatars to include new members
    const groupElement = document.getElementById(`group-${groupId}`);
    const avatarDiv = groupElement.querySelector(".group-avatars");

    if (avatarDiv) {
      avatarDiv.innerHTML = memberAvatars;
    }
  } catch (err) {
    console.log(err);
    alert(err);
  }
}

// TODO: Yoinking Search Friends from the finished Friends Page
// Finding friends script courtesy of Liam
// const DEV_USERS = [
//   "alice_wonder",
//   "bob_builder",
//   "charlie_chaplin",
//   "diana_prince",
//   "eve_online",
// ];

// Displays current users friends
async function loadFriends(excludeIds = []) {
  // Reads CSRF token from token and sends with data
  const token = document.querySelector('meta[name="csrf-token"]').content;
  try {
    // Send HTTP GET request to Flask, runs api route
    const response = await fetch("/api/group/friends", {
      method: "GET",
      headers: { "X-CSRFToken": token, "Content-Type": "application/json" },
    });

    // Flask sends JSON, JS converts to JS object
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Could not load friends");
    }

    const friendsList = document.getElementById("friend-search-list");
    friendsList.innerHTML = "";

    data.friends
      .filter((friend) => !excludeIds.includes(friend.id)) // skips existing group members
      .forEach((friend) => {
        const friendDiv = document.createElement("div");
        friendDiv.innerHTML = `
          <li class="flex items-center justify-between py-2 px-4 hover:bg-gray-100 rounded-md">
            <div class="flex items-center gap-3">
              <img src="${friend.pfp}" class="h-8 w-8 rounded-full" />
              <span class="text-sm font-medium text-gray-800">${friend.username}</span>
            </div>
            <button id = '${friend.username}' onclick="return added(this)" class="text-sm bg-primary text-white px-3 py-1 rounded-md hover:bg-blue-800 cursor-pointer">+</button>
        </li>
        `;
        friendsList.appendChild(friendDiv);
        document
          .getElementById("friend-search-results")
          .classList.remove("hidden");
      });
  } catch (err) {
    console.error("Error:", err);
  }
}

// Search logic based on friends.js
function setupSearchFriend() {
  const input = document.getElementById("friend-search-input");
  input.addEventListener("input", (e) => {
    // lowercased for standardized search
    const query = e.target.value.toLowerCase();
    const friend = document.querySelectorAll("#friend-search-list li");

    friend.forEach((li) => {
      const username = li.querySelector("span").textContent.toLowerCase();

      if (username.includes(query)) {
        li.classList.remove("hidden");
      } else {
        li.classList.add("hidden");
      }
    });
  });
}

// Adding or removing friends in Select Friend Modal
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

// Leaving group functions
function leaveGroup(groupId) {
  // Open the confirmation dialog
  const dialog = document.getElementById("remove-confirmation");
  dialog.showModal();

  // Store groupID as attribute on button for access in confirmLeaveGroup()
  document
    .getElementById("confirm-delete-btn")
    .setAttribute("data-group-id", groupId);
}

async function confirmLeaveGroup() {
  const token = document.querySelector('meta[name="csrf-token"]').content;
  const groupId = document
    .getElementById("confirm-delete-btn")
    .getAttribute("data-group-id");

  try {
    const response = await fetch("/api/group/leave", {
      method: "POST",
      headers: { "X-CSRFToken": token, "Content-Type": "application/json" },
      body: JSON.stringify({ group_id: groupId }),
    });

    // Flask sends JSON, JS converts to JS object
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Could not delete group");
    }

    document.getElementById(`group-${groupId}`).remove();
    document.getElementById("remove-confirmation").close();
  } catch (err) {
    console.error("error: ", err);
  }
}

// Group Details
function getGroupId(groupId) {
  // Set global group ID for reuse in other functions
  // Gets its own function so it's not reliant on having group members to get the global var
  window.currentGroupId = groupId;
}

async function openGroupDetail() {
  const groupDetailModal = document.getElementById("group-details");
  groupDetailModal.showModal();
}

function closeGroupDetail() {
  const groupDetailModal = document.getElementById("group-details");
  groupDetailModal.close();
}

async function loadGroupMembers() {
  const gnameTitle = document.getElementById("group-detail-gname");

  try {
    const response = await fetch(`/api/group/${window.currentGroupId}`);
    const group = await response.json();
    if (!response.ok) {
      throw new Error(group.error || "Could not fetch group members");
    }

    // Render members
    const container = document.getElementById("add-members-list");
    container.innerHTML = group.members
      .map(
        (member) => `
      <li id="friend-${member.id}" class="py-4 flex items-center justify-between bg-lightgray border border-gray-400 rounded-2xl mb-2 px-3 hover:ring-1 hover:shadow shadow-xl ring-white transition duration-200">
        <div class="flex items-center">
          <img class="h-15 w-15 rounded-full" src="${member.pfp}" alt="${member.username}'s avatar" />
          <div class="ml-4">
            <p class="text-sm font-medium">${member.username}</p>
            <p class="text-sm">${member.email}</p>
          </div>
        </div>
      </li>
    `,
      )
      .join("");

    // Render title
    gnameTitle.innerText = group.group_name;

    // Render member count
    const memberCount = document.getElementById("member-count");
    memberCount.innerText = `(${group.members.length})`;

    // Undecided whether want to add removal or not, or just let them leave by themselves (cuz anyone can remove from group)
    // <button class="btn-plain px-3 ml-auto py-2 bg-red-300 text-white rounded-lg hover:bg-red-400" onclick="removeFriend('${member.id}')">
    //     <i class="fas fa-user-times"></i>
    // </button>
  } catch (err) {
    console.error(err);
    // alert("Could not fetch group members");
  }
}

async function openAddMemberModal() {
  // Reusing loadSelectFriends() for modal setup since it's basically the same functionality
  // Adapting it for adding members tho
  window.addMemberMode = true;

  // Fetch current group member details
  try {
    const response = await fetch(`/api/group/${window.currentGroupId}`);
    const group = await response.json();
    if (!response.ok) {
      throw new Error(group.error || "Could not fetch group details");
    }

    // Set group name for display (reuses groupname variable)
    groupname = group.group_name;

    // Update modal title for add member mode (reuses select friends modal elements)
    document.getElementById("friend-modal-title").innerText =
      "Add Members to Group";
    document.getElementById("gname").innerText = groupname;

    // Get existing member IDs to exclude
    const existingMemberIds = group.members.map((m) => m.id);

    // Open the modal and load friends
    const selectFriendModal = document.getElementById("select-friend");
    selectFriendModal.showModal(); // opens modal, skips creating group validation
    loadFriends(existingMemberIds); // Excludes current members
  } catch (err) {
    console.error(err);
  }
}

async function submitAddMember() {
  const token = document.querySelector('meta[name="csrf-token"]').content;

  try {
    const response = await fetch("/api/group/add_member", {
      method: "POST",
      headers: {
        "X-CSRFToken": token,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        group_id: window.currentGroupId,
        list: grouplist,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(
        data.error || "Something went wrong when submitting new members",
      );
    }

    // Refresh group details
    loadGroupMembers(window.currentGroupId);

    // Refresh group avatars in page (the only thing that gets updated)
    updateGroupAvatarsInPage(window.currentGroupId);

    // Closes the model (same as select friends, so just reuse the function)
    closeLoadSelectFriends();
  } catch (err) {
    console.error(err);
    // alert("Failed to add members"); // Temporary error handling
    const addMemberErrorDiv = document.getElementById("add-member-error-div");
    const addMemberErrorMsg = document.getElementById(
      "add-member-error-message",
    );
    addMemberErrorDiv.className = "text-red-600 text-sm mt-3 sm:mt-2";
    addMemberErrorMsg.textContent = err.message;
  }
}

// Buttons to be pressed via Enter for convenience
function handleEnter(e, action) {
  if (e.key === "Enter") {
    e.preventDefault();
    action();
  }
}

document
  .getElementById("group-name-input")
  .addEventListener("keydown", (e) => handleEnter(e, loadSelectFriends));

// Schedule stuff
function openSchedule(groupId, groupname) {
  const token = document.querySelector('meta[name="csrf-token"]').content;

  calendarBaseUrl = `/api/events/group/${groupId}`;
  lastFetchedStart = null;
  lastFetchedEnd = null;
  // re-render the calendar with the new data source
  fetchAndRenderEvents();
  // set the modal title to the group name
  document.getElementById("group-schedule-title").textContent =
    `${groupname}'s Schedule`;
  // open the modal
  const modal = document.getElementById("group-schedule-modal");
  modal.showModal();
}

const scheduleModal = document.getElementById("group-schedule-modal");
new MutationObserver(() => {
  if (scheduleModal.open) requestAnimationFrame(() => renderDesktopEvents());
}).observe(scheduleModal, { attributes: true, attributeFilter: ["open"] });

// Calls search setup once instead of creating a new event listener every search
document.addEventListener("DOMContentLoaded", () => {
  setupSearchFriend();
});

// Group Event Creation -------------------------------------------------------
// Similar logic to schedule.js, just with a group id included :)

// (Group) Event form handler
document.getElementById("add-event-form").addEventListener("submit", (e) => {
  e.preventDefault();
  // Get form values
  const title = document.getElementById("event-title").value;
  const startInput = document.getElementById("event-start").value;
  const endInput = document.getElementById("event-end").value;
  const location = document.getElementById("event-location").value;
  const description = document.getElementById("event-description").value;
  const color = document.getElementById("event-color").value;
  errorElement = document.getElementById("form-message");
  // Basic validation
  if (!title || !startInput || !endInput) {
    errorElement.textContent = "Please fill in all required fields.";
    errorElement.classList.remove("hidden");
    return;
  }
  // datetime-local inputs are interpreted as local time
  const startDate = new Date(startInput);
  console.log(startDate.toISOString())
  const endDate = new Date(endInput);
  console.log(endDate.toISOString())
  // end must be after start
  if (endDate <= startDate) {
    errorElement.textContent = "End must be after start.";
    errorElement.classList.remove("hidden");
    return;
  }
  // Event must be in the future
  if (startDate <= new Date()) {
    errorElement.textContent =
      "Events have to be in the future. Please select a start time later than now.";
    errorElement.classList.remove("hidden");
    return;
  }

  // From here on, new content :)
  // To be finished.

  const newEvent = {

  };


});