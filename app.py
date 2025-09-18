import streamlit as st
import datetime
from modules import auth_gsheet as auth
from modules import leave_gsheet

# ================== CONFIG ==================
st.set_page_config(page_title="AccountWorks Portal", page_icon="🔐", layout="wide")

# ================== CSS ==================
st.markdown("""
    <style>
    body {
        background: linear-gradient(135deg, #f9f9f9 0%, #e3f2fd 100%);
        font-family: "Segoe UI", sans-serif;
    }
    .portal-title {
        text-align:center;
        font-size:36px;
        font-weight:800;
        color:#2c3e50;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# ================== SESSION ==================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"

# ================== LOGIN ==================
def login_page():
    st.markdown("<div class='portal-title'>🔐 AccountWorks Portal</div>", unsafe_allow_html=True)
    st.subheader("เข้าสู่ระบบ")

    with st.form("login_form", clear_on_submit=True):
        username = st.text_input("👤 Username")
        password = st.text_input("🔑 Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        user = auth.check_login(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.user = user
            st.session_state.page = "welcome"
            st.rerun()
        else:
            st.error("❌ Username หรือ Password ไม่ถูกต้อง")

# ================== WELCOME ==================
def welcome_page():
    user = st.session_state.user
    st.markdown(
        f"""
        <div style="text-align:center; padding:40px;
            background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius:20px; color:white; margin:30px auto; max-width:750px;">
            <h1>👋 สวัสดีคุณ {user['Username']}</h1>
            <p style="font-size:18px;">Role: <b>{user['Role']}</b></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("➡️ เข้าสู่เมนูหลัก", use_container_width=True):
            st.session_state.page = "main"
            st.rerun()
    with col2:
        if st.button("🚪 Logout", use_container_width=True, key="logout1"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.page = "login"
            st.rerun()

# ================== MAIN MENU ==================
def main_menu():
    st.markdown("<div class='portal-title'>📌 Main Menu</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🏖 ลางาน", use_container_width=True):
            st.session_state.page = "leave"
            st.rerun()

    with col2:
        if st.button("📦 จองคิวแมสเซ็นเจอร์", use_container_width=True):
            st.info("⏳ กำลังพัฒนา...")

    with col3:
        if st.session_state.user["Role"].lower() in ["admin", "manager"]:
            if st.button("📝 ตรวจสอบการลา", use_container_width=True):
                st.session_state.page = "leave_admin"
                st.rerun()

    st.divider()
    colA, colB, colC = st.columns([1,1,1])
    with colB:
        if st.button("🚪 Logout", use_container_width=True, key="logout2"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.page = "login"
            st.rerun()

# ================== LEAVE FORM ==================
def leave_form():
    st.subheader("🏖 แบบฟอร์มการลา")

    leave_type = st.selectbox("ประเภทการลา", ["ลากิจ", "ลาป่วย", "ลาพักร้อน"])
    start_date = st.date_input("วันที่เริ่มลา", datetime.date.today())
    end_date = st.date_input("วันที่สิ้นสุด")
    reason = st.text_area("เหตุผลการลา")

    if st.button("✅ ส่งคำขอลา", use_container_width=True):
        leave_gsheet.submit_leave(
            st.session_state.user["Username"],
            leave_type,
            str(start_date),
            str(end_date),
            reason
        )
        st.success("📌 ส่งคำขอลาเรียบร้อยแล้ว (รอหัวหน้าอนุมัติ)")
        st.session_state.page = "main"
        st.rerun()

    if st.button("⬅️ กลับเมนูหลัก", use_container_width=True):
        st.session_state.page = "main"
        st.rerun()

# ================== LEAVE ADMIN (Approve) ==================
def leave_admin():
    st.subheader("📝 ตรวจสอบการลา (สำหรับหัวหน้า/Admin)")

    leaves = leave_gsheet.get_all_leaves()
    if not leaves:
        st.info("✅ ยังไม่มีคำขอลา")
    else:
        st.table(leaves)

    approve_user = st.text_input("ชื่อผู้ใช้ที่ต้องการอนุมัติ")
    if st.button("✅ อนุมัติ"):
        leave_gsheet.update_leave_status(approve_user, "Approved")
        st.success(f"✅ อนุมัติการลา {approve_user} แล้ว")
        st.rerun()

    reject_user = st.text_input("ชื่อผู้ใช้ที่ต้องการปฏิเสธ")
    if st.button("❌ ปฏิเสธ"):
        leave_gsheet.update_leave_status(reject_user, "Rejected")
        st.warning(f"❌ ปฏิเสธการลา {reject_user} แล้ว")
        st.rerun()

    if st.button("⬅️ กลับเมนูหลัก", use_container_width=True):
        st.session_state.page = "main"
        st.rerun()

# ================== ROUTER ==================
if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.page == "welcome":
        welcome_page()
    elif st.session_state.page == "main":
        main_menu()
    elif st.session_state.page == "leave":
        leave_form()
    elif st.session_state.page == "leave_admin":
        leave_admin()
