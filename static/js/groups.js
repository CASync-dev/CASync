  let groupname = "My Group";
  let grouplist = [];
  function loadcreategroup() {
    const x = document.getElementById("create-group");
    x.showModal();
  }
  function closeloadcreategroup() {
    const x = document.getElementById("create-group");
    x.close();
  }
  function loadselectfriends(){
    const x = document.getElementById("create-group");
    groupname = document.getElementById("group-name-input").value;
    x.close();
    const y = document.getElementById("select-friend");
    y.showModal();
    document.getElementById("gname").innerText = groupname;
  }
  function closeloadselectfriends() {
    const x = document.getElementById("select-friend");
    // Reset all saved values.
    groupname = "";
    grouplist = [];
    x.close();
  }

  // Dev function to check data 
  function testsubmit() {
    alert(groupname);
    alert(grouplist);
  }

  function submitgroupcreation() {
    let url = "/api/group/create";
    fetch(url, {
      method: 'POST',
      body: JSON.stringify({name: groupname, list: grouplist})
    });
    // Gotta add a error catch here for any group creation issues!
  }

  // Finding friends script courtesy of Liam
  const DEV_USERS = [
    "alice_wonder",
    "bob_builder",
    "charlie_chaplin",
    "diana_prince",
    "eve_online",
  ];

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
  }

  function added(button) {
    if (button.innerHTML == '+') {
      button.innerHTML = '-';
      button.classList.add('bg-red-600');
      button.classList.add('hover:bg-red-800');
      button.classList.remove('bg-primary');
      button.classList.remove('hover:bg-blue-800');
      const idtopush = String(button.id);
      grouplist.push(idtopush);
      return
      }
    button.innerHTML = '+';
    button.classList.add('bg-primary');
    button.classList.add('hover:bg-blue-800');
    button.classList.remove('bg-red-600');
    button.classList.remove('hover:bg-red-800');
    const idtopop = String(button.id);
    grouplist.pop(idtopop);
  }