// TODO: This will get replaced with a user session deteciton system later
// Jquery  for adding user options to the dropdown (replace with actual user data)
// This JS is no longer used with the introduction of user logins. 
//---------------------------------------------------------
function addUserOptions(user) {
    const a = document.createElement("a");
    a.href = "#";
    a.className =
    "block px-4 py-2 text-sm text-gray-700 focus:bg-gray-100 focus:text-gray-900 focus:outline-hidden";
    a.textContent = user.username;
    a.dataset.userId = user.id; // Store user id in data attribute for later use
    $("#dropdown-menu-1").append(a);
}

let selectedUserId = null;
// On Selection Of User From Dropdown, set selectedUserId
$(document).on("click", "#dropdown-menu-1 a", function () {
    // Set selected user ID based on clicked option
    selectedUserId = $(this).data("userId");
    // Update dropdown button text to show selected user
    $("#menu-button-1").html(
    $(this).text() +
        ' <i class="py-1 pl-2 fas fa-chevron-down text-xs"></i>',
    );
    $('[name="user_id"]').val(selectedUserId);
    checkForExistingCalendars(); // Check if the selected user has existing calendars to determine whether to show sync button
});
//---------------------------------------------------------

function checkForExistingCalendars() {
    /*
Check if a selected user has any calender in the system. If they do
show the sync button with the number of existing calenders, 
if not hide the sync button since there is nothing to sync with
*/
    // Check if the user has any calendars
    fetch("/api/calendars/")
    .then((res) => {
        if (!res.ok) {
        return;
        }
        return res.json();
    })
    .then((calendars) => {
        if (!calendars) return;
        if (calendars.length > 0) {
        $("#sync-button").removeClass("hidden");
        $("#sync-button").html(
            `<i class="fa-solid fa-rotate"></i> Sync (${calendars.length}) cals`,
        );
        } else {
        $("#sync-button").addClass("hidden");
        }
    });
}
checkForExistingCalendars();

function showMsg(msg, isSuccess) {
    const msgEl = document.createElement("p");
    msgEl.className = `${isSuccess ? "text-green-600" : "text-red-600"} text-sm mt-2`;
    msgEl.textContent = msg;
    document.querySelector("form").appendChild(msgEl);
    setTimeout(() => {
    msgEl.remove();
    }, 5000);
}

async function syncCal() {
    const token = document.querySelector('meta[name="csrf-token"]').content;
    const res = await fetch(`/api/sync-cal/`, {
    headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": token,
    },
    method: "POST",
    });
    const data = await res.json();
    if (res.ok) {
    showMsg(
        `Successfully synced calendar. ${data.created} events created, ${data.updated} events updated.`,
        true,
    );
    } else {
    showMsg("Error: " + (data.error || "Unknown error"), false);
    }
}

let pfpFlag = 0;
function showProfileSettings() {
    if (pfpFlag == 0) {
    document.getElementById("profile-settings").classList.remove("hidden");
    pfpFlag = 1;
    } else {
    document.getElementById("profile-settings").classList.add("hidden");
    pfpFlag = 0;
    }
}

let accFlag = 0;
function showAccountSettings() {
    if (accFlag == 0) {
    document.getElementById("account-settings").classList.remove("hidden");
    accFlag = 1;
    } else {
    document.getElementById("account-settings").classList.add("hidden");
    accFlag = 0;
    }
}

// Changing username Functions
async function changeUsername() {
    // error will display errors encountered during changing username...
    const errormsg = document.getElementById("usererror");
    const newusername = document.getElementById("newuser").value;
    let results;

    const token = document.querySelector('meta[name="csrf-token"]').content;
    if (newusername == "") {
        return
    }
    try {
      const response = await fetch("/api/changeusername", {
        method: "POST", 
        headers: { "X-CSRFToken": token, "Content-Type": "application/json" },
        body: JSON.stringify({ newuser: newusername})
    })
        .then((response) => response.json())
        .then((x) => {
        results = x;
        if ("error" in results) {
            throw new Error(results["error"]);
        }
        });
    } catch (error) {
    // In case leftover 
        errormsg.classList.remove("text-green-600");
        errormsg.classList.add("text-red-600");
        errormsg.innerHTML = "Error:" + error;
        console.error("Error:", error);
        return
    }
    errormsg.classList.remove("text-red-600");
    errormsg.classList.add("text-green-600");
    errormsg.innerHTML = "Successfully changed your username!"
    return
}

