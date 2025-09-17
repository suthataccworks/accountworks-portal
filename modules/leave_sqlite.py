import sqlite3
import pandas as pd
import streamlit as st
import datetime

DB_FILE = "leave_system.db"

# ================= Database Init =================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # ตารางคำขอลา
    c.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            leave_type TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            days INTEGER NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'รออนุมัติ',
            approver TEXT
        )
    """)

    # ตารางโควต้าวันลา
    c.execute("""
        CREATE TABLE IF NOT EXISTS leave_balance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            sick_leave INTEGER DEFAULT 10,
            business_leave INTEGER DEFAULT 7,
            annual_leave INTEGER DEFAULT 10,
            maternity_leave INTEGER DEFAULT 90,
            monk_leave INTEGER DEFAULT 15
        )
    """)

    conn.commit()
    conn.close()

# ================= CRUD =================
def add_leave_request(username, leave_type, start_date, end_date, days, reason):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO leave_requests (username, leave_type, start_date, end_date, days, reason)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, leave_type, start_date, end_date, days, reason))
    conn.commit()
    conn.close()

def get_all_requests():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM leave_requests ORDER BY start_date DESC", conn)
    conn.close()
    return df

def update_request_status(request_id, status, approver):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        UPDATE leave_requests
        SET status=?, approver=?
        WHERE id=?
    """, (status, approver, request_id))
    conn.commit()
    conn.close()

def get_leave_balance(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM leave_balance WHERE username=?", (username,))
    row = c.fetchone()

    # ถ้ายังไม่มี quota → สร้างใหม่
    if not row:
        c.execute("INSERT INTO leave_balance (username) VALUES (?)", (username,))
        conn.commit()
        c.execute("SELECT * FROM leave_balance WHERE username=?", (username,))
        row = c.fetchone()

    conn.close()
    return row

# ================= UI Components =================
def request_leave_ui(username="ไม่ระบุ"):
    st.subheader("📋 ฟอร์มขอลางาน")

    leave_type = st.selectbox("ประเภทการลา", ["ลากิจ", "ลาป่วย", "ลาพักร้อน", "ลาคลอด", "ลาบวช"])
    start_date = st.date_input("วันเริ่มลา", min_value=datetime.date.today())
    end_date = st.date_input("วันสิ้นสุดลา", min_value=start_date)
    reason = st.text_area("เหตุผลการลา")

    days = (end_date - start_date).days + 1

    # quota
    balance = get_leave_balance(username)
    quota_map = {
        "ลาป่วย": balance[2],
        "ลากิจ": balance[3],
        "ลาพักร้อน": balance[4],
        "ลาคลอด": balance[5],
        "ลาบวช": balance[6],
    }
    st.info(f"📊 สิทธิ์คงเหลือ: {quota_map}")

    if st.button("✅ ส่งคำขอลา"):
        if quota_map.get(leave_type, 0) < days:
            st.warning(f"⚠️ วันลาคงเหลือไม่พอ (เหลือ {quota_map.get(leave_type,0)} วัน) — หากอนุมัติจะถือเป็นลาโดยไม่รับค่าจ้าง")
        add_leave_request(username, leave_type, str(start_date), str(end_date), days, reason)
        st.success(f"🎉 ส่งคำขอลา {leave_type} สำเร็จ ({days} วัน)")

def my_leave_history(username):
    st.subheader("🗂️ ประวัติการลาของฉัน")
    df = get_all_requests()
    df = df[df["username"] == username]

    if df.empty:
        st.info("ยังไม่มีประวัติการลา")
    else:
        st.dataframe(df, use_container_width=True)

def manage_leave_requests_ui(role, approver="Admin"):
    st.subheader("📑 จัดการคำขอลางาน")

    df = get_all_requests()
    if df.empty:
        st.info("ยังไม่มีคำขอลา")
        return

    for _, row in df.iterrows():
        with st.expander(f"#{row['id']} | {row['username']} | {row['leave_type']} | {row['start_date']} → {row['end_date']} | {row['status']}"):
            st.write(f"📝 เหตุผล: {row['reason']}")
            st.write(f"📅 จำนวนวัน: {row['days']} วัน")
            st.write(f"👤 ผู้อนุมัติ: {row['approver'] if row['approver'] else '-'}")

            if row["status"] == "รออนุมัติ":
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✅ อนุมัติ #{row['id']}", key=f"approve_{row['id']}"):
                        update_request_status(row["id"], "อนุมัติ", approver)
                        st.success("อนุมัติเรียบร้อยแล้ว")
                        st.rerun()
                with col2:
                    if st.button(f"❌ ไม่อนุมัติ #{row['id']}", key=f"reject_{row['id']}"):
                        update_request_status(row["id"], "ไม่อนุมัติ", approver)
                        st.error("ปฏิเสธเรียบร้อยแล้ว")
                        st.rerun()

def leave_calendar_view():
    st.subheader("📅 ปฏิทินการลางาน (7 วันถัดไป)")

    today = datetime.date.today()
    week_days = [today + datetime.timedelta(days=i) for i in range(7)]

    df = get_all_requests()
    if df.empty:
        st.info("ยังไม่มีข้อมูลการลาในสัปดาห์นี้")
        return

    timeslot = {d.strftime("%a %d/%m"): "" for d in week_days}

    for _, row in df.iterrows():
        start = datetime.datetime.strptime(row["start_date"], "%Y-%m-%d").date()
        end = datetime.datetime.strptime(row["end_date"], "%Y-%m-%d").date()
        for d in week_days:
            if start <= d <= end:
                status = row["status"]
                label = f"{row['username']} ({row['leave_type']})"
                if status == "อนุมัติ":
                    timeslot[d.strftime("%a %d/%m")] += f"🟢 {label}\n"
                elif status == "รออนุมัติ":
                    timeslot[d.strftime("%a %d/%m")] += f"🟠 {label}\n"
                elif status == "ไม่อนุมัติ":
                    timeslot[d.strftime("%a %d/%m")] += f"🔴 {label}\n"

    df_calendar = pd.DataFrame.from_dict(timeslot, orient="index", columns=["การลา"])
    st.dataframe(df_calendar, use_container_width=True)

# ================= Main Program =================
def program_leave_system(username="ไม่ระบุ", role="User"):
    init_db()
    st.title("🏖️ ระบบจัดการการลางาน")

    if role in ["Admin", "Staff"]:
        menu = ["✍ ขอลางาน", "🗂️ ประวัติการลา", "📑 จัดการคำขอลา", "📅 ปฏิทินการลา"]
    else:
        menu = ["✍ ขอลางาน", "🗂️ ประวัติการลา", "📅 ปฏิทินการลา"]

    choice = st.radio("เมนู", menu, horizontal=True)

    if choice == "✍ ขอลางาน":
        request_leave_ui(username=username)
    elif choice == "🗂️ ประวัติการลา":
        my_leave_history(username)
    elif choice == "📑 จัดการคำขอลา":
        manage_leave_requests_ui(role=role, approver=username)
    elif choice == "📅 ปฏิทินการลา":
        leave_calendar_view()
