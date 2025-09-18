import streamlit as st
import datetime
from modules import auth_gsheet as auth
from modules import leave_gsheet

# ========== CONFIG ==========
st.set_page_config(page_title="AccountWorks Portal", page_icon="🔐", layout="wide")

# ========== SESSION ==========
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"

# ========== LOGIN ==========
def login_page():
    st.markdown("<h2 style='text-align:center;'>🔐 AccountWorks Portal</h2>", unsafe_allow_html=True)

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

# ========== WELCOME ==========
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

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➡️ เข้าสู่เมนูหลัก", key="go_main_from_welcome"):
            st.session_state.page = "main"
            st.rerun()
    with col2:
        if st.button("🚪 Logout", key="logout_from_welcome"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.page = "login"
            st.rerun()

# ========== MAIN MENU ==========
def main_menu():
    st.markdown("<h2 style='text-align:center;'>📌 Main Menu</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🏖 ลางาน", key="btn_leave"):
            st.session_state.page = "leave_form"
            st.rerun()

    with col2:
        if st.button("📦 จองคิวแมสเซ็นเจอร์", key="btn_messenger"):
            st.info("⏳ ฟีเจอร์นี้กำลังพัฒนา...")

    if st.session_state.user["Role"].lower() == "admin":
        with col3:
            if st.button("⚙️ จัดการผู้ใช้", key="btn_user_mgmt"):
                st.session_state.page = "user_mgmt"
                st.rerun()

    st.divider()
    if st.button("🚪 Logout", key="logout_from_main"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.page = "login"
        st.rerun()

# ========== LEAVE FORM ==========
def leave_form():
    st.subheader("🏖 แบบฟอร์มการลา")

    leave_type = st.selectbox("ประเภทการลา", ["ลากิจ", "ลาป่วย", "ลาพักร้อน"], key="leave_type")
    start_date = st.date_input("วันที่เริ่มลา", datetime.date.today(), key="start_date")
    end_date = st.date_input("วันที่สิ้นสุด", key="end_date")
    reason = st.text_area("เหตุผลการลา", key="leave_reason")

    if "leave_submitted" not in st.session_state:
        st.session_state.leave_submitted = False
        st.session_state.leave_message = ""

    if st.button("✅ ส่งคำขอลา", key="submit_leave"):
        success, msg = leave_gsheet.submit_leave(
            st.session_state.user["Username"], leave_type, start_date, end_date, reason
        )
        st.session_state.leave_submitted = True
        st.session_state.leave_message = msg

    if st.session_state.leave_submitted:
        if "✅" in st.session_state.leave_message:
            st.success(st.session_state.leave_message)
        else:
            st.error(st.session_state.leave_message)

        if st.button("⬅️ กลับเมนูหลัก", key="back_main_from_leave"):
            st.session_state.page = "main"
            st.session_state.leave_submitted = False
            st.session_state.leave_message = ""
            st.rerun()

# ========== USER MANAGEMENT ==========
def user_management():
    st.subheader("⚙️ จัดการผู้ใช้ (Admin Only)")

    users = auth.get_all_users(mask_password=True)
    st.write("### 👥 รายชื่อผู้ใช้ทั้งหมด")
    st.table(users)

    st.divider()

    # เพิ่มผู้ใช้
    st.write("### ➕ เพิ่มผู้ใช้ใหม่")
    new_user = st.text_input("Username (ใหม่)", key="new_user")
    new_pass = st.text_input("Password (ใหม่)", type="password", key="new_pass")
    new_role = st.selectbox("Role", ["Admin", "User", "Staff"], key="new_role")
    if st.button("✅ เพิ่มผู้ใช้", key="add_user"):
        ok, msg = auth.add_user(new_user, new_pass, new_role)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    st.divider()

    # แก้ไขผู้ใช้
    st.write("### 📝 แก้ไขผู้ใช้")
    target_user = st.text_input("Username ที่ต้องการแก้ไข", key="upd_user")
    upd_pass = st.text_input("รหัสผ่านใหม่", type="password", key="upd_pass")
    upd_role = st.selectbox("Role ใหม่", ["Admin", "User", "Staff"], key="upd_role")
    if st.button("💾 บันทึกการแก้ไข", key="update_user"):
        ok, msg = auth.update_user(target_user, upd_pass, upd_role)
        if ok:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    st.divider()

    # ลบผู้ใช้
    st.write("### ❌ ลบผู้ใช้")
    del_user = st.text_input("Username ที่ต้องการลบ", key="del_user")
    if st.button("🗑 ลบผู้ใช้", key="delete_user"):
        ok, msg = auth.delete_user(del_user)
        if ok:
            st.warning(msg)
            st.rerun()
        else:
            st.error(msg)

    st.divider()
    if st.button("⬅️ กลับเมนูหลัก", key="back_main_from_user_mgmt"):
        st.session_state.page = "main"
        st.rerun()

# ========== ROUTER ==========
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
