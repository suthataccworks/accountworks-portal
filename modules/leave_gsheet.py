import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    sheet = client.open("LeaveRequests").worksheet("leaves")  # ต้องมีไฟล์ Google Sheet ชื่อ LeaveRequests และแท็บชื่อ leaves
    return sheet

def submit_leave(username, leave_type, start_date, end_date, reason):
    sheet = get_sheet()
    sheet.append_row([username, leave_type, start_date, end_date, reason, "Pending"])

def get_all_leaves():
    sheet = get_sheet()
    return sheet.get_all_records()

def update_leave_status(username, status):
    sheet = get_sheet()
    records = sheet.get_all_records()
    for i, row in enumerate(records, start=2):
        if row["Username"] == username and row["Status"] == "Pending":
            sheet.update_cell(i, 6, status)  # คอลัมน์ 6 = Status
            break
