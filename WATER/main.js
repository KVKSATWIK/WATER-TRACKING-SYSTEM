function requestNotificationPermission() {
  if (!("Notification" in window)) return;
  if (Notification.permission === "default") {
    Notification.requestPermission();
  }
}

let notifyTimer = null;

function startReminders(intervalMinutes = 120) {
  stopReminders();
  const ms = intervalMinutes * 60 * 1000;
  notifyTimer = setInterval(() => {
    if (Notification.permission === "granted") {
      new Notification("Time to drink water 💧", { body: "Tap to log your intake!" });
    }
  }, ms);
  localStorage.setItem("hydration_reminder_minutes", String(intervalMinutes));
}

function stopReminders() {
  if (notifyTimer) {
    clearInterval(notifyTimer);
    notifyTimer = null;
  }
  localStorage.removeItem("hydration_reminder_minutes");
}

function initReminders() {
  requestNotificationPermission();
  const saved = parseInt(localStorage.getItem("hydration_reminder_minutes") || "0", 10);
  if (saved > 0) startReminders(saved);
}

async function logWater(ml) {
  try {
    const res = await fetch("/api/log", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount_ml: ml })
    });
    const data = await res.json();
    if (data.ok) {
      document.getElementById("today-total").textContent = data.today_total;
      document.getElementById("goal").textContent = data.goal;
      document.getElementById("progress-pct").textContent = data.pct;
      document.getElementById("streak").textContent = data.streak;
      const bottle = document.getElementById("bottle-fill");
      const bar = document.getElementById("progress-bar");
      if (bottle) bottle.style.height = data.pct + "%";
      if (bar) bar.style.width = data.pct + "%";
    }
  } catch (e) {
    console.error(e);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initReminders();

  document.querySelectorAll(".log-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const ml = parseInt(btn.dataset.ml, 10);
      logWater(ml);
    });
  });

  const notifyToggle = document.getElementById("notify-toggle");
  if (notifyToggle) {
    notifyToggle.addEventListener("click", async () => {
      if (!("Notification" in window)) return alert("Notifications not supported in this browser.");
      if (Notification.permission !== "granted") {
        await Notification.requestPermission();
      }
      if (notifyTimer) {
        stopReminders();
        alert("Reminders disabled.");
      } else {
        const minutes = parseInt(prompt("Remind me every how many minutes? (e.g., 120)", "120") || "0", 10);
        if (minutes > 0) {
          startReminders(minutes);
          alert("Reminders enabled.");
        }
      }
    });
  }
});
