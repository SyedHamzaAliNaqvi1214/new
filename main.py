import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os
import ssl
import smtplib
from email.message import EmailMessage
from typing import List, Dict, Optional



# ==========================================================
# CONFIG
# ==========================================================
DATA_FILE = "Gym_database_1.txt"
ATTENDANCE_FILE = "attendance.txt"
REMINDER_LOG_FILE = "reminders.txt"

FIELD_ORDER = [
    "ID","Name","Username","Password","DOB","Weight","Height",
    "BMI","Email","DayName","JoinDate","Days","Split",
    "PaymentDate","FeeStatus"
]

SMTP_SERVER = os.getenv("SMTP_SERVER", "aizensol.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "hamza@aizensol.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "Softeng1999***")
DEFAULT_USE_REAL_EMAIL = False

# ==========================================================
# THEME TOGGLE
# ==========================================================
if "theme" not in st.session_state:
    st.session_state.theme = "light"

def apply_theme():
    if st.session_state.theme == "dark":
        st.markdown("""
        <style>
        body, .stApp { background-color:#0e1117; color:white; }
        .stMetric { background:#1f2937; padding:15px; border-radius:10px; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        body, .stApp { background-color:#f9fafb; color:black; }
        .stMetric { background:white; padding:15px; border-radius:10px; }
        </style>
        """, unsafe_allow_html=True)

apply_theme()

# ==========================================================
# FILE HELPERS
# ==========================================================
def read_all_records():
    if not os.path.exists(DATA_FILE):
        return []
    records=[]
    with open(DATA_FILE,"r",encoding="utf-8") as f:
        for line in f:
            parts=line.strip().split("\t")
            parts+=[""]*(len(FIELD_ORDER)-len(parts))
            records.append(dict(zip(FIELD_ORDER,parts)))
    return records

def write_all_records(records):
    with open(DATA_FILE,"w",encoding="utf-8") as f:
        for r in records:
            f.write("\t".join(str(r[k]) for k in FIELD_ORDER)+"\n")

def append_record(r):
    with open(DATA_FILE,"a",encoding="utf-8") as f:
        f.write("\t".join(str(r[k]) for k in FIELD_ORDER)+"\n")

# ==========================================================
# UTILITIES
# ==========================================================
def calculate_age(dob):
    try:
        d,m,y=map(int,dob.split("-"))
        today=datetime.today()
        return today.year-y
    except:
        return "--"

def compute_bmi(w,h):
    try:
        w=float(w); h=float(h)/100
        bmi=w/(h*h)
        return f"{bmi:.2f}"
    except:
        return "--"

def get_next_id(records):
    return max([int(r["ID"]) for r in records], default=0) + 1

# ==========================================================
# EMAIL REMINDER
# ==========================================================
def send_fee_reminder_ui(use_real=False):
    records=read_all_records()
    logs=[]
    for r in records:
        if r["FeeStatus"]!="PAID":
            logs.append(f"Reminder queued for {r['Name']}")
            if use_real and r["Email"]:
                msg=EmailMessage()
                msg["Subject"]="Gym Fee Reminder"
                msg["From"]=SENDER_EMAIL
                msg["To"]=r["Email"]
                msg.set_content(f"Hello {r['Name']}, please pay your gym fee.")
                try:
                    with smtplib.SMTP_SSL(SMTP_SERVER,SMTP_PORT) as s:
                        s.login(SENDER_EMAIL,SENDER_PASSWORD)
                        s.send_message(msg)
                    logs.append("Email sent")
                except Exception as e:
                    logs.append(str(e))
    return logs

# ==========================================================
# STREAMLIT UI
# ==========================================================
st.set_page_config("Gym Manager",layout="wide")

st.sidebar.title("🏋️ Gym Manager")

theme_btn = st.sidebar.toggle("🌙 Dark Mode", value=st.session_state.theme=="dark")
st.session_state.theme = "dark" if theme_btn else "light"
apply_theme()

menu = st.sidebar.radio("Menu",[
    "Dashboard","Register Member","View Members",
    "Attendance","Update Fees","Unpaid Members",
    "Send Fee Reminders"
])

# ==========================================================
# DASHBOARD
# ==========================================================
if menu=="Dashboard":
    st.title("🏋️Jawood Janjua Gym Management Dashboard")
    records=read_all_records()
    total=len(records)
    paid=len([r for r in records if r["FeeStatus"]=="PAID"])
    unpaid=total-paid

    c1,c2,c3=st.columns(3)
    c1.metric("Total Members",total)
    c2.metric("Paid",paid)
    c3.metric("Unpaid",unpaid)

    if total>0:
        fig,ax=plt.subplots()
        ax.pie([paid,unpaid],labels=["Paid","Unpaid"],autopct="%1.1f%%")
        ax.set_title("Fee Status")
        st.pyplot(fig)

# ==========================================================
# REGISTER
# ==========================================================
elif menu=="Register Member":
    st.subheader("Register New Member")
    with st.form("reg"):
        name=st.text_input("Name")
        dob=st.text_input("DOB dd-mm-yyyy")
        weight=st.text_input("Weight")
        height=st.text_input("Height")
        email=st.text_input("Email")
        submit=st.form_submit_button("Register")

    if submit:
        recs=read_all_records()
        new={
            "ID":str(get_next_id(recs)),
            "Name":name,
            "Username":"",
            "Password":"",
            "DOB":dob,
            "Weight":weight,
            "Height":height,
            "BMI":compute_bmi(weight,height),
            "Email":email,
            "DayName":datetime.now().strftime("%A"),
            "JoinDate":datetime.now().strftime("%d-%m-%Y"),
            "Days":"0",
            "Split":"1",
            "PaymentDate":"",
            "FeeStatus":"NOT PAID"
        }
        append_record(new)
        st.success("Member Registered")

# ==========================================================
# VIEW MEMBERS
# ==========================================================
elif menu=="View Members":
    recs=read_all_records()
    if recs:
        df=pd.DataFrame(recs)
        df["Age"]=df["DOB"].apply(calculate_age)
        st.dataframe(df)
    else:
        st.info("No records")

# ==========================================================
# ATTENDANCE
# ==========================================================
elif menu=="Attendance":
    recs=read_all_records()
    ids=[r["ID"] for r in recs]
    chosen=st.multiselect("Select IDs",ids)
    if st.button("Mark Attendance"):
        for r in recs:
            if r["ID"] in chosen:
                r["Days"]=str(int(r["Days"])+1)
        write_all_records(recs)
        st.success("Attendance marked")

# ==========================================================
# UPDATE FEES
# ==========================================================
elif menu=="Update Fees":
    id_text=st.text_input("IDs comma separated")
    if st.button("Mark Paid"):
        recs=read_all_records()
        ids=id_text.split(",")
        for r in recs:
            if r["ID"] in ids:
                r["FeeStatus"]="PAID"
                r["PaymentDate"]=datetime.now().strftime("%d-%m-%Y")
        write_all_records(recs)
        st.success("Updated")

# ==========================================================
# UNPAID
# ==========================================================
elif menu=="Unpaid Members":
    recs=[r for r in read_all_records() if r["FeeStatus"]!="PAID"]
    st.dataframe(pd.DataFrame(recs))

# ==========================================================
# SEND REMINDER
# ==========================================================
elif menu=="Send Fee Reminders":
    use_real=st.checkbox("Actually send emails")
    if st.button("Send"):
        logs=send_fee_reminder_ui(use_real)
        for l in logs:
            st.write(l)
