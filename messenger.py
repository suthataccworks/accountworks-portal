import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import datetime

# ================= CONFIG =================
SHEET_NAME = "MessengerBooking"      # ชื่อไฟล์ Google Sheet
WORKSHEET = "Sheet1"                 # ชื่อแผ่นงาน
TIME_SLOTS = ["09:00:00","10:00:00","11:00:00","13:00:00","14:00:00","15:00:00","16:00:00"]

# ------------- Google Sheet helpers -------------
def get_sheet():
    SCOPE = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", SCOPE)
    client = gspread.authorize(creds)
    try:
        return client.open(SHEET_NAME).worksheet(WORKSHEET)
    except gspread.exceptions.WorksheetNotFound:
        sh = client.open(SHEET_NAME)
        ws = sh.add_worksheet(title=WORKSHEET, rows="1000", cols="9")
        ws.append_row(["Timestamp","Booking Date","Booking Time","Company","Pickup","Dropoff","Phone","Note","User"])
        return ws

def read_df():
    ws = get_sheet()
    records = ws.get_all_records()
    df = pd.DataFrame(records)
    if df.empty:
        return df, ws
    # normalize column names
    rename_map = {}
    for c in df.columns:
        low = c.lower().strip()
        if low == "timestamp": rename_map[c] = "Timestamp"
        if low == "booking date": rename_map[c] = "Booking Date"
        if low == "booking time": rename_map[c] = "Booking Time"
        if low == "company": rename_map[c] = "Company"
        if low == "pickup": rename_map[c] = "Pickup"
        if low == "dropoff": rename_map[c] = "Dropoff"
        if low == "phone": rename_map[c] = "Phone"
        if low == "note": rename_map[c] = "Note"
        if low == "user": rename_map[c] = "User"
    df = df.rename(columns=rename_map)

    df["Booking Date"] = pd.to_datetime(df["Booking Date"], errors="coerce")
    df["Booking Time"] = pd.to_datetime(df["Booking Time"], errors="coerce").dt.strftime("%H:%M:%S")
    df["_row"] = (df.index + 2).astype(int)
    return df, ws

def current_week_bounds(today=None):
    if today is None:
        today = datetime.date.today()
    start = today - datetime.timedelta(days=today.weekday())
    end = start + datetime.timedelta(days=6)
    return start, end

# ------------- Booking core -------------
def is_conflict(df: pd.DataFrame, date_obj: datetime.date, time_str: str) -> bool:
    if df.empty:
        return False
    match = df[(df["Booking Date"].dt.date == date_obj) & (df["Booking Time"] == time_str)]
    return not match.empty

def append_booking(ws, date_obj, time_str, company, pickup, dropoff, phone, note, username):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ws.append_row([
        ts,
        date_obj.strftime("%Y-%m-%d"),
        time_str,
        company, pickup, dropoff, phone, note, username
    ])

def delete_booking(ws, row_index: int):
    ws.delete_rows(row_index)

# ------------- Views -------------
def booking_form(username: str):
    st.subheader("📝 จองคิวแมสเซ็นเจอร์")

    today = datetime.date.today()
    date_pick = st.date_input("เลือกวันที่", min_value=today, value=today)

    # filter time slots (ห้ามเลือกเวลาที่ผ่านไปแล้วของวันนี้)
    available_slots = TIME_SLOTS
    if date_pick == today:
        now = datetime.datetime.now().strftime("%H:%M:%S")
        available_slots = [t for t in TIME_SLOTS if t > now]

    if not available_slots:
        st.warning("⏰ วันนี้ไม่เหลือเวลาว่างแล้ว")
        return

    slot = st.selectbox("เลือกเวลา", available_slots, index=0)

    cols = st.columns(2)
    with cols[0]:
        company = st.text_input("🏢 บริษัท/หน่วยงาน")
        pickup = st.text_input("📍 จุดรับของ")
        phone = st.text_input("📞 เบอร์ติดต่อ")

    with cols[1]:
        dropoff = st.text_input("🎯 จุดส่งของ")
        note = st.text_area("📝 หมายเหตุ", height=80)

    if st.button("✅ ยืนยันการจอง", use_container_width=True):
        try:
            df, ws = read_df()
            if is_conflict(df, date_pick, slot):
                st.error("❌ เวลานี้ถูกจองแล้ว กรุณาเลือกช่วงเวลาอื่น")
                return
            append_booking(ws, date_pick, slot, company, pickup, dropoff, phone, note, username)
            st.success(f"🎉 จองสำเร็จ {date_pick.strftime('%d/%m/%Y')} เวลา {slot[:5]}")
            st.rerun()
        except Exception as e:
            st.error(f"❌ จองไม่สำเร็จ: {e}")

