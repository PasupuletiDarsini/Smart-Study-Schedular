Smart Study Scheduler (Streamlit App)

A modern, neon–themed AI-powered study scheduler built with Streamlit.  
Includes login/sign-up, persistent user data, dynamic planners, weekly reports, and more.

---

## 🚀 Features
- Beautiful dark neon UI
- Login / Signup / Forgot Password functionality
- AI-based study plan generation
- Persistent user data stored in `/data`
- Task tracking, weekly reports, profile settings
- Works fully offline

---

## 📦 Requirements

Install dependencies using:

pip install -r requirements.txt

---

## ▶️ Run the App

After installing dependencies, run:

streamlit run app.py

The app will open in your browser at:

http://localhost:8501

---

## 📁 Project Structure

├── app.py ├── requirements.txt ├── README.md └── data/ ├── users.json └── <user files auto-created>

---

## 📝 Notes

- Streamlit automatically creates the UI.
- The `data/` folder is used for saving user accounts and study plans.
- You can delete data files anytime to reset the app.
