from datetime import date, datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///water.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "dev-secret"  # replace for production
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, default="You")
    daily_goal_ml = db.Column(db.Integer, nullable=False, default=3000)  # default 3L

class WaterLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    amount_ml = db.Column(db.Integer, nullable=False)
    logged_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

# ----------------- Helpers -----------------
def get_or_create_user() -> User:
    user = User.query.first()
    if not user:
        user = User(name="You", daily_goal_ml=3000)
        db.session.add(user)
        db.session.commit()
    return user

def start_of_day(dt: datetime) -> datetime:
    return datetime(dt.year, dt.month, dt.day)

def today_range() -> tuple[datetime, datetime]:
    start = start_of_day(datetime.utcnow())
    end = start + timedelta(days=1)
    return start, end

def total_intake_for_day(user_id: int, day: date) -> int:
    start = datetime(day.year, day.month, day.day)
    end = start + timedelta(days=1)
    total = db.session.query(func.coalesce(func.sum(WaterLog.amount_ml), 0)).filter(
        WaterLog.user_id == user_id,
        WaterLog.logged_at >= start,
        WaterLog.logged_at < end,
    ).scalar()
    return int(total or 0)

def consecutive_streak_days(user_id: int, goal_ml: int) -> int:
    streak = 0
    d = date.today()
    while True:
        total = total_intake_for_day(user_id, d)
        if total >= goal_ml:
            streak += 1
            d = d - timedelta(days=1)
        else:
            break
    return streak

# ----------------- Routes -----------------
@app.route("/")
def index():
    user = get_or_create_user()
    start, end = today_range()
    today_total = db.session.query(func.coalesce(func.sum(WaterLog.amount_ml), 0)).filter(
        WaterLog.user_id == user.id,
        WaterLog.logged_at >= start,
        WaterLog.logged_at < end,
    ).scalar() or 0
    pct = min(100, int(round((today_total / user.daily_goal_ml) * 100))) if user.daily_goal_ml else 0
    streak = consecutive_streak_days(user.id, user.daily_goal_ml)
    return render_template("index.html", user=user, today_total=int(today_total), pct=pct, streak=streak)

@app.route("/history")
def history():
    user = get_or_create_user()
    days = int(request.args.get("days", 14))
    labels = []
    values = []
    goal = user.daily_goal_ml
    for i in range(days-1, -1, -1):
        d = date.today() - timedelta(days=i)
        labels.append(d.strftime("%b %d"))
        values.append(total_intake_for_day(user.id, d))
    return render_template("history.html", user=user, labels=labels, values=values, goal=goal, days=days)

@app.route("/set-goal", methods=["POST"])
def set_goal():
    user = get_or_create_user()
    try:
        new_goal = int(request.form.get("daily_goal_ml", "0"))
    except ValueError:
        flash("Invalid goal", "error")
        return redirect(url_for("index"))
    new_goal = max(250, min(new_goal, 10000))
    user.daily_goal_ml = new_goal
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/log", methods=["POST"])
def log():
    user = get_or_create_user()
    try:
        amt = int(request.form.get("amount_ml", "0"))
    except ValueError:
        flash("Invalid amount", "error")
        return redirect(url_for("index"))
    amt = max(50, min(amt, 2000))
    entry = WaterLog(user_id=user.id, amount_ml=amt, logged_at=datetime.utcnow())
    db.session.add(entry)
    db.session.commit()
    return redirect(url_for("index"))

# --------- JSON API ---------
@app.route("/api/log", methods=["POST"])
def api_log():
    user = get_or_create_user()
    data = request.get_json(force=True, silent=True) or {}
    try:
        amt = int(data.get("amount_ml", 0))
    except (ValueError, TypeError):
        return jsonify({"ok": False, "error": "invalid amount"}), 400
    amt = max(50, min(amt, 2000))
    entry = WaterLog(user_id=user.id, amount_ml=amt, logged_at=datetime.utcnow())
    db.session.add(entry)
    db.session.commit()
    # compute updated stats
    start, end = today_range()
    today_total = db.session.query(func.coalesce(func.sum(WaterLog.amount_ml), 0)).filter(
        WaterLog.user_id == user.id,
        WaterLog.logged_at >= start,
        WaterLog.logged_at < end,
    ).scalar() or 0
    pct = min(100, int(round((today_total / user.daily_goal_ml) * 100))) if user.daily_goal_ml else 0
    streak = consecutive_streak_days(user.id, user.daily_goal_ml)
    return jsonify({"ok": True, "today_total": int(today_total), "goal": user.daily_goal_ml, "pct": pct, "streak": streak})

@app.route("/api/stats")
def api_stats():
    user = get_or_create_user()
    days = int(request.args.get("days", 7))
    out = []
    for i in range(days-1, -1, -1):
        d = date.today() - timedelta(days=i)
        out.append({
            "date": d.isoformat(),
            "total": total_intake_for_day(user.id, d),
            "goal": user.daily_goal_ml,
        })
    return jsonify(out)

# --------- Reset today's logs ---------
@app.route("/api/reset", methods=["POST"])
def api_reset():
    user = get_or_create_user()
    start, end = today_range()
    WaterLog.query.filter(
        WaterLog.user_id == user.id,
        WaterLog.logged_at >= start,
        WaterLog.logged_at < end,
    ).delete()
    db.session.commit()
    return jsonify({
        "ok": True,
        "today_total": 0,
        "pct": 0,
        "streak": consecutive_streak_days(user.id, user.daily_goal_ml)
    })

# ----------------- Run -----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        get_or_create_user()
    app.run(host="0.0.0.0", port=5000, debug=True)