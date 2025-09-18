import streamlit as st

# ✅ import แบบนี้แทน
from modules import auth_gsheet as auth  

st.title("🔐 AccountWorks Portal")

# Debug ช่วยเช็กว่ามี check_login จริงไหม
st.write("DEBUG:", dir(auth))

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
            st.rerun()   # ✅ ใช้ st.rerun() แทน experimental
        else:
            st.error("❌ Invalid username or password")
else:
    user = st.session_state.user
    st.success(f"✅ Logged in as {user['Username']} ({user['Role']})")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()
