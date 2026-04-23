


function updateTime() {
        const now = new Date();

    document.getElementById("day").innerText = now.toLocaleDateString('en-US', { weekday: 'long' });
    document.getElementById("current-date").innerText = now.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    let time = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    let timeParts = time.split(' ');
    document.getElementById("time").innerText = timeParts[0] ?? "";
    document.getElementById("period").innerText = timeParts[1] ?? "";
}

updateTime();
setInterval(updateTime, 1000); // Update every second