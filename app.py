import streamlit as st
import modules.auth_gsheet as auth

st.title("🔐 Google Sheet Login")

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
            st.experimental_rerun()
        else:
            st.error("❌ Invalid username or password")
else:
    st.success(f"✅ Logged in as {st.session_state.user['Username']} ({st.session_state.user['Role']})")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.experimental_rerun()
