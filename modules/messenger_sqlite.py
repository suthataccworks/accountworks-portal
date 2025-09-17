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

def delete_booking(booking_id, username, role):
    """ลบได้เฉพาะ Admin หรือเจ้าของ booking"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    if role == "Admin":
        # ✅ Admin ลบได้ทุก booking
        c.execute("DELETE FROM messenger_booking WHERE id=?", (booking_id,))
    else:
        # ✅ ตรวจสอบก่อนว่าการจองนี้เป็นของ user จริงหรือไม่
        c.execute("SELECT username FROM messenger_booking WHERE id=?", (booking_id,))
        row = c.fetchone()
        if not row or row[0] != username:
            conn.close()
            return False  # ❌ ไม่ใช่เจ้าของ → ห้ามลบ

        # ✅ ถ้าเป็นของ user เอง → ลบได้
        c.execute("DELETE FROM messenger_booking WHERE id=? AND username=?", (booking_id, username))

    conn.commit()
    affected = c.rowcount
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
        # ตรวจสอบว่ามีการจองซ้ำหรือยัง
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

    # สร้างตารางปฏิทิน
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
def cancel_booking_ui(username="ไม่ระบุ", role="User"):
    st.subheader("🗑️ ยกเลิกการจอง Messenger")

    df = get_all_bookings()

    # ถ้าเป็น User ให้เห็นเฉพาะของตัวเอง
    if role != "Admin":
        df = df[df["username"] == username]

    if df.empty:
        st.info("ไม่มีการจองที่สามารถยกเลิกได้")
        return

    for _, row in df.iterrows():
        with st.container():
            st.markdown(
                f"**🆔 {row['id']} | 👤 {row['username']} | 🏢 {row['company']} | 📄 {row['document_type']} "
                f"| 📍 {row['pickup_location']} → {row['dropoff_location']} | 📅 {row['booking_date']} {row['booking_time']} "
                f"| 📞 {row['contact_number']}**"
            )
            if st.button(f"❌ ยกเลิก (ID {row['id']})", key=f"cancel_{row['id']}"):
                success = delete_booking(row["id"], username, role)
                if success:
                    st.success(f"✅ ยกเลิกการจอง ID {row['id']} เรียบร้อยแล้ว")
                    st.rerun()
                else:
                    st.error("⚠️ ไม่มีสิทธิ์ลบการจองนี้")

# ================= Main Program =================
def program_messenger_booking(username="ไม่ระบุ", role="User"):
    init_db()
    st.title("🚚 ระบบจอง Messenger")

    menu = st.radio("เมนู", ["✍ จอง Messenger", "📅 ปฏิทินการจอง", "🗑️ ยกเลิกการจอง"], horizontal=True)

    if menu == "✍ จอง Messenger":
        booking_form(username=username)
    elif menu == "📅 ปฏิทินการจอง":
        calendar_view()
    else:
        cancel_booking_ui(username=username, role=role)
