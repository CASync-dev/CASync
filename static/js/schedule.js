// ── Event data
// This is the list of events that get rendered onto the calendar.
// At the moment we just call the API to get all events and render them
// Should be smarter later, idk if here or in the api request
// We

// -- Add event form handler
document.getElementById("add-event-form").addEventListener("submit", (e) => {
  e.preventDefault();
  // Get form values
  const title = document.getElementById("event-title").value;
  const date = document.getElementById("event-date").value;
  const start_time = document.getElementById("event-time-start").value;
  const end_time = document.getElementById("event-time-end").value;
  const location = document.getElementById("event-location").value;
  const description = document.getElementById("event-description").value;
  const color = document.getElementById("event-color").value;
  errorElement = document.getElementById("form-message");
  // Basic validation
  if (!title || !date || !start_time || !end_time) {
    errorElement.textContent = "Please fill in all required fields.";
    errorElement.classList.remove("hidden");
    return;
  }
  // end time must be after start time
  if (parseTime(end_time) <= parseTime(start_time)) {
    errorElement.textContent = "End time must be after start time.";
    errorElement.classList.remove("hidden");
    return;
  }
  // if event is today, start time must be after current time
  const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
  if (date === today) {
    const currentTime = new Date();
    const currentTimeMinutes = currentTime.getHours() * 60 + currentTime.getMinutes();
    const startTimeMinutes = parseTime(start_time);
    if (startTimeMinutes <= currentTimeMinutes) {
      errorElement.textContent =
        "Events have to be in the future. Please select a start time later than the current time.";
      errorElement.classList.remove("hidden");
      return;
    }
  }

  // Create event object in json format expected by the API
  const newEvent = {
    title: title,
    date: date,
    start_time: start_time,
    end_time: end_time,
    location: location,
    description: description,
    color: color,
  };

  // Send POST request to API to create the event
  fetch("/api/events", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF },
    body: JSON.stringify(newEvent),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to create event");
      }
      console.log("Event created successfully");
      return response.json();
    })
    .then((createdEvent) => {
      // close the modal, reset form and render events
      document.getElementById("add-event-form").reset();
      selectColor(
        document.querySelector("#color-picker-buttons button"),
        "indigo",
      );
      const dialog = document.querySelector("#drawer");
      dialog.close();

      document.dispatchEvent(
        new CustomEvent("calendar:event-created", { detail: createdEvent }),
      );
    })
    .catch((error) => {
      console.error("Error creating event:", error);
      errorElement.textContent = "Error creating event. Please try again.";
      errorElement.classList.remove("hidden");
      console.error("Error creating event:", error);
    });
});

// When the user clicks a color button in the add event form, we update the hidden input value and add a ring around the selected button.
function selectColor(btn, color) {
  // expects the button element and the color name as defined in COLOR_MAP (e.g. "indigo", "red", etc.)
  document.getElementById("event-color").value = color;
  // Remove the ring from all buttons, then add it to the selected button
  document.querySelectorAll("#color-picker-buttons button").forEach((b) => {
    b.classList.remove("ring-2", "ring-offset-2", "ring-black");
  });
  btn.classList.add("ring-2", "ring-offset-2", "ring-black");
}

// Same as selectColor but for the edit event form, we update the hidden input value and add a ring around the selected button.
function editColor(btn, color) {
  // expects the button element and the color name as defined in COLOR_MAP (e.g. "indigo", "red", etc.)
  document.getElementById("edit-event-color").value = color;
  // Remove the ring from all buttons, then add it to the selected button
  document
    .querySelectorAll("#edit-color-picker-buttons button")
    .forEach((b) => {
      b.classList.remove("ring-2", "ring-offset-2", "ring-black");
    });
  btn.classList.add("ring-2", "ring-offset-2", "ring-black");
}

// -- Custom Event Action Handlers
// When the cal was on this page we used to push event changes to the local list and re-render
// Now we dispatch custom events when we create, update, or delete an event, and listen for those events to update our local list and re-render.
let pendingDeleteId = null;

// When the user clicks the delete button on an event card
// we store the event ID and show the confirmation dialog
// If they confirm, we send a DELETE request to the API and remove the event from our local list and re-render.
function deleteEvent(eventId) {
  pendingDeleteId = eventId;
  document.getElementById("delete-confirmation").showModal();
}

document.getElementById("confirm-delete-btn").addEventListener("click", () => {
  // If there's no pending delete ID for some reason, just return early
  if (pendingDeleteId === null) return;
  const id = pendingDeleteId;
  pendingDeleteId = null;

  // Send DELETE request to the API to delete the event
  fetch(`/api/events/${id}`, {
    method: "DELETE",
    headers: {
      "X-CSRFToken": CSRF,
    },
  })
    .then((response) => {
      if (!response.ok) throw new Error("Failed to delete");
      document.dispatchEvent(
        new CustomEvent("calendar:event-deleted", { detail: { id } }),
      );
    })
    .catch((err) => console.error("Error deleting event:", err));
});

// Edit Buton
// When the user clicks the edit button on an event card, we bring up a edit event modal pre-filled with the event's current details.
// When they submit, we send a PUT request to the API to update the event, then update our local list and re-render.
function editEvent(eventId) {
  eventId = Number(eventId);
  // Open the edit modal and pre-fill the form with the event's current details
  const event = Object.values(events)
    .flatMap((userData) => Object.values(userData.events))
    .find((e) => e.id === eventId);
  if (!event) return;
  document.getElementById("edit-event-modal").showModal();
  document.getElementById("edit-event-title").value = event.title;
  document.getElementById("edit-event-description").value = event.description;
  document.getElementById("edit-event-date").value = event.date;
  document.getElementById("edit-event-time-start").value = event.startTime;
  document.getElementById("edit-event-time-end").value = event.endTime;
  document.getElementById("edit-event-location").value = event.location || "";
  selectColor(
    document.querySelector(
      `#edit-color-picker-buttons #${event.color}-color-btn`,
    ),
    event.color,
  );
  // When the user submits the edit form, we gather the updated details and send a PUT request to the API
  document.getElementById("save-edit-btn").onclick = (e) => {
    document.getElementById("edit-event-modal").close();
    // We prevent the default form submission behavior
    e.preventDefault();
    // We gather the updated event details from the form inputs as JSON
    const updatedEvent = {
      title: document.getElementById("edit-event-title").value,
      description: document.getElementById("edit-event-description").value,
      date: document.getElementById("edit-event-date").value,
      start_time: document.getElementById("edit-event-time-start").value,
      end_time: document.getElementById("edit-event-time-end").value,
      location: document.getElementById("edit-event-location").value,
      color: document.getElementById("edit-event-color").value,
    };
    // We send a PUT request to the API to update the event with the new details
    fetch(`/api/events/${eventId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF },
      body: JSON.stringify(updatedEvent),
    })
      .then((response) => {
        if (!response.ok) throw new Error("Failed to update event");
        return response.json();
      })
      .then((updatedEvent) => {
        document.dispatchEvent(
          new CustomEvent("calendar:event-updated", { detail: updatedEvent }),
        );
      })
      .catch((err) => console.error("Error updating event:", err));
  };
}
