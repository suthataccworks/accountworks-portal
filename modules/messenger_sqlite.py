import streamlit as st
import sqlite3
import pandas as pd
import datetime

DB_FILE = "messenger_booking.db"

# ================== Database ==================
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
            status TEXT DEFAULT 'รอจัดการ'
        )
    """)
    conn.commit()
    conn.close()


def add_booking(username, company, document_type, booking_date, booking_time):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # ✅ เช็คว่ามีการจองเวลาซ้ำหรือยัง
    c.execute("""
        SELECT COUNT(*) FROM messenger_booking
        WHERE booking_date=? AND booking_time=?
    """, (booking_date, booking_time))
    exists = c.fetchone()[0]

    if exists > 0:
        conn.close()
        return False  # จองซ้ำ

    c.execute("""
        INSERT INTO messenger_booking (username, company, document_type, booking_date, booking_time, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, company, document_type, booking_date, booking_time, "รอจัดการ"))
    conn.commit()
    conn.close()
    return True


def get_all_bookings():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM messenger_booking ORDER BY booking_date DESC, booking_time DESC", conn)
    conn.close()
    return df


# ================== UI Functions ==================
def booking_form(username="ไม่ระบุ"):
    st.subheader("🚚 แบบฟอร์มจอง Messenger")

    company = st.text_input("ชื่อบริษัท")
    document_type = st.text_input("ประเภทเอกสาร")
    booking_date = st.date_input("วันที่ต้องการใช้ Messenger", min_value=datetime.date.today())
    booking_time = st.selectbox("เวลาที่ต้องการใช้ Messenger", [f"{h:02d}:00" for h in range(7, 19)])

    if st.button("📌 ยืนยันการจอง"):
        success = add_booking(username, company, document_type, str(booking_date), str(booking_time))
        if success:
            st.success("✅ จองสำเร็จแล้ว")
        else:
            st.error("❌ มีการจองเวลานี้แล้ว กรุณาเลือกเวลาอื่น")


def manage_bookings():
    st.subheader("📋 รายการจองทั้งหมด")
    df = get_all_bookings()
    st.dataframe(df, use_container_width=True)


def calendar_view():
    st.subheader("📅 ปฏิทินการจอง Messenger (จันทร์ - อาทิตย์)")

    df = get_all_bookings()

    # รายชั่วโมง 07:00 - 18:00
    time_slots = [f"{h:02d}:00" for h in range(7, 19)]

    today = datetime.date.today()
    monday = today - datetime.timedelta(days=today.weekday())  # หา "วันจันทร์" ของสัปดาห์นี้
    week_days = [monday + datetime.timedelta(days=i) for i in range(7)]  # จันทร์-อาทิตย์

    # สร้างตารางว่าง
    calendar = pd.DataFrame(index=time_slots, columns=[d.strftime("%a %d/%m") for d in week_days])
    calendar[:] = "ว่าง ✅"

    # เติมข้อมูลจาก DB
    for _, row in df.iterrows():
        date_str = row["booking_date"]
        time_str = row["booking_time"][:5]
        username = row["username"]
        company = row["company"]

        try:
            booking_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            continue

        if booking_date in week_days and time_str in time_slots:
            col_name = booking_date.strftime("%a %d/%m")
            calendar.at[time_str, col_name] = f"{username} ({company})"

    # ✅ ทำให้วัน/เวลาที่ผ่านมาแล้วเป็นสีเทา + เปลี่ยนข้อความ
    def highlight_past(val, row_time, col_date):
        booking_date = datetime.datetime.strptime(col_date, "%a %d/%m").date()
        booking_datetime = datetime.datetime.combine(booking_date, datetime.time(int(row_time.split(":")[0]), 0))

        if booking_datetime < datetime.datetime.now():
            return "background-color: lightgray; color: black;"
        return ""

    def replace_past(val, row_time, col_date):
        booking_date = datetime.datetime.strptime(col_date, "%a %d/%m").date()
        booking_datetime = datetime.datetime.combine(booking_date, datetime.time(int(row_time.split(":")[0]), 0))
        if booking_datetime < datetime.datetime.now():
            return "⏳ หมดเวลา"
        return val

    # แทนค่าช่องที่หมดเวลา
    for col in calendar.columns:
        for row_time in calendar.index:
            calendar.at[row_time, col] = replace_past(calendar.at[row_time, col], row_time, col)

    styled_calendar = calendar.style.apply(
        lambda col: [
            highlight_past(val, row_time, col.name)
            for row_time, val in zip(calendar.index, col)
        ],
        axis=0
    )

    st.dataframe(styled_calendar, use_container_width=True)


# ================== Main ==================
def program_messenger_booking(username="ไม่ระบุ"):
    init_db()

    menu = st.radio("เมนู", ["✍ จอง Messenger", "📋 รายการทั้งหมด", "📅 ปฏิทินรายสัปดาห์"])

    if menu == "✍ จอง Messenger":
        booking_form(username=username)
    elif menu == "📋 รายการทั้งหมด":
        manage_bookings()
    elif menu == "📅 ปฏิทินรายสัปดาห์":
        calendar_view()
