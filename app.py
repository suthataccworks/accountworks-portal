import streamlit as st
import datetime
from modules import auth_gsheet as auth
from modules import leave_gsheet

# ================== CONFIG ==================
st.set_page_config(page_title="AccountWorks Portal", page_icon="🔐", layout="wide")

# ================== SESSION ==================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"

# ================== LOGIN ==================
def login_page():
    st.markdown("<h2 style='text-align:center;'>🔐 AccountWorks Portal</h2>", unsafe_allow_html=True)
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
        if st.button("➡️ เข้าสู่เมนูหลัก"):
            st.session_state.page = "main"
            st.rerun()
    with col2:
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.page = "login"
            st.rerun()

# ================== MAIN MENU ==================
def main_menu():
    st.markdown("<h2 style='text-align:center;'>📌 Main Menu</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🏖 ลางาน", use_container_width=True):
            st.session_state.page = "leave_form"
            st.rerun()

    with col2:
        if st.button("📦 จองคิวแมสเซ็นเจอร์", use_container_width=True):
            st.info("⏳ กำลังพัฒนา...")

    with col3:
        if st.session_state.user["Role"].lower() == "admin":
            if st.button("⚙️ จัดการผู้ใช้", use_container_width=True):
                st.session_state.page = "user_mgmt"
                st.rerun()

    st.divider()
    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    if st.button("🚪 Logout", key="logout_center"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.page = "login"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ================== LEAVE FORM ==================
def leave_form():
    st.subheader("🏖 แบบฟอร์มการลา")

    leave_type = st.selectbox("ประเภทการลา", ["ลากิจ", "ลาป่วย", "ลาพักร้อน"])
    start_date = st.date_input("วันที่เริ่มลา", datetime.date.today())
    end_date = st.date_input("วันที่สิ้นสุด")
    reason = st.text_area("เหตุผลการลา")

    if "leave_submitted" not in st.session_state:
        st.session_state.leave_submitted = False
        st.session_state.leave_message = ""

    if st.button("✅ ส่งคำขอลา"):
        success, msg = leave_gsheet.submit_leave(
            st.session_state.user["Username"],
            leave_type,
            start_date,
            end_date,
            reason
        )
        st.session_state.leave_submitted = True
        st.session_state.leave_message = msg

    if st.session_state.leave_submitted:
        if "✅" in st.session_state.leave_message:
            st.success(st.session_state.leave_message)
        else:
            st.error(st.session_state.leave_message)

        if st.button("⬅️ กลับเมนูหลัก"):
            st.session_state.page = "main"
            st.session_state.leave_submitted = False
            st.session_state.leave_message = ""
            st.rerun()

# ================== USER MANAGEMENT ==================
def user_management():
    st.subheader("⚙️ จัดการผู้ใช้ (Admin Only)")
    st.info("⏳ กำลังพัฒนา...")

    if st.button("⬅️ กลับเมนูหลัก"):
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
    elif st.session_state.page == "leave_form":
        leave_form()
    elif st.session_state.page == "user_mgmt":
        user_management()
