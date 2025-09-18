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

# ================== After Login ==================
else:
    user = st.session_state.user
    role = user["Role"].lower()

    # Welcome Banner (ใช้ทุก role)
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

    # ================== Role-based Dashboard ==================
    if role == "admin":
        st.subheader("👩‍💻 Admin Dashboard")
        st.info("คุณสามารถจัดการผู้ใช้ได้ที่นี่")

        # Add user
        st.markdown("### ➕ Add New User")
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password")
        new_role = st.selectbox("Role", ["Admin", "User", "Staff"])

        if st.button("Add User"):
            if new_user and new_pass:
                auth.add_user(new_user, new_pass, new_role)
                st.success(f"✅ Added {new_user}")
                st.rerun()
            else:
                st.warning("⚠️ Please fill username and password")

        # Delete user
        st.markdown("### 🗑 Delete User")
        del_user = st.text_input("Delete Username")
        if st.button("Delete User"):
            if auth.delete_user(del_user):
                st.success(f"🗑 Deleted {del_user}")
                st.rerun()
            else:
                st.warning("⚠️ User not found")

    elif role == "staff":
        st.subheader("👷 Staff Dashboard")
        st.info("หน้านี้สำหรับพนักงานทั่วไป เช่น ดูสิทธิ์การลา เช็ควันลา ฯลฯ")

    elif role == "user":
        st.subheader("🙋 User Dashboard")
        st.info("หน้านี้สำหรับผู้ใช้งานทั่วไป เช่น ดูข้อมูลส่วนตัว")

    # ================== Logout ==================
    st.divider()
    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()
