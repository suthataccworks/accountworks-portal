import sqlite3
import pandas as pd
import streamlit as st
import datetime

DB_FILE = "messenger_booking.db"

# ================= Database Init =================
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

# ================= CRUD =================
def add_booking(username, company, document_type, booking_date, booking_time):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO messenger_booking (username, company, document_type, booking_date, booking_time, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, company, document_type, booking_date, booking_time, "รอจัดการ"))
    conn.commit()
    conn.close()

def get_all_bookings():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM messenger_booking ORDER BY booking_date DESC, booking_time DESC", conn)
    conn.close()
    return df

def delete_booking(booking_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM messenger_booking WHERE id=?", (booking_id,))
    conn.commit()
    conn.close()

# ================= UI Forms =================
def booking_form(username="ไม่ระบุ"):
    st.subheader("🚚 แบบฟอร์มจอง Messenger")

    company = st.text_input("ชื่อบริษัท")
    document_type = st.text_input("ประเภทเอกสาร")
    booking_date = st.date_input("วันที่ต้องการใช้ Messenger", datetime.date.today())
    booking_time = st.selectbox("เวลาที่ต้องการใช้ Messenger", [f"{h:02d}:00" for h in range(7, 19)])

    if st.button("✨ ยืนยันการจอง"):
        if company and document_type:
            add_booking(username, company, document_type, str(booking_date), booking_time)
            st.success("✅ บันทึกการจองเรียบร้อยแล้ว")
        else:
            st.error("⚠️ กรุณากรอกข้อมูลให้ครบ")

def manage_bookings():
    st.subheader("📋 รายการจอง Messenger ทั้งหมด")

    df = get_all_bookings()
    if df.empty:
        st.info("ยังไม่มีข้อมูลการจอง")
        return

    st.dataframe(df, use_container_width=True)

    delete_id = st.number_input("กรอก ID ที่ต้องการลบ", min_value=0, step=1)
    if st.button("🗑️ ลบการจอง"):
        delete_booking(delete_id)
        st.warning(f"ลบรายการที่ ID {delete_id} เรียบร้อยแล้ว")
        st.experimental_rerun()

# ================= Calendar View =================
def calendar_view():
    st.subheader("📅 ปฏิทินการจอง Messenger (1 สัปดาห์)")

    df = get_all_bookings()

    if df.empty:
        st.info("ยังไม่มีการจอง Messenger")
        return

    # รายชั่วโมง 07:00 - 18:00
    time_slots = [f"{h:02d}:00" for h in range(7, 19)]

    today = datetime.date.today()
    week_days = [today + datetime.timedelta(days=i) for i in range(7)]

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

    st.dataframe(calendar, use_container_width=True)

# ================= Main Program =================
def program_messenger_booking(username="ไม่ระบุ"):
    init_db()

    st.title("📦 ระบบจอง Messenger")
    menu = ["📌 จอง Messenger", "📋 รายการทั้งหมด", "📅 ปฏิทินสัปดาห์"]
    choice = st.radio("เมนู", menu)

    if choice == "📌 จอง Messenger":
        booking_form(username=username)
    elif choice == "📋 รายการทั้งหมด":
        manage_bookings()
    elif choice == "📅 ปฏิทินสัปดาห์":
        calendar_view()
