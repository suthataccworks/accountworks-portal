import streamlit as st
import datetime
from modules import auth_gsheet as auth
from modules import leave_gsheet

st.set_page_config(page_title="AccountWorks Portal", page_icon="🔐", layout="wide")

# ================== Custom CSS ==================
st.markdown(
    """
    <style>
    body {
        background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
    }
    .title {
        text-align: center;
        font-size: 36px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .welcome-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 50px;
        border-radius: 20px;
        text-align: center;
        color: white;
        box-shadow: 0 6px 25px rgba(0,0,0,0.25);
        margin: 30px auto;
        max-width: 700px;
    }
    /* ✅ Responsive Menu */
    .menu-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 25px;
        margin-top: 30px;
    }
    .menu-card {
        border-radius: 20px;
        padding: 30px;
        background: white;
        box-shadow: 0 6px 20px rgba(0,0,0,0.1);
        text-align: center;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .menu-card:hover {
        transform: translateY(-8px) scale(1.03);
        box-shadow: 0 12px 25px rgba(0,0,0,0.2);
    }
    .menu-icon {
        font-size: 55px;
        margin-bottom: 15px;
    }
    .menu-title {
        font-size: 22px;
        font-weight: bold;
        margin-bottom: 8px;
        color: #2c3e50;
    }
    .menu-desc {
        font-size: 14px;
        color: #555;
    }
    a { text-decoration: none; color: inherit; }
    </style>
    """,
    unsafe_allow_html=True
)

# ================== Session State ==================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "welcome"

# ================== Title ==================
st.markdown("<div class='title'>🔐 AccountWorks Portal</div>", unsafe_allow_html=True)

# ================== Login Form ==================
if not st.session_state.logged_in:
    st.subheader("🔑 Please login")

    with st.form("login_form", clear_on_submit=True):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        user = auth.check_login(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.user = user
            st.session_state.page = "welcome"
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

# ================== After Login ==================
else:
    user = st.session_state.user

    # ----------- Welcome Page -----------
    if st.session_state.page == "welcome":
        st.markdown(
            f"""
            <div class="welcome-card">
                <h1>👋 ยินดีต้อนรับ</h1>
                <h2>{user['Username']}</h2>
                <p style="font-size:18px;">Role ของคุณคือ <b>{user['Role']}</b></p>
            </div>
            """,
            unsafe_allow_html=True
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
                st.session_state.page = "welcome"
                st.rerun()

    # ----------- Main Menu -----------
    elif st.session_state.page == "main":
        st.subheader("📌 Main Menu")

        # ✅ Responsive menu การ์ด
        menu_html = """
            <div class="menu-grid">
                <div onclick="window.parent.streamlitSend('leave_form')" class="menu-card">
                    <div class="menu-icon">🏖</div>
                    <div class="menu-title">ลางาน</div>
                    <div class="menu-desc">ยื่นคำขอลา ตรวจสอบวันลาคงเหลือ</div>
                </div>
                <div onclick="window.parent.streamlitSend('messenger')" class="menu-card">
                    <div class="menu-icon">📦</div>
                    <div class="menu-title">จองคิวแมสเซ็นเจอร์</div>
                    <div class="menu-desc">จองแมสเพื่อส่งเอกสารและพัสดุ</div>
                </div>
        """

        # ✅ ถ้า Role เป็น Admin → เพิ่มเมนู "จัดการผู้ใช้"
        if user["Role"].lower() == "admin":
            menu_html += """
                <div onclick="window.parent.streamlitSend('user_mgmt')" class="menu-card">
                    <div class="menu-icon">⚙️</div>
                    <div class="menu-title">จัดการผู้ใช้</div>
                    <div class="menu-desc">เพิ่ม/ลบ/แก้ไข ผู้ใช้งานในระบบ</div>
                </div>
            """

        menu_html += "</div>"  # ปิด grid

        st.markdown(menu_html, unsafe_allow_html=True)

        st.divider()
        colA, colB = st.columns([1,1])
        with colA:
            if st.button("⬅️ กลับไปหน้า Welcome"):
                st.session_state.page = "welcome"
                st.rerun()
        with colB:
            if st.button("🚪 Logout"):
                st.session_state.logged_in = False
                st.session_state.user = None
                st.session_state.page = "welcome"
                st.rerun()

    # ----------- Leave Form -----------
    elif st.session_state.page == "leave_form":
        st.subheader("🏖 แบบฟอร์มการลา")

        leave_type = st.selectbox("ประเภทการลา", ["ลากิจ", "ลาป่วย", "ลาพักร้อน"])
        start_date = st.date_input("วันที่เริ่มลา", datetime.date.today())
        end_date = st.date_input("วันที่สิ้นสุด")
        reason = st.text_area("เหตุผลการลา")

        if st.button("✅ ส่งคำขอลา"):
            leave_gsheet.submit_leave(
                st.session_state.user["Username"],
                leave_type, start_date, end_date, reason
            )
            st.success("📌 ส่งคำขอลาเรียบร้อยแล้ว (รอหัวหน้าอนุมัติ)")
            st.session_state.page = "main"
            st.rerun()

        if st.button("⬅️ กลับเมนูหลัก"):
            st.session_state.page = "main"
            st.rerun()

    # ----------- User Management (เฉพาะ Admin) -----------
    elif st.session_state.page == "user_mgmt":
        st.subheader("⚙️ จัดการผู้ใช้ (Admin Only)")
        st.info("⏳ หน้านี้เอาไว้เพิ่ม/ลบผู้ใช้ (จะเชื่อม Google Sheet ภายหลัง)")
        if st.button("⬅️ กลับเมนูหลัก"):
            st.session_state.page = "main"
            st.rerun()
