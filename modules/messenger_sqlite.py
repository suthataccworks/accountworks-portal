import streamlit as st
import pandas as pd
import datetime
import sqlite3

DB_FILE = "messenger_booking.db"

# ============ Database ==============
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS messenger_booking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        company TEXT,
        document_type TEXT,
        booking_date TEXT,
        booking_time TEXT,
        status TEXT
    )
    """)
    conn.commit()
    conn.close()

def add_booking(username, company, document_type, booking_date, booking_time):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # ตรวจสอบว่าซ้ำหรือยัง
    c.execute("""
        SELECT COUNT(*) FROM messenger_booking
        WHERE booking_date=? AND booking_time=?
    """, (booking_date, booking_time))
    exists = c.fetchone()[0]

    if exists > 0:
        conn.close()
        return False  # มีการจองแล้ว

    c.execute("""
        INSERT INTO messenger_booking (username, company, document_type, booking_date, booking_time, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, company, document_type, booking_date, booking_time, "รอจัดการ"))
    conn.commit()
    conn.close()
    return True

def get_all_bookings():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM messenger_booking", conn)
    conn.close()
    return df


# ============ Calendar View ==============
def calendar_view():
    st.subheader("📅 ปฏิทินการจอง Messenger (จันทร์ - อาทิตย์)")

    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())  # วันจันทร์
    week_days = [monday + datetime.timedelta(days=i) for i in range(7)]

    # ช่วงเวลา 07:00 - 18:00
    time_slots = [f"{h:02d}:00" for h in range(7, 19)]

    # สร้าง DataFrame เปล่า
    calendar = pd.DataFrame(index=time_slots, columns=[d.strftime("%a %d/%m/%Y") for d in week_days])

    # ดึงข้อมูลจาก DB
    bookings = get_all_bookings()

    for d in week_days:
        day_str = d.strftime("%Y-%m-%d")
        col_name = d.strftime("%a %d/%m/%Y")
        for t in time_slots:
            booking = bookings[(bookings["booking_date"] == day_str) & (bookings["booking_time"] == t)]
            if not booking.empty:
                if len(booking) > 1:
                    calendar.loc[t, col_name] = "❌ ถูกจองแล้ว"
                else:
                    calendar.loc[t, col_name] = booking.iloc[0]["company"]
            else:
                calendar.loc[t, col_name] = "ว่าง ✅"

    # ฟังก์ชันเปลี่ยนข้อความ
    def replace_past(val, row_time, col_date):
        booking_date = datetime.datetime.strptime(col_date, "%a %d/%m/%Y").date()
        booking_datetime = datetime.datetime.combine(booking_date, datetime.time(int(row_time.split(":")[0]), 0))
        if booking_datetime < datetime.datetime.now():
            return "⏳ หมดเวลา"
        return val

    # ฟังก์ชันเปลี่ยนสี
    def highlight_past(val, row_time, col_date):
        booking_date = datetime.datetime.strptime(col_date, "%a %d/%m/%Y").date()
        booking_datetime = datetime.datetime.combine(booking_date, datetime.time(int(row_time.split(":")[0]), 0))
        if booking_datetime < datetime.datetime.now():
            return "background-color: lightgray; color: black;"
        return ""

    # Apply ทั้ง DataFrame
    styled_calendar = calendar.copy()
    for col in styled_calendar.columns:
        for row in styled_calendar.index:
            styled_calendar.loc[row, col] = replace_past(calendar.loc[row, col], row, col)

    styled_calendar = styled_calendar.style.applymap(
        lambda v, row_time, col_date: highlight_past(v, row_time, col_date),
        row_time=styled_calendar.index, col_date=styled_calendar.columns
    )

    st.dataframe(styled_calendar, use_container_width=True, height=600)


# ============ Run ==============
if __name__ == "__main__":
    init_db()
    calendar_view()
