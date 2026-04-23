// simple function to update the time and date on the dashboard every second
function updateTime() {
    // Get the current date and time each time this runs
    const now = new Date();

    // Update the day and date text on the page
    document.getElementById("day").innerText = now.toLocaleDateString('en-US', { weekday: 'long' });
    document.getElementById("current-date").innerText = now.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });

    // Format the time into hour/minute and AM/PM parts
    let time = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    let timeParts = time.split(' ');

    // Update the time and period separately
    document.getElementById("time").innerText = timeParts[0] ?? "";
    document.getElementById("period").innerText = timeParts[1] ?? "";
}

// Run once immediately so the page shows the current time on load
updateTime();
// Keep the time updated every second
setInterval(updateTime, 1000);