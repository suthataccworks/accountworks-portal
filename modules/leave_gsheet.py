import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
import datetime

def get_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )
    client = gspread.authorize(creds)
    sheet = client.open("LeaveManagement").worksheet("LeaveRequests")
    return sheet

def submit_leave(username, leave_type, start_date, end_date, reason):
    sheet = get_sheet()
    sheet.append_row([username, leave_type, str(start_date), str(end_date), reason, "Pending"])
    return True

def get_user_leaves(username):
    sheet = get_sheet()
    records = sheet.get_all_records()
    return [r for r in records if r["Username"] == username]
