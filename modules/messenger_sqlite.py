# modules/messenger_sqlite.py
import sqlite3
import pandas as pd
import streamlit as st
import datetime
from typing import Optional

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
def add_booking(username: str, company: str, document_type: str,
                pickup: str, dropoff: str, contact: str,
                booking_date: str, booking_time: str) -> int:
    """Insert booking and return inserted id."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO messenger_booking
        (username, company, document_type, pickup_location, dropoff_location, contact_number, booking_date, booking_time, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (username, company, document_type, pickup, dropoff, contact, booking_date, booking_time, "รอจัดการ"))
    conn.commit()
    inserted_id = c.lastrowid
    conn.close()
    return inserted_id

def get_all_bookings() -> pd.DataFrame:
    conn = sqlite3.connect(DB_FILE)
    try:
        df = pd.read_sql("SELECT * FROM messenger_booking ORDER BY booking_date, booking_time, id", conn)
    except Exception:
        df = pd.DataFrame(columns=["id","username","company","document_type","pickup_location","dropoff_location","contact_number","booking_date","booking_time","status"])
    conn.close()
    return df

def get_booking_owner(booking_id: int) -> Optional[str]:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username FROM messenger_booking WHERE id=?", (booking_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def cancel_booking(booking_id: int, username: str, is_admin: bool = False) -> bool:
    """
    Try to cancel booking.
    Return True if deleted, False otherwise.
    Strong server-side check: if not admin, owner must match.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        # If not admin, ensure owner matches current username
        if not is_admin:
            c.execute("SELECT username FROM messenger_booking WHERE id=?", (booking_id,))
            row = c.fetchone()
            if not row:
                conn.close()
                return False  # not exists
            owner = row[0]
            if owner != username:
                conn.close()
                return False  # not allowed

            # proceed to delete only if owner matches
            c.execute("DELETE FROM messenger_booking WHERE id=? AND username=?", (booking_id, username))
        else:
            # admin can delete any id
            c.execute("DELETE FROM messenger_booking WHERE id=?", (booking_id,))

        affected = c.rowcount
        conn.commit()
        conn.close()
        return affected > 0
    except Exception:
        conn.rollback()
        conn.close()
        return False

# ================= Booking Form (UI) =================
def booking_form(username: str = "ไม่ระบุ"):
    st.subheader("📋 แบบฟอร์มจอง Messenger")

    company = st.text_input("ชื่อบริษัท")
    document_type = st.text_input("ประเภทเอกสาร")
    pickup = st.text_input("📍 สถานที่รับเอกสาร")
    dropoff = st.text_input("🏢 สถานที่ส่งเอกสาร")
    contact = st.text_input("📞 เบอร์ติดต่อ")

    booking_date = st.date_input("วันที่ต้องการใช้ Messenger", min_value=datetime.date.today())
    booking_time = st.selectbox("เวลาที่ต้องการใช้ Messenger", [f"{h:02d}:00" for h in range(7, 19)])

    if st.button("✅ ยืนยันการจอง"):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM messenger_booking WHERE booking_date=? AND booking_time=?", (str(booking_date), booking_time))
        exists = c.fetchone()[0]
        conn.close()

        if exists > 0:
            st.error(f"❌ มีการจองแล้วในช่วง {booking_date} {booking_time}")
        else:
            new_id = add_booking(username, company, document_type, pickup, dropoff, contact, str(booking_date), booking_time)
            st.success(f"🎉 จองสำเร็จ (ID: {new_id}) — {booking_date} {booking_time}")

# ================= Calendar View (UI) =================
def calendar_view():
    st.subheader("📅 ปฏิทินการจอง Messenger (จันทร์ - อาทิตย์)")

    today = datetime.date.today()
    week_days = [today + datetime.timedelta(days=i) for i in range(7)]
    times = [f"{h:02d}:00" for h in range(7, 19)]

    df = get_all_bookings()
    bookings = {}
    for _, row in df.iterrows():
        key = (row["booking_date"], row["booking_time"])
        # show company (or username) in calendar
        bookings[key] = f"{row.get('company') or row.get('username')}"

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

# ================= Cancel Booking (UI) =================
def cancel_booking_ui(username: str, role: str = "User"):
    st.subheader("🗑 ยกเลิกการจอง Messenger")

    df = get_all_bookings()
    if df.empty:
        st.info("ยังไม่มีการจอง")
        return

    # UI filter: normal users see only their own bookings
    if role != "Admin":
        df = df[df["username"] == username]

    if df.empty:
        st.info("คุณยังไม่มีการจองที่จะยกเลิก")
        return

    today = datetime.date.today()

    # Show each booking with clear owner and id; only allow cancel button when allowed
    for _, row in df.iterrows():
        try:
            booking_day = datetime.datetime.strptime(str(row["booking_date"]), "%Y-%m-%d").date()
        except Exception:
            # If date stored in different format, skip parse error
            booking_day = today

        is_past = booking_day < today
        is_self = (row["username"] == username)

        # background color
        if is_past:
            bg = "#f0f0f0"  # gray = past
        elif is_self:
            bg = "#e6ffec"  # light green = own
        else:
            bg = "#ffe6e6"  # light red = others (only admin can see)

        # render
        st.markdown(
            f"""
            <div style="background:{bg}; padding:10px; border-radius:8px; margin-bottom:6px;">
                <strong>🆔 {int(row['id'])}</strong> |
                👤 <strong>{row['username']}</strong> |
                🏢 {row.get('company','-')} |
                📄 {row.get('document_type','-')} |
                📅 {row.get('booking_date','-')} {row.get('booking_time','-')} |
                📞 {row.get('contact_number','-')}
            </div>
            """,
            unsafe_allow_html=True
        )

        # Only allow cancellation for not-past bookings.
        # For normal user, since df was filtered above, we only render user's bookings.
        if not is_past:
            key = f"cancel_{int(row['id'])}"
            if st.button("🗑 ยกเลิก", key=key):
                # SERVER-SIDE CHECK: cancel_booking will verify owner or admin
                success = cancel_booking(int(row["id"]), username, is_admin=(role == "Admin"))
                if success:
                    st.success(f"ลบการจอง ID {int(row['id'])} เรียบร้อยแล้ว")
                    # rerun to refresh UI
                    st.experimental_rerun()
                else:
                    st.error("⚠️ ไม่สามารถยกเลิกได้ — คุณไม่มีสิทธิ์ หรือการจองหายไปแล้ว")

# ================= Main Program =================
def program_messenger_booking(username: str = "ไม่ระบุ", role: str = "User"):
    init_db()
    st.title("🚚 ระบบจอง Messenger")

    menu = st.radio("เมนู", ["✍ จอง Messenger", "📅 ปฏิทินการจอง", "🗑 ยกเลิกการจอง"], horizontal=True)

    if menu == "✍ จอง Messenger":
        booking_form(username=username)
    elif menu == "📅 ปฏิทินการจอง":
        calendar_view()
    else:
        cancel_booking_ui(username, role)