// Changing email function
async function changeEmail() {
    // error will display errors encountered during changing email (ie. not an email...)
    const errormsg = document.getElementById("mailerror"); 
    const newmail = document.getElementById("newemail").value;
    let results;

    const token = document.querySelector('meta[name="csrf-token"]').content;
    if (newmail == "") {
        return
    }
    try {
    const response = await fetch("/api/changeemail", {
        method: "POST", 
        headers: { "X-CSRFToken": token, "Content-Type": "application/json" },
        body: JSON.stringify({ newemailaddress: newmail})
    })
        .then((response) => response.json())
        .then((x) => {
        results = x;
        if ("error" in results) {
            throw new Error(results["error"]);
        }
        });
    } catch (error) {
    // In case leftover 
    errormsg.classList.remove("text-green-600");
    errormsg.classList.add("text-red-600");
    errormsg.innerHTML = error;
    console.error("Error:", error);
    return
    }
    errormsg.classList.remove("text-red-600");
    errormsg.classList.add("text-green-600");
    errormsg.innerHTML = "Successfully changed your email!"
    return
}

// Changing Password and Account deletion done via. flask forms.

async function removeLink(urlid) {
    const icaldiv = document.getElementsByClassName(urlid);
    const errormsg = document.getElementById('icalediterror');
    let results;
    
    const token = document.querySelector('meta[name="csrf-token"]').content;
    try {
        const response = await fetch("/api/remove-cal/", {
            method: "POST",
            headers: { "X-CSRFToken": token, "Content-Type": "application/json" },
            body: JSON.stringify({id:urlid})
        })
        .then((response) => response.json())
        .then((x) => {
        results = x;
        if ("error" in results) {
            throw new Error(results["error"]);
        }
        });
    } catch (error) {
        errormsg.classList.remove("text-green-600");
        errormsg.classList.add("text-red-600");
        errormsg.innerHTML = error;
        console.error("Error:", error);
        return;
    }
    errormsg.classList.remove("text-red-600");
    errormsg.classList.add("text-green-600");
    for (var i = 0; i < icaldiv.length; i++) {
        icaldiv[i].remove();
    }
    errormsg.innerHTML = "Succesfully removed iCal Link!";
}

document.getElementById("pfpform").addEventListener('submit', async function(e) {
    e.preventDefault(); // We'll handle sending ourselves!

    const newPFP = document.getElementById("newpfp").files; // Only used to check length
    const errormsg = document.getElementById('pfperror');
    if (newPFP.length < 1) {
        errormsg.classList.remove("text-green-600");
        errormsg.classList.add("text-red-600");
        errormsg.innerHTML = "No file uploaded."
        return
    }
    let results;


    const formToSend = new FormData(this);

    const token = document.querySelector('meta[name="csrf-token"]').content;
    try {
        const response = await fetch("/api/changepfp", {
            method: "POST",
            headers: { "X-CSRFToken": token },
            body: formToSend
        })
        .then((response) => response.json())
        .then((x) => {
        results = x;
        if ("error" in results) {
            throw new Error(results["error"]);
        }
        });
    } catch (error) {
        if (error instanceof TypeError) {
            errormsg.classList.remove("text-green-600");
            errormsg.classList.add("text-red-600");
            errormsg.innerHTML = "Oops! File not supported! Supported types are: .png, .jpg"
            return;
        }
        errormsg.classList.remove("text-green-600");
        errormsg.classList.add("text-red-600");
        errormsg.innerHTML = error;
        console.error("Error:", error);
        return;
    } 
    errormsg.classList.remove("text-red-600");
    errormsg.classList.add("text-green-600");
    errormsg.innerHTML = "Successfully changed your profile!"
    document.getElementById("newpfp").value = "" // Clear file selection after setting
    document.getElementById("pfp").setAttribute("src", results["success"])
    return
    
})

async function delPFP() {
    const errormsg = document.getElementById('pfperror');
    const token = document.querySelector('meta[name="csrf-token"]').content;
    try {
        const response = await fetch("/api/removepfp", {
            method: "POST",
            headers: { "X-CSRFToken": token, "Content-Type": "application/json" },
            body: JSON.stringify({removepfp: "true"})
        })
        .then((response) => response.json())
        .then((x) => {
        results = x;
        if ("error" in results) {
            throw new Error(results["error"]);
        }
        });
    } catch (error) {
        errormsg.classList.remove("text-green-600");
        errormsg.classList.add("text-red-600");
        errormsg.innerHTML = error;
        console.error("Error:", error);
        return;
    }
    errormsg.classList.remove("text-red-600");
    errormsg.classList.add("text-green-600");
    errormsg.innerHTML = "Successfully removed your profile!"
    document.getElementById("pfp").setAttribute("src", results["success"])
    return
}
