import streamlit as st
from modules import auth_gsheet as auth

st.set_page_config(page_title="AccountWorks Portal", page_icon="🔐")

st.title("🔐 AccountWorks Portal")

# Debug: ช่วยตรวจสอบว่า module โหลด function มาจริง
st.write("DEBUG (auth functions):", dir(auth))

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

if not st.session_state.logged_in:
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = auth.check_login(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.user = user
            st.success(f"Welcome {user['Username']} (Role: {user['Role']})")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")
else:
    user = st.session_state.user
    st.success(f"✅ Logged in as {user['Username']} ({user['Role']})")

    # ถ้า role เป็น Admin → แสดง Admin Panel
    if user["Role"].lower() == "admin":
        st.subheader("👩‍💻 Admin Panel")
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password")
        new_role = st.selectbox("Role", ["Admin", "User", "Staff"])

        if st.button("Add User"):
            if new_user and new_pass:
                auth.add_user(new_user, new_pass, new_role)
                st.success(f"✅ Added {new_user}")
                st.rerun()

        del_user = st.text_input("Delete Username")
        if st.button("Delete User"):
            if auth.delete_user(del_user):
                st.success(f"🗑 Deleted {del_user}")
                st.rerun()
            else:
                st.warning("⚠️ User not found")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()
