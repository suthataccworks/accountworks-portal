import streamlit as st
import datetime
from modules import auth_gsheet as auth

st.set_page_config(page_title="AccountWorks Portal", page_icon="🔐", layout="wide")

# ================= CSS =================
st.markdown("""
    <style>
    body {
        background: linear-gradient(135deg, #f8f9fa, #eef2f7);
        font-family: 'Segoe UI', sans-serif;
    }
    .portal-title {
        text-align:center;
        font-size:40px;
        font-weight:800;
        color:#2c3e50;
        margin: 20px 0 40px 0;
    }
    .menu-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 25px;
        max-width: 1000px;
        margin: auto;
    }
    .menu-card {
        background: white;
        border-radius: 20px;
        padding: 40px 20px;
        text-align: center;
        box-shadow: 0 8px 18px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .menu-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 15px 30px rgba(0,0,0,0.2);
        background: #f0f8ff;
    }
    .menu-icon {
        font-size: 55px;
        margin-bottom: 15px;
    }
    .menu-title {
        font-size: 22px;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 10px;
    }
    .menu-desc {
        font-size: 15px;
        color: #555;
    }
    .logout-btn {
        display: block;
        margin: 50px auto 0 auto;
        background: #e74c3c;
        color: white !important;
        font-size: 18px;
        font-weight: bold;
        padding: 12px 35px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 6px 12px rgba(231,76,60,0.4);
    }
    .logout-btn:hover {
        background: #c0392b;
    }
    </style>
""", unsafe_allow_html=True)

# ================= SESSION =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"

# ================= LOGIN =================
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

# ================= MAIN MENU =================
def main_menu():
    st.markdown("<div class='portal-title'>📌 Main Menu</div>", unsafe_allow_html=True)

    user = st.session_state.user
    role = user["Role"].lower()

    st.markdown('<div class="menu-grid">', unsafe_allow_html=True)

    # เมนูการ์ด
    if st.button("🏖 ลางาน\n\nยื่นคำขอลา ตรวจสอบวันลา", key="leave", use_container_width=True):
        st.session_state.page = "leave"
        st.rerun()

    if st.button("📦 จองคิวแมสเซ็นเจอร์\n\nจองแมสเพื่อส่งเอกสารและพัสดุ", key="messenger", use_container_width=True):
        st.session_state.page = "messenger"
        st.rerun()

    if role == "admin":
        if st.button("⚙️ จัดการผู้ใช้\n\nเพิ่ม/แก้ไข/ลบ ผู้ใช้งานระบบ", key="user_mgmt", use_container_width=True):
            st.session_state.page = "user_mgmt"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # ปุ่ม Logout
    st.write("")
    st.write("")
    if st.button("🚪 Logout", key="logout", use_container_width=False):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.page = "login"
        st.rerun()

# ================= ROUTER =================
if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.page == "main":
        main_menu()
    elif st.session_state.page == "leave":
        st.subheader("📌 ฟอร์มการลา (กำลังพัฒนา)")
        if st.button("⬅️ กลับเมนูหลัก"):
            st.session_state.page = "main"
            st.rerun()
    elif st.session_state.page == "messenger":
        st.subheader("📌 ระบบจองคิวแมสเซ็นเจอร์ (กำลังพัฒนา)")
        if st.button("⬅️ กลับเมนูหลัก"):
            st.session_state.page = "main"
            st.rerun()
    elif st.session_state.page == "user_mgmt":
        st.subheader("📌 จัดการผู้ใช้ (Admin Only)")
        if st.button("⬅️ กลับเมนูหลัก"):
            st.session_state.page = "main"
            st.rerun()