def weekly_table(can_cancel: bool, username: str, is_admin: bool):
    st.subheader("📋 ตารางคิว (สัปดาห์นี้)")
    try:
        df, ws = read_df()
        if df.empty:
            st.info("ยังไม่มีการจองคิว")
            return

        start, end = current_week_bounds()
        week = df[(df["Booking Date"].dt.date >= start) & (df["Booking Date"].dt.date <= end)]
        if week.empty:
            st.info("ℹ️ ไม่มีการจองในสัปดาห์นี้")
            return

        week = week.sort_values(by=["Booking Date","Booking Time"])

        # ==== Header ====
        st.markdown(
            """
            <style>
            .header {background:#4CAF50; color:white; font-weight:bold; padding:8px; text-align:center;}
            .cell {padding:6px; border-bottom:1px solid #ddd;}
            </style>
            """,
            unsafe_allow_html=True
        )

        header_cols = st.columns([1,1,2,2,2,2,3,1,1])
        headers = ["วันที่","เวลา","บริษัท","รับ","ส่ง","โทร","หมายเหตุ","ผู้จอง","ยกเลิก"]
        for col, h in zip(header_cols, headers):
            col.markdown(f"<div class='header'>{h}</div>", unsafe_allow_html=True)

        # ==== Rows ====
        for _, row in week.iterrows():
            cols = st.columns([1,1,2,2,2,2,3,1,1])
            cols[0].markdown(f"<div class='cell'>{row['Booking Date'].date().strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)
            cols[1].markdown(f"<div class='cell'>{row['Booking Time'][:5]}</div>", unsafe_allow_html=True)
            cols[2].markdown(f"<div class='cell'>{row['Company']}</div>", unsafe_allow_html=True)
            cols[3].markdown(f"<div class='cell'>{row['Pickup']}</div>", unsafe_allow_html=True)
            cols[4].markdown(f"<div class='cell'>{row['Dropoff']}</div>", unsafe_allow_html=True)
            cols[5].markdown(f"<div class='cell'>{row['Phone']}</div>", unsafe_allow_html=True)
            cols[6].markdown(f"<div class='cell'>{row['Note']}</div>", unsafe_allow_html=True)
            cols[7].markdown(f"<div class='cell'>{row['User']}</div>", unsafe_allow_html=True)

            # ✅ ปุ่มยกเลิกอยู่ในตารางแถวเดียวกัน
            if can_cancel and (is_admin or row["User"] == username):
                if cols[8].button("❌ ยกเลิก", key=f"cancel_{row['_row']}"):
                    try:
                        delete_booking(ws, int(row["_row"]))
                        st.success("ลบรายการสำเร็จ")
                        st.rerun()
                    except Exception as e:
                        st.error(f"ลบไม่สำเร็จ: {e}")
            else:
                cols[8].markdown("<div class='cell'>-</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ โหลดข้อมูลล้มเหลว: {e}")

def weekly_calendar():
    st.subheader("📆 ปฏิทินรายสัปดาห์ (เวลาว่าง/จองแล้ว)")
    try:
        df, _ = read_df()
        start, end = current_week_bounds()
        days = [(start + datetime.timedelta(days=i)) for i in range(7)]

        grid = []
        for slot in TIME_SLOTS:
            row = {"เวลา": slot[:5]}
            for d in days:
                row[d.strftime("%a %d/%m")] = "✅ ว่าง"
            grid.append(row)
        cal = pd.DataFrame(grid)

        if not df.empty:
            week = df[(df["Booking Date"].dt.date >= start) & (df["Booking Date"].dt.date <= end)]
            for _, r in week.iterrows():
                col = r["Booking Date"].strftime("%a %d/%m")
                if col in cal.columns:
                    idx = cal.index[cal["เวลา"] == r["Booking Time"][:5]]
                    if len(idx) > 0:
                        cal.loc[idx[0], col] = f"❌ จองโดย {r['User']}"

        st.dataframe(cal, use_container_width=True)

    except Exception as e:
        st.error(f"❌ โหลดปฏิทินล้มเหลว: {e}")

# ------------- Main entry -------------
def program_messenger_booking():
    st.header("🚚 ระบบจองคิวแมสเซ็นเจอร์")

    role = st.session_state.get("role", "User")
    username = st.session_state.get("username", "Guest")
    is_admin = (role == "Admin")

    weekly_calendar()
    st.markdown("---")
    weekly_table(can_cancel=True, username=username, is_admin=is_admin)
    st.markdown("---")

    st.subheader("🧾 จองคิวใหม่")
    booking_form(username if not is_admin else "Admin")
