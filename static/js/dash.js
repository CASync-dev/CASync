// simple function to update the time and date on the dashboard every second
// test 4
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

// Run once immediately so the page shows the current time on load
updateTime();
// Keep the time updated every second
setInterval(updateTime, 1000);

// dynamic stuff for the calendar events -------------------------------------


//     GET /api/events/me?start=2026-05-06&end=2026-05-07 
fetch("/api/events/me?start=2026-05-06&end=2026-05-06")
  .then((response) => response.json())
  .then((data) => {
    console.log('Fetched events:', data); // Log the fetched data for debugging
  })
  .catch((error) => {
    console.error('Error loading events:', error);
  });


    // let lastFetchedStart = null;
    // let lastFetchedEnd = null;
    // function fetchAndRenderEvents() {
    //   let apiUrl = calendarBaseUrl;
    //   if ( {{ enableAdaptiveDateCalls | lower }} ) {
    //     const weekDates = getWeekDates();
    //     const weekStart = new Date(weekDates[0]);
    //     const weekEnd = new Date(weekDates[4]);
    //     // if the current week is already covered by the last fetch, just re-render
    //     if (lastFetchedStart && lastFetchedEnd && weekStart >= lastFetchedStart && weekEnd <= lastFetchedEnd) {
    //       renderDesktopEvents();
    //       return;
    //     }
    //     // fetch 2 weeks before and after the current week
    //     const startDate = new Date(weekStart);
    //     startDate.setDate(startDate.getDate() - 14);
    //     const endDate = new Date(weekEnd);
    //     endDate.setDate(endDate.getDate() + 14);
    //     const fmt = d => d.toLocaleDateString('en-CA');
    //     apiUrl += `?start=${fmt(startDate)}&end=${fmt(endDate)}`;
    //     fetch(apiUrl)
    //       .then((response) => response.json())
    //       .then((data) => {
    //         lastFetchedStart = startDate;
    //         lastFetchedEnd = endDate;
    //         events = data;
    //         renderDesktopEvents();
    //       })
    //       .catch((error) => {
    //         console.error('Error loading events:', error);
    //       });
    //     return;
    //   } else {
    //     // if adaptive data calls is not enabled it means the url provided expects no date query param and will return all events
    //     let apiUrl = calendarBaseUrl;
    //             fetch(apiUrl)
    //       .then((response) => response.json())
    //       .then((data) => {
    //         lastFetchedStart = startDate;
    //         lastFetchedEnd = endDate;
    //         events = data;
    //         renderDesktopEvents();
    //       })
    //       .catch((error) => {
    //         console.error('Error loading events:', error);
    //       });
    //   }

    //   fetch(apiUrl)
    //     .then((response) => response.json())
    //     .then((data) => {
    //       events = data;
    //       renderDesktopEvents();
    //     })
    //     .catch((error) => {
    //       console.error('Error loading events:', error);
    //     });
    // }