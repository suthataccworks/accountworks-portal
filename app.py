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
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 30px;
        margin: 40px auto;
        max-width: 1000px;
    }
    .menu-card {
        background: white;
        padding: 40px 20px;
        border-radius: 18px;
        text-align: center;
        box-shadow: 0 6px 18px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        cursor: pointer;
        height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .menu-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 30px rgba(0,0,0,0.15);
        background: #f0f8ff;
    }
    .menu-icon {
        font-size: 60px;
        margin-bottom: 15px;
    }
    .menu-title {
        font-size: 22px;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 8px;
    }
    .menu-desc {
        font-size: 15px;
        color: #555;
    }
    .logout-btn {
        display: block;
        margin: 50px auto;
        background: #e74c3c;
        color: white !important;
        font-size: 18px;
        font-weight: bold;
        padding: 12px 30px;
        border-radius: 12px;
        text-align: center;
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
            st.session_state.page = "main"
            st.rerun()
        else:
            st.error("❌ Username หรือ Password ไม่ถูกต้อง")

# ========== MAIN MENU ==========
def main_menu():
    st.markdown("<div class='portal-title'>📌 Main Menu</div>", unsafe_allow_html=True)

    # เมนู
    st.markdown('<div class="menu-grid">', unsafe_allow_html=True)

    # ลางาน
    if st.button("🏖 ลางาน", key="leave_btn"):
        st.session_state.page = "leave_form"
        st.rerun()

    # จองคิวแมส
    if st.button("📦 จองคิวแมสเซ็นเจอร์", key="msg_btn"):
        st.info("⏳ ฟีเจอร์กำลังพัฒนา...")

    # Admin เท่านั้น
    if st.session_state.user["Role"].lower() == "admin":
        if st.button("⚙️ จัดการผู้ใช้", key="admin_btn"):
            st.session_state.page = "user_mgmt"
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # Logout ตรงกลาง
    st.markdown('<div style="text-align:center;">', unsafe_allow_html=True)
    if st.button("🚪 Logout", key="logout_center"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.page = "login"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ========== ROUTER ==========
if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.page == "main":
        main_menu()
