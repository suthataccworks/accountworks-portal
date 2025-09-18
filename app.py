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
    .menu-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        justify-content: center;
    }
    .menu-card {
        flex: 1 1 calc(50% - 20px);
        max-width: 300px;
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
        font-size: 50px;
        margin-bottom: 10px;
    }
    .menu-title {
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 5px;
        color: #2c3e50;
    }
    .menu-desc {
        font-size: 14px;
        color: #555;
    }
    @media (max-width: 768px) {
        .menu-card {
            flex: 1 1 100%;
        }
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

        st.markdown("<div class='menu-grid'>", unsafe_allow_html=True)

        # Leave
        if st.button("🏖 ลางาน", key="leave", use_container_width=True):
            st.session_state.page = "leave_form"
            st.rerun()

        # Messenger
        if st.button("📦 จองคิวแมสเซ็นเจอร์", key="messenger", use_container_width=True):
            st.info("⏳ กำลังพัฒนา...")

        # User Management (Admin only)
        if user["Role"] == "Admin":
            if st.button("⚙️ จัดการผู้ใช้", key="user_mgmt", use_container_width=True):
                st.session_state.page = "user_mgmt"
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

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

    # ----------- User Management (Admin Only) -----------
    elif st.session_state.page == "user_mgmt":
        st.subheader("⚙️ จัดการผู้ใช้ (Admin Only)")

        users = auth.get_all_users()
        st.table(users)

        st.markdown("### ➕ เพิ่มผู้ใช้ใหม่")
        new_user = st.text_input("Username (ใหม่)")
        new_pass = st.text_input("Password (ใหม่)", type="password")
        new_role = st.selectbox("Role", ["Admin", "User", "Staff"])
        if st.button("✅ เพิ่มผู้ใช้"):
            auth.add_user(new_user, new_pass, new_role)
            st.success("เพิ่มผู้ใช้เรียบร้อยแล้ว ✅")
            st.rerun()

        st.markdown("### 📝 อัปเดตผู้ใช้")
        target_user = st.text_input("เลือก Username ที่ต้องการแก้ไข")
        upd_pass = st.text_input("รหัสผ่านใหม่", type="password")
        upd_role = st.selectbox("Role ใหม่", ["Admin", "User", "Staff"], key="upd_role")
        if st.button("💾 บันทึกการแก้ไข"):
            auth.update_user(target_user, upd_pass, upd_role)
            st.success("อัปเดตผู้ใช้เรียบร้อย ✅")
            st.rerun()

        st.markdown("### ❌ ลบผู้ใช้")
        del_user = st.text_input("Username ที่ต้องการลบ")
        if st.button("🗑 ลบผู้ใช้"):
            auth.delete_user(del_user)
            st.warning(f"ลบผู้ใช้ {del_user} เรียบร้อยแล้ว")
            st.rerun()

        st.divider()
        if st.button("⬅️ กลับเมนูหลัก"):
            st.session_state.page = "main"
            st.rerun()
