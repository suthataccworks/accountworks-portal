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
            username TEXT NOT NULL,
            company TEXT NOT NULL,
            document_type TEXT NOT NULL,
            pickup_location TEXT,
            dropoff_location TEXT,
            contact_number TEXT,
            booking_date TEXT NOT NULL,
            booking_time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'รอจัดการ'
        )
    """)
    conn.commit()
    conn.close()

# ================= CRUD =================
def add_booking(username, company, document_type, pickup, dropoff, contact, booking_date, booking_time):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO messenger_booking 
        (username, company, document_type, pickup_location, dropoff_location, contact_number, booking_date, booking_time, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (username, company, document_type, pickup, dropoff, contact, booking_date, booking_time, "รอจัดการ"))
    conn.commit()
    conn.close()

def get_all_bookings():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM messenger_booking ORDER BY booking_date, booking_time", conn)
    conn.close()
    return df

def cancel_booking(booking_id, username, is_admin=False):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    if is_admin:
        # Admin ลบได้ทุกการจอง
        c.execute("DELETE FROM messenger_booking WHERE id=?", (booking_id,))
    else:
        # User ธรรมดาลบได้เฉพาะของตัวเอง
        c.execute("DELETE FROM messenger_booking WHERE id=? AND username=?", (booking_id, username))

    conn.commit()
    affected = conn.total_changes  # เช็คว่ามี row ถูกลบจริงหรือไม่
    conn.close()
    return affected > 0

# ================= Booking Form =================
def booking_form(username="ไม่ระบุ"):
    st.subheader("📋 แบบฟอร์มจอง Messenger")

    company = st.text_input("ชื่อบริษัท")
    document_type = st.text_input("ประเภทเอกสาร")
    pickup = st.text_input("📍 สถานที่รับเอกสาร")
    dropoff = st.text_input("🏢 สถานที่ส่งเอกสาร")
    contact = st.text_input("📞 เบอร์ติดต่อ")

    booking_date = st.date_input("วันที่ต้องการใช้ Messenger", min_value=datetime.date.today())
    booking_time = st.selectbox("เวลาที่ต้องการใช้ Messenger", 
                                [f"{h:02d}:00" for h in range(7, 19)])

    if st.button("✅ ยืนยันการจอง"):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            SELECT COUNT(*) FROM messenger_booking 
            WHERE booking_date=? AND booking_time=?
        """, (str(booking_date), booking_time))
        exists = c.fetchone()[0]
        conn.close()

        if exists > 0:
            st.error(f"❌ มีการจองแล้วในช่วง {booking_date} {booking_time}")
        else:
            add_booking(username, company, document_type, pickup, dropoff, contact, str(booking_date), booking_time)
            st.success(f"🎉 จอง Messenger สำเร็จสำหรับ {booking_date} {booking_time}")

# ================= Calendar View =================
def calendar_view():
    st.subheader("📅 ปฏิทินการจอง Messenger (จันทร์ - อาทิตย์)")

    today = datetime.date.today()
    week_days = [today + datetime.timedelta(days=i) for i in range(7)]
    times = [f"{h:02d}:00" for h in range(7, 19)]

    df = get_all_bookings()
    bookings = {(row["booking_date"], row["booking_time"]): row["company"] for _, row in df.iterrows()}

    table = []
    for t in times:
        row = []
        for d in week_days:
            key = (str(d), t)
            if d < today:
                row.append("⏳ หมดเวลา")
            elif key in bookings:
                row.append(f"📌 {bookings[key]}")
            else:
                row.append("ว่าง ✅")
        table.append(row)

    df_calendar = pd.DataFrame(table, index=times, columns=[d.strftime("%a %d/%m") for d in week_days])
    st.dataframe(df_calendar, use_container_width=True)

# ================= Cancel Booking =================
def cancel_booking_ui(username, role="User"):
    st.subheader("🗑 ยกเลิกการจอง Messenger")

    df = get_all_bookings()
    if df.empty:
        st.info("ยังไม่มีการจอง")
        return

    if role != "Admin":
        df = df[df["username"] == username]

    st.dataframe(df, use_container_width=True)

    booking_id = st.number_input("กรอก ID ของการจองที่ต้องการยกเลิก", min_value=1, step=1)
    if st.button("❌ ยกเลิกการจอง"):
        success = cancel_booking(booking_id, username, is_admin=(role == "Admin"))
        if success:
            st.success(f"ลบการจอง ID {booking_id} เรียบร้อยแล้ว")
        else:
            st.error("⚠️ คุณไม่มีสิทธิ์ยกเลิกการจองนี้ หรือ ID ไม่ถูกต้อง")

# ================= Main Program =================
def program_messenger_booking(username="ไม่ระบุ", role="User"):
    init_db()
    st.title("🚚 ระบบจอง Messenger")

    menu = st.radio("เมนู", ["✍ จอง Messenger", "📅 ปฏิทินการจอง", "🗑 ยกเลิกการจอง"], horizontal=True)

    if menu == "✍ จอง Messenger":
        booking_form(username=username)
    elif menu == "📅 ปฏิทินการจอง":
        calendar_view()
    else:
        cancel_booking_ui(username, role)
