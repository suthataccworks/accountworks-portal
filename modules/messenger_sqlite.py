import streamlit as st
import sqlite3
import pandas as pd
import datetime

DB_FILE = "messenger_booking.db"

# ============ Database Init ============
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # ✅ สร้างตารางเบื้องต้น (ไม่รวม booking_time)
    c.execute("""
        CREATE TABLE IF NOT EXISTS messenger_booking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            company TEXT NOT NULL,
            document_type TEXT NOT NULL,
            booking_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'รอจัดการ'
        )
    """)

    # ✅ ตรวจสอบ schema ถ้าไม่มี booking_time → เพิ่ม column อัตโนมัติ
    c.execute("PRAGMA table_info(messenger_booking)")
    cols = [col[1] for col in c.fetchall()]
    if "booking_time" not in cols:
        c.execute("ALTER TABLE messenger_booking ADD COLUMN booking_time TEXT NOT NULL DEFAULT '09:00'")

    conn.commit()
    conn.close()

# ============ DB Utils ============
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

    # ✅ ป้องกัน error ด้วย setdefault
    st.session_state.setdefault("company", "")
    st.session_state.setdefault("document_type", "")
    st.session_state.setdefault("booking_date", datetime.date.today())
    st.session_state.setdefault("booking_time", datetime.time(9, 0))

    company = st.text_input("ชื่อบริษัท", value=st.session_state["company"])
    document_type = st.text_input("ประเภทเอกสาร", value=st.session_state["document_type"])
    booking_date = st.date_input("วันที่ต้องการใช้ Messenger", value=st.session_state["booking_date"])
    booking_time = st.time_input("เวลาที่ต้องการใช้ Messenger", value=st.session_state["booking_time"])

    if st.button("📌 ยืนยันการจอง"):
        if company and document_type:
            add_booking(username, company, document_type, str(booking_date), str(booking_time))
            st.success("✅ บันทึกการจองสำเร็จ")

            # reset ค่าในฟอร์ม
            st.session_state["company"] = ""
            st.session_state["document_type"] = ""
            st.session_state["booking_date"] = datetime.date.today()
            st.session_state["booking_time"] = datetime.time(9, 0)
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
