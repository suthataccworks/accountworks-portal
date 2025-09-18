import streamlit as st
from modules import auth_gsheet as auth

st.set_page_config(page_title="AccountWorks Portal", page_icon="🔐", layout="centered")

st.title("🔐 AccountWorks Portal")

# ================== Session State ==================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

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
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

# ================== Welcome Page ==================
else:
    user = st.session_state.user

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            color: white;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        ">
            <h1 style="margin-bottom: 10px;">👋 ยินดีต้อนรับ</h1>
            <h2 style="margin-top: 0;">{user['Username']}</h2>
            <p style="font-size:18px;">Role ของคุณคือ <b>{user['Role']}</b></p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()
