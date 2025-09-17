import streamlit as st
import sqlite3
import pandas as pd
import datetime

DB_FILE = "messenger_booking.db"

# ============ Database Init ============
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # ✅ สร้างตารางพร้อมฟิลด์ใหม่ (pickup_location, dropoff_location, contact_phone)
    c.execute("""
        CREATE TABLE IF NOT EXISTS messenger_booking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            company TEXT NOT NULL,
            document_type TEXT NOT NULL,
            pickup_location TEXT NOT NULL,
            dropoff_location TEXT NOT NULL,
            contact_phone TEXT NOT NULL,
            booking_date TEXT NOT NULL,
            booking_time TEXT NOT NULL DEFAULT '09:00',
            status TEXT NOT NULL DEFAULT 'รอจัดการ'
        )
    """)

    # ✅ migrate column ถ้า schema เก่า
    c.execute("PRAGMA table_info(messenger_booking)")
    cols = [col[1] for col in c.fetchall()]
    if "pickup_location" not in cols:
        c.execute("ALTER TABLE messenger_booking ADD COLUMN pickup_location TEXT DEFAULT ''")
    if "dropoff_location" not in cols:
        c.execute("ALTER TABLE messenger_booking ADD COLUMN dropoff_location TEXT DEFAULT ''")
    if "contact_phone" not in cols:
        c.execute("ALTER TABLE messenger_booking ADD COLUMN contact_phone TEXT DEFAULT ''")

    conn.commit()
    conn.close()

# ============ DB Utils ============
def add_booking(username, company, document_type, pickup_location, dropoff_location, contact_phone, booking_date, booking_time):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO messenger_booking 
        (username, company, document_type, pickup_location, dropoff_location, contact_phone, booking_date, booking_time, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (username, company, document_type, pickup_location, dropoff_location, contact_phone, booking_date, booking_time, "รอจัดการ"))
    conn.commit()
    conn.close()

def get_all_bookings():
    conn = sqlite3.connect(DB_FILE)
    try:
        df = pd.read_sql("SELECT * FROM messenger_booking ORDER BY booking_date DESC, booking_time DESC", conn)
    except Exception:
        df = pd.read_sql("SELECT * FROM messenger_booking ORDER BY booking_date DESC", conn)
    conn.close()
    return df

def update_status(booking_id, new_status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE messenger_booking SET status=? WHERE id=?", (new_status, booking_id))
    conn.commit()
    conn.close()

def delete_booking(booking_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM messenger_booking WHERE id=?", (booking_id,))
    conn.commit()
    conn.close()

# ============ Booking Form ============
def booking_form(username=""):
    st.subheader("🚚 แบบฟอร์มจอง Messenger")

    # ฟอร์ม
    company = st.text_input("ชื่อบริษัท")
    document_type = st.text_input("ประเภทเอกสาร")
    pickup_location = st.text_input("📍 ตำแหน่งรับเอกสาร")
    dropoff_location = st.text_input("📍 ตำแหน่งส่งเอกสาร")
    contact_phone = st.text_input("📞 เบอร์ผู้ติดต่อ")

    booking_date = st.date_input("วันที่ต้องการใช้ Messenger", value=datetime.date.today())
    booking_time = st.time_input("เวลาที่ต้องการใช้ Messenger", value=datetime.time(9, 0))

    if st.button("📌 ยืนยันการจอง"):
        if company and document_type and pickup_location and dropoff_location and contact_phone:
            add_booking(username, company, document_type, pickup_location, dropoff_location, contact_phone, str(booking_date), str(booking_time))
            st.success("✅ บันทึกการจองสำเร็จ")
        else:
            st.warning("⚠️ กรุณากรอกข้อมูลให้ครบ")

# ============ Manage Bookings (Admin/Staff) ============
def manage_bookings():
    st.subheader("📋 จัดการรายการจอง Messenger")
    df = get_all_bookings()

    if df.empty:
        st.info("ยังไม่มีการจอง Messenger")
        return

    st.dataframe(df, use_container_width=True)

    booking_ids = df["id"].tolist()
    booking_id = st.selectbox("เลือกรายการที่ต้องการแก้ไข", [""] + [str(i) for i in booking_ids])

    if booking_id:
        new_status = st.selectbox("สถานะใหม่", ["รอจัดการ", "กำลังดำเนินการ", "สำเร็จ", "ยกเลิก"])
        if st.button("อัปเดตสถานะ"):
            update_status(int(booking_id), new_status)
            st.success("✅ อัปเดตสถานะเรียบร้อยแล้ว")
            st.rerun()

        if st.button("❌ ลบรายการ"):
            delete_booking(int(booking_id))
            st.warning("🗑️ ลบรายการเรียบร้อยแล้ว")
            st.rerun()

# ============ Entry Point ============
def program_messenger_booking(username=""):
    init_db()

    st.title("📦 ระบบจอง Messenger")
    menu = ["📌 จอง Messenger", "📋 รายการทั้งหมด"]
    choice = st.radio("เมนู", menu)

    if choice == "📌 จอง Messenger":
        booking_form(username=username)
    elif choice == "📋 รายการทั้งหมด":
        manage_bookings()
