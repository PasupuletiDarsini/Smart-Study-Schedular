# app.py
"""
Smart Study Scheduler — Streamlit app (UI refresh + conditional Auth forms)
- Improved dark neon / violet UI
- Login page shows only login initially; "Create account" and "Forgot password"
  are revealed only when the user clicks their buttons.
- All buttons and flows work without using st.experimental_rerun()
- Disk persistence kept (data/ folder)
Save and run with: streamlit run app.py
"""

import streamlit as st
import json
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np

# -------------------------
# Persistence helpers
# -------------------------
DATA_DIR = Path("data")
USERS_FILE = DATA_DIR / "users.json"

def ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)

def load_users_file():
    ensure_data_dir()
    if USERS_FILE.exists():
        try:
            with USERS_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_users_file(users):
    ensure_data_dir()
    with USERS_FILE.open("w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def user_file(username):
    ensure_data_dir()
    return DATA_DIR / f"{username}.json"

def load_user_data(username):
    p = user_file(username)
    if p.exists():
        try:
            with p.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def save_user_data(username, data):
    ensure_data_dir()
    p = user_file(username)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# -------------------------
# Page config and rich theme CSS
# -------------------------
st.set_page_config(page_title="Smart Study Scheduler", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap" rel="stylesheet">
    <style>
    :root{
      --bg:#05040b;
      --panel:#0b0820;
      --card:#0e0826;
      --muted:#9aa5b1;
      --accent:#8b5cf6;    /* violet */
      --accent2:#7c3aed;
      --accent3:#00e5ff;
      --glass: rgba(255,255,255,0.03);
      --text:#e6eef3;
    }
    html,body, [data-testid="stAppViewContainer"] { background: radial-gradient(900px 600px at 10% 10%, rgba(124,58,237,0.06), transparent 6%), radial-gradient(700px 400px at 90% 90%, rgba(0,229,255,0.02), transparent 6%), var(--bg) !important; color:var(--text) !important; font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial; }
    /* Sidebar */
    [data-testid="stSidebar"] { background: linear-gradient(180deg, rgba(12,9,30,0.96), rgba(8,6,24,0.96)); border-right: 1px solid rgba(255,255,255,0.03); padding:18px; color:var(--muted); }
    /* Header & cards */
    .card { background: linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.00)); border: 1px solid rgba(255,255,255,0.04); padding:16px; border-radius:12px; box-shadow: 0 8px 30px rgba(2,4,20,0.6); }
    .header-title { color:var(--text); font-weight:700; font-size:1.1rem; }
    .muted { color:var(--muted); font-size:0.95rem; }
    .small { color:var(--muted); font-size:0.85rem; }
    /* Buttons */
    .stButton>button { background: linear-gradient(90deg,var(--accent), var(--accent2)); color: #021024; border: none; padding:10px 14px; border-radius:10px; font-weight:700; box-shadow: 0 8px 22px rgba(124,58,237,0.12); }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 12px 30px rgba(124,58,237,0.18); }
    /* Secondary ghost buttons */
    .ghost-btn { background: transparent !important; color: var(--muted) !important; border: 1px solid rgba(255,255,255,0.04) !important; padding:6px 10px !important; border-radius:8px !important; }
    /* Inputs */
    input, textarea, select { background: rgba(255,255,255,0.02) !important; border: 1px solid rgba(255,255,255,0.03) !important; color: var(--text) !important; border-radius:8px !important; padding:8px !important; }
    /* Nice focus ring */
    input:focus, textarea:focus, select:focus { outline: none; box-shadow: 0 0 0 4px rgba(124,58,237,0.12); border-color: var(--accent2) !important; }
    /* Metrics */
    .metric { display:flex; gap:12px; align-items:center; }
    .logo-mark{ width:44px; height:44px; border-radius:10px; background: linear-gradient(135deg,var(--accent2), var(--accent3)); box-shadow: 0 8px 30px rgba(124,58,237,0.12); display:inline-block; vertical-align:middle; }
    /* subtle animations */
    .fade-in { animation: fadeIn 0.45s ease both; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(6px);} to { opacity:1; transform: none; } }
    /* card small title */
    .card h3 { color: var(--accent2); margin-top:0; margin-bottom:6px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# Initialize session state and disk caches
# -------------------------
ensure_data_dir()
disk_users = load_users_file()
if "init" not in st.session_state:
    st.session_state.init = True
    if disk_users:
        st.session_state.users = disk_users
    else:
        st.session_state.users = {
            "user1": {
                "name": "Alex Kumar",
                "username": "user1",
                "email": "alex@example.com",
                "password": "pass123",
                "photo": None,
                "goal_hours_per_day": 3.0,
            }
        }
        save_users_file(st.session_state.users)

    st.session_state.logged_in = None
    st.session_state.subjects = {}
    st.session_state.plans = {}
    st.session_state.progress = {}
    st.session_state.streaks = {}
    st.session_state.notifications = {}

    # show_signup / show_forgot flags control the visibility of those forms on the login page
    st.session_state.show_signup = False
    st.session_state.show_forgot = False

    # load per-user files if exist
    for uname in st.session_state.users.keys():
        ud = load_user_data(uname)
        if ud:
            st.session_state.subjects[uname] = ud.get("subjects", [])
            st.session_state.plans[uname] = ud.get("plan", None)
            st.session_state.progress[uname] = ud.get("progress", [])
            st.session_state.streaks[uname] = ud.get("streaks", {"current": 0, "best": 0})
            st.session_state.notifications[uname] = ud.get("notifications", [])
        else:
            st.session_state.subjects[uname] = []
            st.session_state.plans[uname] = None
            st.session_state.progress[uname] = []
            st.session_state.streaks[uname] = {"current": 0, "best": 0}
            st.session_state.notifications[uname] = []

# -------------------------
# Helpers
# -------------------------
def ensure_user_storage(username):
    if username is None:
        return
    st.session_state.subjects.setdefault(username, [])
    st.session_state.plans.setdefault(username, None)
    st.session_state.progress.setdefault(username, [])
    st.session_state.streaks.setdefault(username, {"current": 0, "best": 0})
    st.session_state.notifications.setdefault(username, [])

def persist_user(username):
    try:
        payload = {
            "subjects": st.session_state.subjects.get(username, []),
            "plan": st.session_state.plans.get(username),
            "progress": st.session_state.progress.get(username, []),
            "streaks": st.session_state.streaks.get(username, {"current": 0, "best": 0}),
            "notifications": st.session_state.notifications.get(username, []),
            "saved_at": datetime.utcnow().isoformat(),
        }
        save_user_data(username, payload)
    except Exception as e:
        st.error(f"Failed to persist user data: {e}")

def persist_users_global():
    try:
        save_users_file(st.session_state.users)
    except Exception as e:
        st.error(f"Failed to save users list: {e}")

def uid(prefix="id"):
    return prefix + "_" + uuid.uuid4().hex[:8]

def today_iso():
    return datetime.utcnow().date().isoformat()

# -------------------------
# Planner algorithm
# -------------------------
def pick_focus_note(subject_name):
    tips = [
        "Focus on problem solving",
        "Review weak topics first",
        "Practice previous questions",
        "Do a short self-quiz",
        "Summarize key formulas",
        "Teach this topic to an imaginary friend",
    ]
    idx = sum(ord(c) for c in subject_name) % len(tips)
    return tips[idx]

def smart_generate_plan(subjects, hours_per_day, days, exam_date=None, focus_subjects=None):
    weights = {"easy": 1.0, "medium": 1.5, "hard": 2.5}
    scores = []
    for s in subjects:
        w = weights.get(s.get("difficulty", "medium"), 1.5)
        urgency = 1.0
        if exam_date:
            try:
                days_until_exam = max((exam_date - datetime.utcnow()).days, 0)
            except Exception:
                days_until_exam = 0
            if days_until_exam <= 7:
                urgency += (8 - days_until_exam) * 0.12
            elif days_until_exam <= 30:
                urgency += (30 - days_until_exam) * 0.03
        boost = 1.15 if focus_subjects and s["name"] in focus_subjects else 1.0
        scores.append((s["name"], w * urgency * boost))

    total_score = sum(s for _, s in scores) or 1.0
    total_hours = float(hours_per_day) * int(days)
    subj_totals = {name: max(0.5, round((score / total_score) * total_hours, 2)) for name, score in scores}

    plan = {}
    subject_order = sorted(subj_totals.items(), key=lambda x: -x[1])

    for d in range(1, int(days) + 1):
        day_label = f"Day {d}"
        plan[day_label] = []
        remaining = float(hours_per_day)
        for name, _ in subject_order:
            if subj_totals.get(name, 0) <= 0.01:
                continue
            remaining_days = max(1, int(days) - d + 1)
            ideal_alloc = subj_totals[name] / remaining_days
            alloc = round(min(remaining, max(0.25, ideal_alloc)), 2)
            if alloc <= 0:
                continue
            plan[day_label].append({"subject": name, "hours": alloc, "note": pick_focus_note(name)})
            remaining -= alloc
            subj_totals[name] -= alloc
            if remaining <= 0.01:
                break
        if remaining > 0.01:
            plan[day_label].append({"subject": "Review & Breaks", "hours": round(remaining, 2), "note": "Light review / short breaks"})
    for d, tasks in list(plan.items()):
        plan[d] = [t for t in tasks if float(t.get("hours", 0)) > 0.0]
    return plan

# -------------------------
# Auth UI (now conditional)
# -------------------------
def page_signup_inline():
    st.markdown("<div class='card fade-in'>", unsafe_allow_html=True)
    st.header("Create Account")
    with st.form("signup_form"):
        name = st.text_input("Full name")
        username = st.text_input("Choose username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button("Create account")
    if submitted:
        if not username or not password or not email:
            st.error("Please fill required fields.")
            return
        if username in st.session_state.users:
            st.error("Username already taken.")
            return
        st.session_state.users[username] = {"name": name or username, "username": username, "email": email, "password": password, "photo": None, "goal_hours_per_day": 3.0}
        persist_users_global()
        ensure_user_storage(username)
        persist_user(username)
        st.success("Account created. You can now sign in.")
        # hide signup form after successful creation
        st.session_state.show_signup = False
    st.markdown("</div>", unsafe_allow_html=True)

def page_forgot_inline():
    st.markdown("<div class='card fade-in'>", unsafe_allow_html=True)
    st.header("Forgot Password")
    st.write("Enter your email. A reset link will be simulated and stored in your notifications.")
    with st.form("forgot_form"):
        email = st.text_input("Email")
        submitted = st.form_submit_button("Send reset link")
    if submitted:
        found = None
        for k, v in st.session_state.users.items():
            if v.get("email") == email:
                found = k
                break
        # We don't leak whether email exists
        token = uuid.uuid4().hex
        if found:
            st.session_state.notifications.setdefault(found, []).append(f"Password reset simulated: token {token}")
            persist_user(found)
        st.info("If the email exists, a reset link has been simulated and stored in Notifications.")
        st.session_state.show_forgot = False
    st.markdown("</div>", unsafe_allow_html=True)

def page_login():
    st.markdown("<div class='card fade-in'>", unsafe_allow_html=True)
    st.title("Smart Study Scheduler")
    st.markdown("<div style='display:flex;align-items:center;gap:12px'><div class='logo-mark'></div><div class='header-title'>Smart Study Scheduler</div></div>", unsafe_allow_html=True)
    st.markdown("<div class='small'>Sign in to continue</div>", unsafe_allow_html=True)
    st.markdown("---")
    # Login form (always visible)
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")
    if submitted:
        u = st.session_state.users.get(username)
        if u and u.get("password") == password:
            st.session_state.logged_in = username
            ensure_user_storage(username)
            # load per-user file if present
            ud = load_user_data(username)
            if ud:
                st.session_state.subjects[username] = ud.get("subjects", [])
                st.session_state.plans[username] = ud.get("plan", None)
                st.session_state.progress[username] = ud.get("progress", [])
                st.session_state.streaks[username] = ud.get("streaks", {"current": 0, "best": 0})
                st.session_state.notifications[username] = ud.get("notifications", [])
            persist_user(username)
            st.success("Signed in. Proceed to the app.")
            return
        else:
            st.error("Invalid credentials. Check username/password.")
    st.markdown("<div style='display:flex;gap:8px;margin-top:12px;'>", unsafe_allow_html=True)
    # Buttons to reveal signup / forgot forms
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("Create account", key="show_signup"):
            st.session_state.show_signup = True
            st.session_state.show_forgot = False
    with col2:
        if st.button("Forgot password", key="show_forgot"):
            st.session_state.show_forgot = True
            st.session_state.show_signup = False
    with col3:
        if st.button("Continue as demo user"):
            st.session_state.logged_in = "user1"
            ensure_user_storage("user1")
            ud = load_user_data("user1")
            if ud:
                st.session_state.subjects["user1"] = ud.get("subjects", [])
                st.session_state.plans["user1"] = ud.get("plan", None)
                st.session_state.progress["user1"] = ud.get("progress", [])
                st.session_state.streaks["user1"] = ud.get("streaks", {"current": 0, "best": 0})
                st.session_state.notifications["user1"] = ud.get("notifications", [])
            persist_user("user1")
            st.success("Signed in as demo user.")
            return
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# Main UI pieces
# -------------------------
def header(user):
    cols = st.columns([3, 1])
    with cols[0]:
        st.markdown(f"<div style='display:flex;align-items:center;gap:12px'><div class='logo-mark'></div><div class='header-title'>AI Study Scheduler</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='small'>Welcome, <strong>{user.get('name')}</strong> • @{user.get('username')}</div>", unsafe_allow_html=True)
    with cols[1]:
        col_img, col_btn = st.columns([1, 1])
        with col_img:
            if user.get("photo"):
                try:
                    img = Image.open(BytesIO(user["photo"])).convert("RGB").resize((64, 64))
                    st.image(img, width=64)
                except Exception:
                    st.image("https://via.placeholder.com/64/7c3aed/001122?text=U", width=64)
            else:
                st.image("https://via.placeholder.com/64/7c3aed/001122?text=U", width=64)
        with col_btn:
            st.write("")
            if st.button("Sign out"):
                st.session_state.logged_in = None
                # hide signup/forgot flags when signed out
                st.session_state.show_signup = False
                st.session_state.show_forgot = False
                return

def sidebar_menu():
    st.sidebar.markdown("## Navigation")
    page = st.sidebar.radio("", ["Dashboard", "Scheduler", "Tasks", "Weekly Report", "Profile", "Settings", "Help"])
    st.sidebar.markdown("---")
    u = st.session_state.logged_in
    ensure_user_storage(u)
    subs = st.session_state.subjects.get(u, [])
    plan = st.session_state.plans.get(u)
    hours_planned = 0.0
    if plan:
        try:
            for tasks in plan.values():
                for t in tasks:
                    hours_planned += float(t.get("hours", 0))
        except Exception:
            hours_planned = 0.0
    st.sidebar.markdown(f"*Subjects:* {len(subs)}  \n*Planned hrs:* {round(hours_planned,1)}")
    st.sidebar.markdown("---")
    st.sidebar.markdown("Theme: Dark • Violet • Neon")
    return page

# -------------------------
# Scheduler / Tasks / Report (same behavior as before)
# (Kept concise here; unchanged logic from prior working version)
# -------------------------
def page_scheduler(user):
    st.header("Scheduler")
    st.markdown("Create a personalized study schedule. The planner balances difficulty, upcoming exams and your daily hours.")

    cols = st.columns([2, 1])
    username = user["username"]

    with cols[0]:
        st.subheader("Subjects")
        subj_list = st.session_state.subjects.get(username, [])
        if subj_list:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            for s in subj_list:
                st.markdown(f"🧠 *{s['name']}* — {s['difficulty'].capitalize()}")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No subjects yet. Add some below.")

        with st.form("add_subject", clear_on_submit=True):
            st.markdown("##### Add New Subject")
            ncol = st.columns([3, 1])
            name = ncol[0].text_input("Subject name")
            diff = ncol[1].selectbox("Difficulty", ["easy", "medium", "hard"], label_visibility="collapsed")
            add = st.form_submit_button("Add subject")
        if add and name:
            st.session_state.subjects[username].append({"name": name, "difficulty": diff})
            persist_user(username)
            st.success(f"Added {name}")
            return

    with cols[1]:
        st.subheader("Plan settings")
        with st.form("plan_settings_form"):
            hours_per_day = st.number_input("Target Hours/Day", min_value=0.5, max_value=12.0, value=float(user.get("goal_hours_per_day", 3.0)), step=0.5)
            days = st.number_input("Days to plan", min_value=1, max_value=60, value=14, step=1)
            exam_date = st.date_input("Exam date (optional)", value=None)
            exam_dt = None
            if exam_date:
                try:
                    exam_dt = datetime.combine(exam_date, datetime.min.time())
                except Exception:
                    exam_dt = None
            st.markdown("---")
            st.markdown("### Priority subjects (optional)")
            priority = st.multiselect("Pick subjects to prioritize", [s["name"] for s in st.session_state.subjects.get(username, [])])
            if st.form_submit_button("Generate schedule", type="primary"):
                subs = st.session_state.subjects.get(username, [])
                if not subs:
                    st.error("Add at least one subject before generating a schedule.")
                else:
                    plan = smart_generate_plan(subs, float(hours_per_day), int(days), exam_dt, focus_subjects=priority)
                    st.session_state.plans[username] = plan
                    st.session_state.progress[username] = []
                    for day_label, tasks in plan.items():
                        st.session_state.progress[username].append({"day": day_label, "tasks": [t.copy() for t in tasks], "completed": False, "date": None})
                    persist_user(username)
                    st.success("Schedule generated and saved.")
                    return

    st.markdown("---")
    st.subheader("Quick actions")
    a1, a2, a3 = st.columns(3)
    if a1.button("Regenerate with same settings"):
        plan = st.session_state.plans.get(username)
        if not plan:
            st.warning("No existing plan to regenerate. Use Generate schedule.")
        else:
            days = len(plan)
            first = plan.get("Day 1", []) if isinstance(plan, dict) else []
            hours = sum(float(t.get("hours", 0)) for t in first) if first else user.get("goal_hours_per_day", 3.0)
            subs = st.session_state.subjects.get(username, [])
            plan_new = smart_generate_plan(subs, hours or user.get("goal_hours_per_day", 3.0), days or 14, None)
            st.session_state.plans[username] = plan_new
            st.session_state.progress[username] = []
            for day_label, tasks in plan_new.items():
                st.session_state.progress[username].append({"day": day_label, "tasks": [t.copy() for t in tasks], "completed": False, "date": None})
            persist_user(username)
            st.success("Schedule regenerated.")
            return

    if a2.button("Auto-fill example subjects"):
        st.session_state.subjects[username] = [
            {"name": "Mathematics", "difficulty": "hard"},
            {"name": "Physics", "difficulty": "hard"},
            {"name": "Chemistry", "difficulty": "medium"},
            {"name": "English Literature", "difficulty": "easy"},
            {"name": "Computer Science", "difficulty": "medium"},
        ]
        persist_user(username)
        st.success("Example subjects added.")
        return

    if a3.button("Clear schedule & subjects"):
        st.session_state.plans[username] = None
        st.session_state.subjects[username] = []
        st.session_state.progress[username] = []
        persist_user(username)
        st.success("Cleared all data.")
        return

def page_tasks(user):
    st.header("Tasks & Progress")
    username = user["username"]
    plan = st.session_state.plans.get(username)
    progress = st.session_state.progress.get(username, [])

    if not plan:
        st.info("No schedule available. Create one in Scheduler.")
        return

    st.subheader("Current Study Plan")
    for entry in progress.copy():
        day = entry["day"]
        status = "✅ Completed" if entry.get("completed") else "⏳ Pending"
        with st.expander(f"{status} — {day}", expanded=not entry.get("completed")):
            st.markdown(f"*Tasks for {day}:*")
            for idx, t in enumerate(entry.get("tasks", [])):
                st.markdown(f"- *{t['subject']}* ({t['hours']} hrs)  \n  <span class='small'>— {t.get('note','')}</span>", unsafe_allow_html=True)
            st.markdown("---")
            cols = st.columns([1, 1])
            if not entry.get("completed"):
                if cols[0].button(f"Mark {day} Complete", key=f"complete_{day}"):
                    entry["completed"] = True
                    entry["date"] = datetime.utcnow().isoformat()
                    s = st.session_state.streaks.get(username, {"current": 0, "best": 0})
                    s["current"] += 1
                    s["best"] = max(s["best"], s["current"])
                    st.session_state.streaks[username] = s
                    persist_user(username)
                    st.success(f"{day} marked complete. Your streak is now {s['current']} days!")
                    return
            else:
                if entry.get("date"):
                    try:
                        dt = datetime.fromisoformat(entry.get("date"))
                        cols[0].markdown(f"*Completed on:* {dt.strftime('%b %d, %Y')}")
                    except Exception:
                        cols[0].markdown("*Completed*")
            if cols[1].button(f"Skip {day} (Carry Forward)", key=f"skip_{day}"):
                if not entry.get("tasks"):
                    st.warning("This day has no tasks to skip.")
                    return
                idx_in_list = st.session_state.progress[username].index(entry)
                try:
                    next_label = f"Day {int(day.split()[1]) + 1}"
                except Exception:
                    next_label = day + " (tasks appended)"
                found_next = None
                for en in st.session_state.progress[username]:
                    if en["day"] == next_label:
                        found_next = en
                        break
                if found_next:
                    found_next["tasks"].extend([t.copy() for t in entry["tasks"]])
                else:
                    st.session_state.progress[username].insert(idx_in_list + 1, {"day": next_label, "tasks": [t.copy() for t in entry["tasks"]], "completed": False, "date": None})
                st.session_state.progress[username].remove(entry)
                persist_user(username)
                st.success(f"Tasks moved from {day} to {next_label}. Day skipped.")
                return

def page_report(user):
    st.header("Weekly Report")
    username = user["username"]
    progress = st.session_state.progress.get(username, [])

    if not progress:
        st.info("No progress tracked yet. Complete some tasks on the 'Tasks' page.")
        return

    subj_hours = {}
    completed_days = 0
    total_days = len(progress)
    for entry in progress:
        for t in entry.get("tasks", []):
            subj_hours[t["subject"]] = subj_hours.get(t["subject"], 0) + float(t.get("hours", 0))
        if entry.get("completed"):
            completed_days += 1

    total_hours = sum(subj_hours.values())
    completion_rate = round((completed_days / total_days) * 100, 1) if total_days else 0

    st.markdown("### Performance Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Completed Days", completed_days)
    c2.metric("Total Hours Planned", f"{round(total_hours,1)} hrs")
    c3.metric("Completion Rate", f"{completion_rate}%")

    st.markdown("---")
    st.markdown("### Planned Hours per Subject")
    if subj_hours:
        sorted_subj_hours = sorted(subj_hours.items(), key=lambda item: item[1], reverse=True)
        names = [item[0] for item in sorted_subj_hours]
        vals = [item[1] for item in sorted_subj_hours]
        cmap = plt.get_cmap("tab20")
        colors = cmap(np.linspace(0, 1, max(1, len(names))))
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(names, vals, color=colors)
        ax.set_ylabel("Hours", color="#e6eef3")
        ax.tick_params(axis="x", rotation=30, colors="#e6eef3")
        ax.tick_params(axis="y", colors="#e6eef3")
        fig.patch.set_facecolor("none")
        ax.set_facecolor("none")
        ax.spines["bottom"].set_color("#9aa5b1")
        ax.spines["left"].set_color("#9aa5b1")
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig)

    productivity = min(100, int((completion_rate * 0.6 + min(total_hours / 7, 6) * 10) / 1.6))
    st.markdown("### Productivity & Streaks")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.metric("Productivity Score", f"{productivity}%")
        pct = productivity / 100.0
        st.markdown(f"<div class='progress-bar'><div class='progress-fill' style='width:{int(pct*100)}%'></div></div>", unsafe_allow_html=True)
    with col2:
        s = st.session_state.streaks.get(username, {"current": 0, "best": 0})
        st.metric("Current Streak (days)", s["current"])
        st.metric("Best Streak", s["best"])
    st.markdown("---")
    st.markdown("### Subject Recommendations")
    if subj_hours:
        min_sub = min(subj_hours.items(), key=lambda x: x[1])
        st.warning(f"⚠ *Focus Area:* Consider prioritizing *{min_sub[0]}* — only {min_sub[1]} hrs planned this period.")
    notes = st.session_state.notifications.get(username, [])
    if notes:
        st.markdown("### Notifications")
        for n in notes[::-1][:5]:
            st.info(n)

# -------------------------
# Profile & settings
# -------------------------
def page_profile(user):
    st.header("Profile")
    username = user["username"]
    if user.get("photo"):
        try:
            st.image(Image.open(BytesIO(user["photo"])).resize((128, 128)), width=128)
        except Exception:
            st.image("https://via.placeholder.com/128/7c3aed/001122?text=U", width=128)
    else:
        st.image("https://via.placeholder.com/128/7c3aed/001122?text=U", width=128)
    with st.form("profile_form"):
        st.subheader("Personal Details")
        name = st.text_input("Name", value=user.get("name", ""))
        email = st.text_input("Email", value=user.get("email", ""))
        st.subheader("Goals")
        goal = st.number_input("Target study hours per day", min_value=0.5, max_value=12.0, value=float(user.get("goal_hours_per_day", 3.0)), step=0.5)
        photo = st.file_uploader("Change profile photo", type=["png", "jpg", "jpeg"])
        save = st.form_submit_button("Save profile", type="primary")
    if save:
        user["name"] = name or user["name"]
        user["email"] = email or user["email"]
        user["goal_hours_per_day"] = float(goal)
        if photo:
            user["photo"] = photo.read()
        st.session_state.users[username] = user
        persist_users_global()
        ensure_user_storage(username)
        persist_user(username)
        st.success("Profile updated.")
        return

def page_settings(user):
    st.header("Settings")
    with st.form("prefs"):
        reminder = st.checkbox("Enable daily reminders (simulated)", value=True)
        sound = st.checkbox("Enable notification sounds (simulated)", value=False)
        save = st.form_submit_button("Save", type="primary")
    if save:
        username = user["username"]
        st.session_state.notifications.setdefault(username, []).append("Preferences updated: Reminders=" + ("On" if reminder else "Off"))
        persist_user(username)
        st.success("Preferences saved.")
        return

def page_help(user):
    st.header("Help & Walkthrough")
    st.markdown("""
    This is a local Smart Study Scheduler.
    - Use "Scheduler" to create plans.
    - Use "Tasks" to mark completion.
    - Plans persist to the `data/` folder.
    - For advanced AI-driven natural-language plans, we can integrate an LLM (requires API key).
    """)

# -------------------------
# Router / main
# -------------------------
def run_app():
    # If logged out, show only login and optionally signup/forgot inline
    if st.session_state.logged_in is None:
        # show focused login area centered
        left, center, right = st.columns([1, 2, 1])
        with center:
            page_login()
            # show signup and forgot inline forms conditionally
            if st.session_state.show_signup:
                page_signup_inline()
            if st.session_state.show_forgot:
                page_forgot_inline()
        st.stop()

    # logged in
    username = st.session_state.logged_in
    user = st.session_state.users.get(username)
    ensure_user_storage(username)

    header(user)
    page = sidebar_menu()

    if page == "Dashboard":
        st.header("Overview")
        subs = st.session_state.subjects.get(username, [])
        plan = st.session_state.plans.get(username)
        total_days = len(plan) if plan else 0
        total_planned_hrs = 0.0
        completed_days = 0
        for p in st.session_state.progress.get(username, []):
            for t in p.get("tasks", []):
                total_planned_hrs += float(t.get("hours", 0))
            if p.get("completed"):
                completed_days += 1
        st.markdown('<div class="card">', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Subjects Tracked", len(subs))
        c2.metric("Total Days Planned", total_days)
        c3.metric("Total Planned Hours", round(total_planned_hrs, 1))
        c4.metric("Days Completed", completed_days)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("### Today's Focus")
        focus = None
        plan_list = st.session_state.progress.get(username, [])
        if plan_list:
            active_day = next((item for item in plan_list if not item.get("completed")), None)
            if active_day and active_day.get("tasks"):
                active_day["tasks"].sort(key=lambda x: x.get("hours", 0), reverse=True)
                focus = active_day["tasks"][0]["subject"]
                note = active_day["tasks"][0]["note"]
        if focus:
            st.markdown(f"*Main Focus:* <span style='color:var(--accent); font-size:1.2em;'>{focus}</span>", unsafe_allow_html=True)
            st.info(f"💡 *Tip:* {note}")
        else:
            st.info("No active tasks! Generate a schedule in the Scheduler page.")
    elif page == "Scheduler":
        page_scheduler(user)
    elif page == "Tasks":
        page_tasks(user)
    elif page == "Weekly Report":
        page_report(user)
    elif page == "Profile":
        page_profile(user)
    elif page == "Settings":
        page_settings(user)
    elif page == "Help":
        page_help(user)

if __name__ == "__main__":
    run_app()
