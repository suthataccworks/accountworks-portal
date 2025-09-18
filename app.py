import streamlit as st
from modules import auth_gsheet as auth

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="AccountWorks Portal", page_icon="🔐")

# แสดงชื่อระบบ
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
            st.success(f"Welcome {user['Username']} (Role: {user['Role']})")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

# ================== Dashboard ==================
else:
    user = st.session_state.user
    st.success(f"✅ Logged in as {user['Username']} ({user['Role']})")

    # แยกการแสดงผลตาม Role
    if user["Role"].lower() == "admin":
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

    elif user["Role"].lower() == "staff":
        st.subheader("👷 Staff Dashboard")
        st.info("หน้านี้สำหรับพนักงานทั่วไป")

    elif user["Role"].lower() == "user":
        st.subheader("🙋 User Dashboard")
        st.info("หน้านี้สำหรับผู้ใช้งานทั่วไป")

    # Logout
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()
