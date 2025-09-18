import streamlit as st
import datetime
from modules import auth_gsheet as auth


# ========== CONFIG ==========
st.set_page_config(page_title="AccountWorks Portal", page_icon="🔐", layout="wide")

# CSS Custom
st.markdown("""
    <style>
    body {
        background: linear-gradient(135deg, #f9f9f9 0%, #e3f2fd 100%);
        font-family: "Segoe UI", sans-serif;
    }
    .portal-title {
        text-align:center;
        font-size:38px;
        font-weight:800;
        color:#2c3e50;
        margin-bottom: 30px;
    }
    .menu-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 25px;
        margin-top: 30px;
    }
    .menu-card {
        background: white;
        padding: 30px;
        border-radius: 18px;
        text-align: center;
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .menu-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    }
    .menu-icon {
        font-size: 55px;
        margin-bottom: 15px;
    }
    .menu-title {
        font-size: 20px;
        font-weight: bold;
        color: #2c3e50;
    }
    .menu-desc {
        font-size: 14px;
        color: #555;
        margin-top: 5px;
    }
    .logout-btn {
        background: #e74c3c;
        color: white !important;
        border-radius: 10px;
        padding: 8px 18px;
    }
    </style>
""", unsafe_allow_html=True)


# ========== SESSION ==========
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"


# ========== LOGIN ==========
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

    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("➡️ เข้าสู่เมนูหลัก"):
            st.session_state.page = "main"
            st.rerun()
    with col2:
        if st.button("🚪 Logout", key="logout1"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.page = "login"
            st.rerun()


# ========== MAIN MENU ==========
def main_menu():
    st.markdown("<div class='portal-title'>📌 Main Menu</div>", unsafe_allow_html=True)

    st.markdown('<div class="menu-grid">', unsafe_allow_html=True)

    st.markdown(f"""
        <div class="menu-card" onclick="window.parent.streamlitSend('leave_form')">
            <div class="menu-icon">🏖</div>
            <div class="menu-title">ลางาน</div>
            <div class="menu-desc">ยื่นคำขอลา ตรวจสอบวันลา</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="menu-card" onclick="window.parent.streamlitSend('messenger')">
            <div class="menu-icon">📦</div>
            <div class="menu-title">จองคิวแมสเซ็นเจอร์</div>
            <div class="menu-desc">จองแมสเพื่อส่งเอกสารและพัสดุ</div>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.user["Role"].lower() == "admin":
        st.markdown(f"""
            <div class="menu-card" onclick="window.parent.streamlitSend('user_mgmt')">
                <div class="menu-icon">⚙️</div>
                <div class="menu-title">จัดการผู้ใช้</div>
                <div class="menu-desc">เพิ่ม/แก้ไข/ลบ ผู้ใช้งานระบบ</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    if st.button("⬅️ กลับ Welcome"):
        st.session_state.page = "welcome"
        st.rerun()
    if st.button("🚪 Logout", key="logout2"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.page = "login"
        st.rerun()


# ========== LEAVE FORM ==========
def leave_form():
    st.subheader("🏖 แบบฟอร์มการลา")
    leave_type = st.selectbox("ประเภทการลา", ["ลากิจ", "ลาป่วย", "ลาพักร้อน"])
    start_date = st.date_input("วันที่เริ่มลา", datetime.date.today())
    end_date = st.date_input("วันที่สิ้นสุด")
    reason = st.text_area("เหตุผลการลา")

    if st.button("✅ ส่งคำขอลา"):
        st.success("📌 ส่งคำขอลาเรียบร้อยแล้ว (รอหัวหน้าอนุมัติ)")
        st.session_state.page = "main"
        st.rerun()

    if st.button("⬅️ กลับเมนูหลัก"):
        st.session_state.page = "main"
        st.rerun()


# ========== USER MANAGEMENT ==========
def user_management():
    st.subheader("⚙️ จัดการผู้ใช้ (Admin Only)")

    users = auth.get_all_users()
    st.table(users)

    st.markdown("### ➕ เพิ่มผู้ใช้ใหม่")
    new_user = st.text_input("Username (ใหม่)")
    new_pass = st.text_input("Password (ใหม่)", type="password")
    new_role = st.selectbox("Role", ["Admin", "User", "Staff"])
    if st.button("✅ เพิ่มผู้ใช้"):
        auth.add_user(new_user, new_pass, new_role)
        st.success("เพิ่มผู้ใช้เรียบร้อยแล้ว ✅")
        st.rerun()

    st.markdown("### 📝 อัปเดตผู้ใช้")
    target_user = st.text_input("เลือก Username ที่ต้องการแก้ไข")
    upd_pass = st.text_input("รหัสผ่านใหม่", type="password")
    upd_role = st.selectbox("Role ใหม่", ["Admin", "User", "Staff"], key="upd_role")
    if st.button("💾 บันทึกการแก้ไข"):
        auth.update_user(target_user, upd_pass, upd_role)
        st.success("อัปเดตผู้ใช้เรียบร้อย ✅")
        st.rerun()

    st.markdown("### ❌ ลบผู้ใช้")
    del_user = st.text_input("Username ที่ต้องการลบ")
    if st.button("🗑 ลบผู้ใช้"):
        auth.delete_user(del_user)
        st.warning(f"ลบผู้ใช้ {del_user} เรียบร้อยแล้ว")
        st.rerun()

    if st.button("⬅️ กลับเมนูหลัก"):
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
