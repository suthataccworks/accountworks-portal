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
    /* Welcome Card */
    .welcome-card {
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
        padding: 40px;
        border-radius: 20px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        margin-bottom: 30px;
    }
    /* Menu Grid */
    .menu-grid {
        display: flex;
        justify-content: center;
        gap: 40px;
        flex-wrap: wrap;
        margin-top: 30px;
    }
    .menu-card {
        width: 240px;
        height: 200px;
        border-radius: 20px;
        padding: 25px;
        background: linear-gradient(135deg, #ffffff 0%, #f0f4ff 100%);
        box-shadow: 0 6px 15px rgba(0,0,0,0.1);
        text-align: center;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .menu-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 12px 25px rgba(0,0,0,0.2);
    }
    .menu-icon {
        font-size: 55px;
        margin-bottom: 15px;
    }
    .menu-title {
        font-size: 22px;
        font-weight: bold;
        margin-bottom: 10px;
        color: #2c3e50;
    }
    .menu-desc {
        font-size: 14px;
        color: #555;
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

        col1, col2 = st.columns(2)
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

        st.markdown('<div class="menu-grid">', unsafe_allow_html=True)

        # การ์ด: ลางาน
        st.markdown(
            """
            <div class="menu-card" onclick="window.location.reload();">
                <div class="menu-icon">🏖</div>
                <div class="menu-title">ลางาน</div>
                <div class="menu-desc">ยื่นคำขอลา ตรวจสอบวันลาคงเหลือ</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # การ์ด: จองแมสเซ็นเจอร์
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

        st.divider()
        colA, colB = st.columns(2)
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
