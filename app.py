import streamlit as st
import pandas as pd
from modules import tax_system, messenger_sqlite as messenger
from modules import auth_sqlite   # ✅ ใช้ SQLite + bcrypt

# ============ CONFIG ============
st.set_page_config(page_title="AccountWorks Portal", layout="wide")
auth_sqlite.init_db()  # ✅ สร้างตาราง users ถ้ายังไม่มี + migrate role

# ---------------- Check Login ----------------
def check_login(username, password):
    user = auth_sqlite.get_user(username, password)
    if user:
        role = user[3] if len(user) > 3 else "User"
        return True, role
    return False, None

# ---------------- First User Setup ----------------
def first_user_setup():
    st.title("🛠️ สร้างผู้ใช้คนแรก (Admin)")

    new_username = st.text_input("Username (Admin)")
    new_password = st.text_input("Password", type="password")

    if st.button("สร้างผู้ใช้ Admin"):
        if new_username and new_password:
            try:
                auth_sqlite.add_user(new_username, new_password, "Admin")
                st.success(f"✅ สร้างผู้ใช้ {new_username} (Admin) สำเร็จแล้ว")
                st.info("กรุณาเข้าสู่ระบบด้วยบัญชีที่สร้างใหม่")
                st.session_state["first_user_created"] = True
                st.rerun()
            except Exception as e:
                st.error(f"❌ สร้างผู้ใช้ไม่สำเร็จ: {e}")
        else:
            st.warning("⚠️ กรุณากรอกข้อมูลให้ครบ")

# ---------------- Login UI ----------------
def login_ui():
    # ถ้า DB ยังไม่มี user → ให้ไปหน้า first_user_setup
    users = auth_sqlite.get_all_users()
    if not users:
        first_user_setup()
        st.stop()

    st.title("🔐 AccountWorks Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("เข้าสู่ระบบ"):
        ok, role = check_login(username, password)
        if ok:
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.session_state["role"] = role
            st.session_state["show_welcome"] = True
            st.rerun()
        else:
            st.error("❌ Username หรือ Password ไม่ถูกต้อง")

# ---------------- Welcome Page ----------------
def welcome_ui():
    st.markdown(
        f"""
        <div style='text-align:center; padding:50px;'>
            <h1>🎉 ยินดีต้อนรับ {st.session_state.get("username","")} 🎉</h1>
            <p>สู่ <b>AccountWorks Portal</b></p>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("➡️ เริ่มใช้งาน"):
        st.session_state["show_welcome"] = False
        st.rerun()

# ---------------- User Management (Admin) ----------------
def manage_users():
    st.subheader("👥 จัดการผู้ใช้ (SQLite + bcrypt)")

    users = auth_sqlite.get_all_users()
    if users:
        df = pd.DataFrame(users, columns=["ID", "Username", "Role"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("ยังไม่มีผู้ใช้ในระบบ")

    # เพิ่มผู้ใช้
    st.markdown("### ➕ เพิ่มผู้ใช้ใหม่")
    with st.form("add_user_form"):
        new_username = st.text_input("Username ใหม่")
        new_password = st.text_input("Password", type="password")
        new_role = st.selectbox("Role", ["Admin", "Staff", "User"])
        submitted = st.form_submit_button("เพิ่มผู้ใช้")
        if submitted:
            try:
                auth_sqlite.add_user(new_username, new_password, new_role)
                st.success(f"✅ เพิ่มผู้ใช้ {new_username} สำเร็จแล้ว")
                st.rerun()
            except Exception as e:
                st.error(f"เพิ่มผู้ใช้ไม่สำเร็จ: {e}")

    # ลบผู้ใช้
    st.markdown("### ❌ ลบผู้ใช้")
    usernames = [u[1] for u in users] if users else []
    user_to_delete = st.selectbox("เลือกผู้ใช้ที่ต้องการลบ", [""] + usernames)
    if st.button("ลบผู้ใช้"):
        if user_to_delete:
            auth_sqlite.delete_user(user_to_delete)
            st.warning(f"🗑️ ลบผู้ใช้ {user_to_delete} เรียบร้อยแล้ว")
            st.rerun()

    # แก้ไขผู้ใช้
    st.markdown("### ✏️ แก้ไขผู้ใช้")
    user_to_edit = st.selectbox("เลือกผู้ใช้ที่ต้องการแก้ไข", [""] + usernames, key="edit_user")
    if user_to_edit:
        new_password = st.text_input("แก้ไข Password", type="password")
        new_role = st.selectbox("แก้ไข Role", ["Admin","Staff","User"])
        if st.button("บันทึกการแก้ไข"):
            auth_sqlite.update_user(user_to_edit, new_password, new_role)
            st.success(f"✅ อัปเดตข้อมูลของ {user_to_edit} สำเร็จแล้ว")
            st.rerun()

# ---------------- Main App ----------------
def main_app():
    if st.session_state.get("show_welcome", False):
        welcome_ui()
        return

    st.sidebar.title("📌 เมนูหลัก")
    role = st.session_state.get("role", "User")

    if role == "Admin":
        menu = ["📑 ระบบดาวน์โหลดใบเสร็จภาษี", "🚚 จองคิวแมสเซ็นเจอร์", "⚙️ จัดการผู้ใช้", "🚪 ออกจากระบบ"]
    elif role == "Staff":
        menu = ["📑 ระบบดาวน์โหลดใบเสร็จภาษี", "🚪 ออกจากระบบ"]
    else:
        menu = ["🚚 จองคิวแมสเซ็นเจอร์", "🚪 ออกจากระบบ"]

    choice = st.sidebar.radio("เลือกโปรแกรม", menu)

    if choice == "📑 ระบบดาวน์โหลดใบเสร็จภาษี":
        tax_system.program_tax()
    elif choice == "🚚 จองคิวแมสเซ็นเจอร์":
        messenger.program_messenger_booking(
            username=st.session_state.get("username", "ไม่ระบุ"),
            role=st.session_state.get("role", "User")
        )
    elif choice == "⚙️ จัดการผู้ใช้" and role == "Admin":
        manage_users()
    elif choice == "🚪 ออกจากระบบ":
        st.session_state.clear()
        st.rerun()

# ---------------- Entry Point ----------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login_ui()
    st.stop()
else:
    main_app()
