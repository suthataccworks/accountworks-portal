import streamlit as st
import sqlite3
import pandas as pd
import datetime
from contextlib import contextmanager

# ================= CONFIG =================
DB_FILE = "messenger_booking.db"
TIME_SLOTS = ["09:00:00","10:00:00","11:00:00","13:00:00","14:00:00","15:00:00","16:00:00"]

# ================= DB Helpers =================
@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        yield conn
    finally:
        conn.close()

def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_date TEXT NOT NULL,
                booking_time TEXT NOT NULL,
                company TEXT,
                pickup TEXT,
                dropoff TEXT,
                phone TEXT,
                note TEXT,
                user TEXT NOT NULL
            );
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_bookings_date_time ON bookings(booking_date, booking_time);")
        c.execute("CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings(user);")
        conn.commit()

def add_booking(date, time, company, pickup, dropoff, phone, note, user):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            """INSERT INTO bookings
               (booking_date, booking_time, company, pickup, dropoff, phone, note, user)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?);""",
            (date, time, company.strip(), pickup.strip(), dropoff.strip(), phone.strip(), (note or "").strip(), user)
        )
        conn.commit()

def delete_booking(booking_id: int):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM bookings WHERE id = ?;", (booking_id,))
        conn.commit()

def fetch_week(start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
    with get_conn() as conn:
        query = """
            SELECT id, booking_date, booking_time, company, pickup, dropoff, phone, note, user
            FROM bookings
            WHERE booking_date BETWEEN ? AND ?
            ORDER BY booking_date, booking_time;
        """
        df = pd.read_sql_query(query, conn, params=(start_date.isoformat(), end_date.isoformat()))
    if not df.empty:
        df["booking_date"] = pd.to_datetime(df["booking_date"]).dt.date
    return df

def is_conflict(date_obj: datetime.date, time_str: str) -> bool:
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT 1 FROM bookings WHERE booking_date = ? AND booking_time = ? LIMIT 1;",
            (date_obj.isoformat(), time_str)
        )
        return c.fetchone() is not None

# ================= Utils =================
def current_week_bounds(today: datetime.date | None = None):
    if today is None:
        today = datetime.date.today()
    start = today - datetime.timedelta(days=today.weekday())  # Monday
    end = start + datetime.timedelta(days=6)                   # Sunday
    return start, end

def hhmm(time_str: str) -> str:
    return time_str[:5] if time_str else ""

# ================= Views =================
def booking_form(username: str):
    st.subheader("📝 จองคิวแมสเซ็นเจอร์")

    today = datetime.date.today()
    date_pick = st.date_input("เลือกวันที่", min_value=today, value=today, format="YYYY-MM-DD", key="date_pick")

    # สร้างรายการเวลาที่เลือกได้
    now = datetime.datetime.now()
    available = []
    for t in TIME_SLOTS:
        if date_pick == today:
            t_obj = datetime.datetime.strptime(t, "%H:%M:%S").time()
            if t_obj <= now.time():
                continue
        if not is_conflict(date_pick, t):
            available.append(t)

    if not available:
        st.warning("⏰ ไม่มีเวลาว่างให้จองในวันที่เลือก")
        return

    slot = st.selectbox("เลือกเวลา", [f"{hhmm(t)}" for t in available], index=0, key="slot_select")
    slot_full = [t for t in available if hhmm(t) == slot][0]

    c1, c2 = st.columns(2)
    with c1:
        company = st.text_input("🏢 บริษัท/หน่วยงาน", key="company")
        pickup  = st.text_input("📍 จุดรับของ", key="pickup")
        phone   = st.text_input("📞 เบอร์ติดต่อ", key="phone")
    with c2:
        dropoff = st.text_input("🎯 จุดส่งของ", key="dropoff")
        note    = st.text_area("📝 หมายเหตุ", key="note", height=80)

    if st.button("✅ ยืนยันการจอง", use_container_width=True):
        if not company.strip():
            st.error("กรุณากรอกชื่อบริษัท/หน่วยงาน")
            return
        if is_conflict(date_pick, slot_full):
            st.error("❌ เวลานี้มีคนจองแล้ว กรุณาเลือกเวลาอื่น")
            st.session_state["_force_refresh"] = True
            st.rerun()

        add_booking(date_pick.isoformat(), slot_full, company, pickup, dropoff, phone, note, username)
        st.success(f"🎉 จองสำเร็จ {date_pick.strftime('%d/%m/%Y')} เวลา {slot}")

        # ✅ รีเซ็ตค่า form หลังบันทึก
        for key, default in {
            "company": "",
            "pickup": "",
            "dropoff": "",
            "phone": "",
            "note": "",
            "slot_select": 0
        }.items():
            st.session_state[key] = default

        st.session_state["_force_refresh"] = True
        st.rerun()

