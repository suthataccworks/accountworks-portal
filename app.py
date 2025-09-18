import streamlit as st
from modules import auth_gsheet as auth

st.set_page_config(page_title="AccountWorks Portal", page_icon="🔐", layout="centered")

# ================== Custom CSS ==================
st.markdown(
    """
    <style>
    body {
        background-color: #f5f7fa;
    }
    .welcome-card {
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
        padding: 40px;
        border-radius: 20px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .menu-container {
        display: flex;
        justify-content: center;
        gap: 30px;
        flex-wrap: wrap;
        margin-top: 30px;
    }
    .menu-card {
        background: white;
        border-radius: 15px;
        padding: 30px;
        width: 220px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        transition: all 0.25s ease-in-out;
        cursor: pointer;
    }
    .menu-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.2);
    }
    .menu-icon {
        font-size: 50px;
        margin-bottom: 15px;
    }
    .menu-title {
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 8px;
        color: #333;
    }
    .menu-desc {
        font-size: 14px;
        color: #666;
    }
    .action-btn {
        display: inline-block;
        padding: 10px 20px;
        border-radius: 8px;
        margin: 10px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.2s;
        border: none;
    }
    .logout-btn {
        background: #ff4b5c;
        color: white;
    }
    .logout-btn:hover {
        background: #e84150;
    }
    .back-btn {
        background: #3498db;
        color: white;
    }
    .back-btn:hover {
        background: #2980b9;
    }
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
st.markdown("<h1 style='text-align:center;'>🔐 AccountWorks Portal</h1>", unsafe_allow_html=True)

# ================== Login Form ==================
if not st.session_state.logged_in:
    st.subheader("🔑 Please login")

    with st.form("login_form"):
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
    role = user["Role"].lower()

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

        st.markdown("<div style='text-align:center; margin-top:20px;'>", unsafe_allow_html=True)
        if st.button("➡️ เข้าสู่เมนูหลัก"):
            st.session_state.page = "main"
            st.rerun()
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.page = "welcome"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ----------- Main Menu -----------
    elif st.session_state.page == "main":
        st.subheader("📌 Main Menu")

        st.markdown('<div class="menu-container">', unsafe_allow_html=True)

        # ลางาน
        st.markdown(
            """
            <div class="menu-card" onclick="window.location.reload();">
                <div class="menu-icon">🏖</div>
                <div class="menu-title">ลางาน</div>
                <div class="menu-desc">ยื่นคำขอลา และตรวจสอบวันลาคงเหลือ</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # จองแมสเซ็นเจอร์
        st.markdown(
            """
            <div class="menu-card" onclick="window.location.reload();">
                <div class="menu-icon">📦</div>
                <div class="menu-title">จองคิวแมสเซ็นเจอร์</div>
                <div class="menu-desc">จองแมสเพื่อส่งเอกสารและพัสดุ</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('</div>', unsafe_allow_html=True)

        # ปุ่มด้านล่าง
        st.markdown("<div style='text-align:center; margin-top:30px;'>", unsafe_allow_html=True)
        if st.button("⬅️ กลับไปหน้า Welcome"):
            st.session_state.page = "welcome"
            st.rerun()
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.page = "welcome"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
