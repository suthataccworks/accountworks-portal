import streamlit as st
import datetime
from modules import auth_gsheet as auth
import streamlit as st

st.set_page_config(page_title="AccountWorks Portal", page_icon="🔐", layout="wide")

# ========== CSS ==========
st.markdown("""
    <style>
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
if "page" not in st.session_state:
    st.session_state.page = "main"

# ========== MAIN MENU ==========
def main_menu():
    st.markdown("<div class='portal-title'>📌 Main Menu</div>", unsafe_allow_html=True)

    st.markdown('<div class="menu-grid">', unsafe_allow_html=True)

    # ใช้ st.markdown + form แทน st.button → ให้คลิกได้ทั้ง card
    with st.form("leave_form_btn"):
        if st.form_submit_button(
            "🏖 ลางาน\nยื่นคำขอลา ตรวจสอบวันลา",
            use_container_width=True
        ):
            st.session_state.page = "leave_form"
            st.rerun()

    with st.form("messenger_btn"):
        if st.form_submit_button(
            "📦 จองคิวแมสเซ็นเจอร์\nจองแมสเพื่อส่งเอกสารและพัสดุ",
            use_container_width=True
        ):
            st.session_state.page = "messenger"
            st.rerun()

    with st.form("user_mgmt_btn"):
        if st.form_submit_button(
            "⚙️ จัดการผู้ใช้\nเพิ่ม/แก้ไข/ลบ ผู้ใช้งานระบบ",
            use_container_width=True
        ):
            st.session_state.page = "user_mgmt"
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # Logout ปุ่มตรงกลาง
    st.markdown('<div style="text-align:center;">', unsafe_allow_html=True)
    if st.button("🚪 Logout", key="logout_center"):
        st.session_state.page = "login"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ========== ROUTER ==========
if st.session_state.page == "main":
    main_menu()
elif st.session_state.page == "leave_form":
    st.write("📄 หน้าฟอร์มการลา (ยังไม่ทำ)")
elif st.session_state.page == "messenger":
    st.write("📦 หน้าจองคิวแมส (ยังไม่ทำ)")
elif st.session_state.page == "user_mgmt":
    st.write("⚙️ หน้าจัดการผู้ใช้ (ยังไม่ทำ)")
elif st.session_state.page == "login":
    st.write("🔑 หน้าล็อกอิน (ยังไม่ทำ)")
