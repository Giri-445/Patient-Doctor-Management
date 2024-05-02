import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

conn = sqlite3.connect("medical_appointments.db")
c = conn.cursor()


c.execute(
    """
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        phone TEXT
    )
    """
)
c.execute(
    """
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY,
        patient_id INTEGER,
        provider TEXT,
        date_time DATETIME,
        status TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )
    """
)
conn.commit()


st.title("Medical Appointment Scheduler")


st.header("Add New Patient")
patient_name = st.text_input("Name")
patient_email = st.text_input("Email")
patient_phone = st.text_input("Phone")
if st.button("Add Patient"):
    c.execute("INSERT INTO patients (name, email, phone) VALUES (?, ?, ?)", (patient_name, patient_email, patient_phone))
    conn.commit()
    st.success("Patient added.")


st.header("Schedule Appointment")
patients = c.execute("SELECT * FROM patients").fetchall()
patient_options = {p[1]: p[0] for p in patients}
selected_patient = st.selectbox("Select Patient", list(patient_options.keys()))
provider = st.text_input("Healthcare Provider")
appointment_datetime = st.date_input("Appointment Date", min_value=datetime.today().date())
appointment_time = st.time_input("Appointment Time")
appointment_datetime_full = datetime.combine(appointment_datetime, appointment_time)

if st.button("Schedule Appointment"):
    c.execute(
        "INSERT INTO appointments (patient_id, provider, date_time, status) VALUES (?, ?, ?, ?)",
        (patient_options[selected_patient], provider, appointment_datetime_full, "Scheduled"),
    )
    conn.commit()
    st.success("Appointment scheduled.")


st.header("Send Appointment Reminders")
reminder_days = st.slider("Remind before (days)", 1, 7, 1)
upcoming_appointments = c.execute(
    "SELECT a.id, p.name, p.email, a.date_time, a.provider FROM appointments a "
    "JOIN patients p ON a.patient_id = p.id "
    "WHERE a.date_time BETWEEN ? AND ?",
    (datetime.now(), datetime.now() + timedelta(days=reminder_days)),
).fetchall()

if st.button("Send Reminders"):
    for appointment in upcoming_appointments:
        patient_name = appointment[1]
        patient_email = appointment[2]
        appointment_time = appointment[3]
        provider_name = appointment[4]


        email_subject = f"Appointment Reminder for {patient_name}"
        email_body = f"Dear {patient_name},\n\nThis is a reminder that you have an appointment with {provider_name} on {appointment_time}.\n\nBest regards,\nYour Healthcare Team"
        msg = MIMEText(email_body)
        msg["Subject"] = email_subject
        msg["From"] = "your_email@example.com"
        msg["To"] = patient_email


        try:
            smtp_server = "smtp.example.com"
            smtp_port = 587
            smtp_user = "your_email@example.com"
            smtp_pass = "your_email_password"
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, [patient_email], msg.as_string())
            st.success(f"Reminder sent to {patient_name}.")
        except Exception as e:
            st.error(f"Error sending reminder: {e}")


st.header("Patient Records")
patient_records = c.execute("SELECT * FROM patients").fetchall()
for patient in patient_records:
    st.write(f"Name: {patient[1]}, Email: {patient[2]}, Phone: {patient[3]}")


st.header("Appointment History")
appointment_records = c.execute(
    "SELECT a.id, p.name, a.date_time, a.provider, a.status FROM appointments a "
    "JOIN patients p ON a.patient_id = p.id"
).fetchall()

for appointment in appointment_records:
    st.write(
        f"Patient: {appointment[1]}, Appointment: {appointment[2]}, Provider: {appointment[3]}, Status: {appointment[4]}"
    )
