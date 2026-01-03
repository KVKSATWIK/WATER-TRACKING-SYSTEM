# Smart Water Intake Reminder

A simple, remarkable hydration tracker with a sleek UI (Flask + Tailwind).  
Features: quick log buttons, animated bottle fill, streaks, history chart, and optional desktop notifications.

## 1) Install

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

## 2) Run

```bash
python app.py
```
The app starts at http://localhost:5000

## 3) Project Structure

```
water-tracker/
  app.py
  requirements.txt
  templates/
    base.html
    index.html
    history.html
  static/
    main.js
    styles.css
```

## 4) What it Does

- **Dashboard:** shows your daily goal, total intake, progress bar, and bottle animation.
- **Quick Log:** +250ml, +500ml, +750ml, +1000ml or a custom amount.
- **Set Goal:** change your daily goal from the UI.
- **Streak:** counts consecutive days (including today) where you reached your goal.
- **History:** 7/14/30-day chart (Chart.js).
- **Reminders:** desktop notifications every X minutes (when the tab is open).

## 5) Customize

- Default daily goal is 3000 ml (3L). Change it in the UI or in `User.daily_goal_ml` default in `app.py`.
- Styling uses Tailwind CDN for simplicity—tweak in `styles.css` and classes in templates.

## 6) Notes

- This starter uses SQLite (`water.db`) located next to `app.py`.
- For production, generate a strong `SECRET_KEY` and consider a real user system (JWT/OAuth).
- Push notifications in the background require a Service Worker and a full PWA setup (advanced).