def weekly_table(username: str, is_admin: bool):
    st.subheader("📋 ตารางคิว (สัปดาห์นี้)")

    st.markdown("""
        <style>
            .header {background:#4CAF50; color:white; font-weight:700; padding:8px; text-align:center; border-radius:6px;}
            .cell {padding:8px 10px; border-bottom:1px solid #e9ecef;}
            .cell.left {text-align:left;}
            .cell.center {text-align:center;}
            .row-wrap {padding:2px 0;}
        </style>
    """, unsafe_allow_html=True)

    start, end = current_week_bounds()
    df = fetch_week(start, end)
    if df.empty:
        st.info("ℹ️ ไม่มีการจองในสัปดาห์นี้")
        return

    header_cols = st.columns([1,1,2,2,2,1.5,3,1.2,1])
    headers = ["วันที่","เวลา","บริษัท","รับ","ส่ง","โทร","หมายเหตุ","ผู้จอง","ยกเลิก"]
    aligns  = ["center","center","left","left","left","center","left","center","center"]
    for col, text, align in zip(header_cols, headers, aligns):
        col.markdown(f"<div class='header'>{text}</div>", unsafe_allow_html=True)

    for _, r in df.iterrows():
        row_cols = st.columns([1,1,2,2,2,1.5,3,1.2,1])
        row_cols[0].markdown(f"<div class='cell center row-wrap'>{r['booking_date'].strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)
        row_cols[1].markdown(f"<div class='cell center row-wrap'>{hhmm(r['booking_time'])}</div>", unsafe_allow_html=True)
        row_cols[2].markdown(f"<div class='cell left   row-wrap'>{(r['company'] or '')}</div>", unsafe_allow_html=True)
        row_cols[3].markdown(f"<div class='cell left   row-wrap'>{(r['pickup'] or '')}</div>", unsafe_allow_html=True)
        row_cols[4].markdown(f"<div class='cell left   row-wrap'>{(r['dropoff'] or '')}</div>", unsafe_allow_html=True)
        row_cols[5].markdown(f"<div class='cell center row-wrap'>{(r['phone'] or '')}</div>", unsafe_allow_html=True)
        row_cols[6].markdown(f"<div class='cell left   row-wrap'>{(r['note'] or '')}</div>", unsafe_allow_html=True)
        row_cols[7].markdown(f"<div class='cell center row-wrap'>{(r['user'] or '')}</div>", unsafe_allow_html=True)

        if is_admin or (r["user"] == username):
            with row_cols[8]:
                if st.button("❌", key=f"del_{r['id']}", help="ยกเลิกคิวนี้"):
                    delete_booking(int(r["id"]))
                    st.success("ลบรายการสำเร็จ")
                    st.session_state["_force_refresh"] = True
                    st.rerun()
        else:
            row_cols[8].markdown("<div class='cell center row-wrap'>-</div>", unsafe_allow_html=True)

def weekly_calendar():
    st.subheader("📆 ปฏิทินรายสัปดาห์ (เวลาว่าง/จองแล้ว)")

    start, end = current_week_bounds()
    df = fetch_week(start, end)

    days = [(start + datetime.timedelta(days=i)) for i in range(7)]
    grid = []
    for t in TIME_SLOTS:
        row = {"เวลา": hhmm(t)}
        for d in days:
            row[d.strftime("%a %d/%m")] = "✅ ว่าง"
        grid.append(row)
    cal = pd.DataFrame(grid)

    if not df.empty:
        for _, r in df.iterrows():
            col = r["booking_date"].strftime("%a %d/%m")
            idx = cal.index[cal["เวลา"] == hhmm(r["booking_time"])]
            if len(idx) > 0 and col in cal.columns:
                cal.loc[idx[0], col] = f"❌ {r['user']}"

    st.dataframe(cal, use_container_width=True)

# ================= Main Entry =================
def program_messenger_booking():
    init_db()
    st.header("🚚 ระบบจองคิวแมสเซ็นเจอร์ (SQLite)")

    username = st.session_state.get("username", "Guest")
    role = st.session_state.get("role", "User")
    is_admin = (role == "Admin")

    weekly_calendar()
    st.markdown("---")
    weekly_table(username=username, is_admin=is_admin)
    st.markdown("---")
    booking_form(username=username)
