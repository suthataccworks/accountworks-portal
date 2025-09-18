import streamlit as st
import datetime
from modules import auth_gsheet as auth

# ================= CONFIG =================
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
    .menu-container {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 30px;
    }
    .menu-card {
        width: 280px;
        height: 200px;
        background: white;
        border-radius: 18px;
        box-shadow: 0 6px 15px rgba(0,0,0,0.1);
        text-align: center;
        padding: 30px 20px;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .menu-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 15px 25px rgba(0,0,0,0.15);
        background: #f0f8ff;
    }
    .menu-icon {
        font-size: 50px;
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
        margin: 60px auto 0 auto;
        background: #e74c3c;
        color: white !important;
        font-size: 18px;
        font-weight: bold;
        padding: 12px 35px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 6px 12px rgba(231,76,60,0.4);
        text-decoration: none;
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

    st.markdown('<div class="menu-container">', unsafe_allow_html=True)

    # เมนูการ์ด
    st.markdown("""
        <div class="menu-card" onclick="window.parent.location.href='?page=leave'">
            <div class="menu-icon">🏖</div>
            <div class="menu-title">ลางาน</div>
            <div class="menu-desc">ยื่นคำขอลา ตรวจสอบวันลา</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="menu-card" onclick="window.parent.location.href='?page=messenger'">
            <div class="menu-icon">📦</div>
            <div class="menu-title">จองคิวแมสเซ็นเจอร์</div>
            <div class="menu-desc">จองแมสเพื่อส่งเอกสารและพัสดุ</div>
        </div>
    """, unsafe_allow_html=True)

    if role == "admin":
        st.markdown("""
            <div class="menu-card" onclick="window.parent.location.href='?page=user_mgmt'">
                <div class="menu-icon">⚙️</div>
                <div class="menu-title">จัดการผู้ใช้</div>
                <div class="menu-desc">เพิ่ม/แก้ไข/ลบ ผู้ใช้งานระบบ</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ปุ่ม Logout ตรงกลาง
    if st.markdown('<a class="logout-btn" href="?page=login">🚪 Logout</a>', unsafe_allow_html=True):
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
        st.write("📌 ฟอร์มการลา (กำลังพัฒนา)")
    elif st.session_state.page == "messenger":
        st.write("📌 ระบบจองคิวแมสเซ็นเจอร์ (กำลังพัฒนา)")
    elif st.session_state.page == "user_mgmt":
        st.write("📌 จัดการผู้ใช้ (Admin Only)")
