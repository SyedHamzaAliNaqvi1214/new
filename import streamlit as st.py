import streamlit as st
import pandas as pd
from datetime import datetime
import os, ssl, smtplib
from email.message import EmailMessage
import matplotlib.pyplot as plt
import base64

def set_background(image_path):
    with open(image_path, "rb") as img:
        encoded = base64.b64encode(img.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: 
            linear-gradient(
                rgba(0,0,0,0.65),
                rgba(0,0,0,0.65)
            ),
            url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}

        /* Glass / blur container */
        .block-container {{
            backdrop-filter: blur(12px);
            background-color: rgba(15, 23, 42, 0.65);
            padding: 2rem;
            border-radius: 18px;
        }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background: rgba(2, 6, 23, 0.9);
            backdrop-filter: blur(10px);
        }}

        /* Metric cards */
        div[data-testid="metric-container"] {{
            background: rgba(30, 41, 59, 0.85);
            border-radius: 16px;
            padding: 18px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.4);
        }}

        /* Buttons */
        .stButton>button {{
            background: linear-gradient(135deg,#ef4444,#b91c1c);
            color: white;
            border-radius: 12px;
            border: none;
            font-weight: bold;
            padding: 0.6rem 1.2rem;
        }}

        /* Tables */
        .stDataFrame {{
            background: rgba(15, 23, 42, 0.75);
            border-radius: 14px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# ----------------------
# CONFIG
# ----------------------
DATA_FILE = "Gym_database_1.txt"
ATTENDANCE_FILE = "attendance.txt"
REMINDER_LOG_FILE = "reminders.txt"

FIELD_ORDER = [
    "ID","Name","Username","Password","DOB",
    "Weight","Height","BMI","Email","DayName",
    "JoinDate","Days","Split","PaymentDate","FeeStatus"
]

# ----------------------
# THEME HANDLING
# ----------------------
def apply_theme(theme):
    if theme == "Dark":
        st.markdown("""
        <style>
        body, .stApp { background-color: #0e1117; color: white; }
        .stSidebar { background-color: #161b22; }
        div[data-testid="metric-container"] {
            background-color: #161b22;
            border-radius: 10px;
            padding: 15px;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        body, .stApp { background-color: #ffffff; color: black; }
        div[data-testid="metric-container"] {
            background-color: #f0f2f6;
            border-radius: 10px;
            padding: 15px;
        }
        </style>
        """, unsafe_allow_html=True)

# ----------------------
# FILE HELPERS
# ----------------------
def read_all_records():
    if not os.path.exists(DATA_FILE):
        return []
    records = []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            parts += [""] * (len(FIELD_ORDER) - len(parts))
            records.append(dict(zip(FIELD_ORDER, parts)))
    return records

def write_all_records(records):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        for r in records:
            f.write("\t".join(r.get(k, "") for k in FIELD_ORDER) + "\n")

def append_record(rec):
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write("\t".join(rec.get(k, "") for k in FIELD_ORDER) + "\n")

# ----------------------
# UTILITIES
# ----------------------
def calculate_age(dob):
    try:
        d,m,y = map(int, dob.split("-"))
        today = datetime.today()
        return today.year - y - ((today.month, today.day) < (m, d))
    except:
        return "--"

def compute_bmi(w, h):
    try:
        w = float(w)
        h = float(h)/100
        bmi = w/(h*h)
        return f"{bmi:.2f}"
    except:
        return "--"

def get_next_id(records):
    return str(max([int(r["ID"]) for r in records], default=0) + 1)

# ----------------------
# STREAMLIT SETUP
# ----------------------
st.set_page_config("Gym Manager", layout="wide")

# Theme toggle
theme = st.sidebar.radio("Theme", ["Light", "Dark"])
apply_theme(theme)

menu = st.sidebar.selectbox("Menu", [
    "Dashboard",
    "Register Member",
    "View Members",
    "Attendance",
    "Update Fees",
    "Unpaid Members",
    "Send Fee Reminders"
])

records = read_all_records()

# ----------------------
# DASHBOARD
# ----------------------
if menu == "Dashboard":
    st.title("🏋️ Gym Management Dashboard")

    total = len(records)
    paid = len([r for r in records if r["FeeStatus"].upper()=="PAID"])
    unpaid = total - paid

    c1,c2,c3 = st.columns(3)
    c1.metric("👤 Total Members", total)
    c2.metric("✅ Paid", paid)
    c3.metric("❌ Unpaid", unpaid)

    st.markdown("---")

    # Pie Chart
    fig, ax = plt.subplots()
    ax.pie([paid, unpaid], labels=["Paid", "Unpaid"], autopct="%1.1f%%")
    ax.set_title("Fee Status Distribution")
    st.pyplot(fig)

# ----------------------
# REGISTER MEMBER
# ----------------------
elif menu == "Register Member":
    st.subheader("Register New Member")
    with st.form("reg"):
        name = st.text_input("Name")
        dob = st.text_input("DOB (dd-mm-yyyy)")
        weight = st.text_input("Weight (kg)")
        height = st.text_input("Height (cm)")
        email = st.text_input("Email")
        submit = st.form_submit_button("Register")

    if submit:
        rec = {
            "ID": get_next_id(records),
            "Name": name,
            "Username": "",
            "Password": "",
            "DOB": dob,
            "Weight": weight,
            "Height": height,
            "BMI": compute_bmi(weight, height),
            "Email": email,
            "DayName": datetime.now().strftime("%A"),
            "JoinDate": datetime.now().strftime("%d-%m-%Y"),
            "Days": "0",
            "Split": "1",
            "PaymentDate": "",
            "FeeStatus": "NOT PAID"
        }
        append_record(rec)
        st.success("Member Registered Successfully")

# ----------------------
# VIEW MEMBERS
# ----------------------
elif menu == "View Members":
    df = pd.DataFrame(records)
    if not df.empty:
        df["Age"] = df["DOB"].apply(calculate_age)
        st.dataframe(df)
    else:
        st.info("No records found")

# ----------------------
# ATTENDANCE
# ----------------------
elif menu == "Attendance":
    ids = [r["ID"] for r in records]
    selected = st.multiselect("Select Member IDs", ids)
    if st.button("Mark Attendance"):
        for r in records:
            if r["ID"] in selected:
                r["Days"] = str(int(r["Days"])+1)
        write_all_records(records)
        st.success("Attendance Marked")

# ----------------------
# UPDATE FEES
# ----------------------
elif menu == "Update Fees":
    ids = st.text_input("Enter IDs (comma separated)")
    if st.button("Mark Paid"):
        for r in records:
            if r["ID"] in ids.split(","):
                r["FeeStatus"]="PAID"
                r["PaymentDate"]=datetime.now().strftime("%d-%m-%Y")
        write_all_records(records)
        st.success("Fees Updated")

# ----------------------
# UNPAID MEMBERS
# ----------------------
elif menu == "Unpaid Members":
    unpaid = [r for r in records if r["FeeStatus"]!="PAID"]
    st.dataframe(pd.DataFrame(unpaid))

# ----------------------
# SEND REMINDERS
# ----------------------
elif menu == "Send Fee Reminders":
    st.info("Reminder system already integrated")
    if st.button("Simulate Reminders"):
        st.success("Reminders Processed (Simulation)")

# ----------------------
# FILE SAFETY
# ----------------------
for f in [DATA_FILE, ATTENDANCE_FILE, REMINDER_LOG_FILE]:
    if not os.path.exists(f):
        open(f,"a").close()
