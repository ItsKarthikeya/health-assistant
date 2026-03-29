import streamlit as st
import pandas as pd
import time
import schedule
from datetime import datetime

# -----------------------------
# Simple in-memory database
# -----------------------------
if 'medications' not in st.session_state:
    st.session_state.medications = []

if 'health_logs' not in st.session_state:
    st.session_state.health_logs = []

# -----------------------------
# UI Title
# -----------------------------
st.title("🩺 Personal Health Assistant")

# -----------------------------
# Sidebar Navigation
# -----------------------------
menu = st.sidebar.selectbox("Menu", [
    "Dashboard",
    "Add Medication",
    "Medication Tracker",
    "Fitness Tracker",
    "Health Info"
])

# -----------------------------
# Dashboard
# -----------------------------
if menu == "Dashboard":
    st.header("📊 Patient Dashboard")
    
    st.subheader("Today's Medications")
    for med in st.session_state.medications:
        st.write(f"💊 {med['name']} at {med['time']}")

    st.subheader("Health Logs")
    if st.session_state.health_logs:
        df = pd.DataFrame(st.session_state.health_logs)
        st.dataframe(df)
    else:
        st.write("No logs yet")

# -----------------------------
# Add Medication
# -----------------------------
elif menu == "Add Medication":
    st.header("➕ Add Medication")
    
    name = st.text_input("Medicine Name")
    time_input = st.time_input("Time")

    if st.button("Add"):
        st.session_state.medications.append({
            "name": name,
            "time": time_input.strftime("%H:%M")
        })
        st.success("Medication added!")

# -----------------------------
# Medication Tracker
# -----------------------------
elif menu == "Medication Tracker":
    st.header("💊 Medication List")
    
    for med in st.session_state.medications:
        st.write(f"{med['name']} - {med['time']}")

# -----------------------------
# Fitness Tracker
# -----------------------------
elif menu == "Fitness Tracker":
    st.header("🏃 Fitness Tracker")
    
    steps = st.number_input("Steps Walked", min_value=0)
    water = st.number_input("Water Intake (litres)", min_value=0.0)

    if st.button("Save Fitness Data"):
        st.session_state.health_logs.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "steps": steps,
            "water": water
        })
        st.success("Data saved!")

# -----------------------------
# Health Info (Basic Lookup)
# -----------------------------
elif menu == "Health Info":
    st.header("🔍 Health Information Lookup")
    
    query = st.text_input("Enter disease or medicine")

    if st.button("Search"):
        info = {
            "fever": "Fever is a temporary increase in body temperature.",
            "diabetes": "A chronic condition that affects blood sugar levels.",
            "paracetamol": "Used to treat pain and fever."
        }

        result = info.get(query.lower(), "No info found.")
        st.write(result)

# -----------------------------
# Reminder System (basic)
# -----------------------------
def check_reminders():
    current_time = datetime.now().strftime("%H:%M")
    for med in st.session_state.medications:
        if med['time'] == current_time:
            st.warning(f"⏰ Time to take {med['name']}")

schedule.every(1).minutes.do(check_reminders)