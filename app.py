import streamlit as st
import datetime
from modules import auth_gsheet as auth
from modules import leave_gsheet


# ========== CONFIG ==========
st.set_page_config(page_title="AccountWorks Portal", page_icon="🔐", layout="wide")

# ========== SESSION ==========
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"


# ----------- LOGIN -----------
def login_page():
    st.title("🔐 AccountWorks Portal")
    with st.form("login_form", clear_on_submit=True):
        username = st.text_input("👤 Username")
        password = st.text_input("🔑 Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        user = auth.check_login(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.user = user
            st.session_state.page = "main"
            st.rerun()
        else:
            st.error("❌ Username หรือ Password ไม่ถูกต้อง")


# ----------- MAIN MENU -----------
def main_menu():
    st.header("📌 Main Menu")

    cols = st.columns(3)
    if cols[0].button("🏖 ลางาน", use_container_width=True):
        st.session_state.page = "leave_form"
        st.rerun()

    if cols[1].button("📦 จองคิวแมสเซ็นเจอร์", use_container_width=True):
        st.info("⏳ กำลังพัฒนา...")

    if st.session_state.user["Role"].lower() == "admin":
        if cols[2].button("⚙️ จัดการผู้ใช้", use_container_width=True):
            st.session_state.page = "user_mgmt"
            st.rerun()

    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.page = "login"
        st.rerun()


# ----------- USER MANAGEMENT -----------
def user_management():
    st.subheader("⚙️ จัดการผู้ใช้ (Admin Only)")

    users = auth.get_all_users(mask_password=True)
    st.table(users)

    st.markdown("### ➕ เพิ่มผู้ใช้ใหม่")
    new_user = st.text_input("Username (ใหม่)")
    new_pass = st.text_input("Password (ใหม่)", type="password")
    new_role = st.selectbox("Role", ["Admin", "User", "Staff"], key="add_role")
    if st.button("✅ เพิ่มผู้ใช้"):
        ok, msg = auth.add_user(new_user, new_pass, new_role)
        st.success(msg) if ok else st.error(msg)
        st.rerun()

    st.markdown("### 📝 อัปเดตผู้ใช้")
    target_user = st.text_input("เลือก Username ที่ต้องการแก้ไข")
    upd_pass = st.text_input("รหัสผ่านใหม่", type="password")
    upd_role = st.selectbox("Role ใหม่", ["Admin", "User", "Staff"], key="upd_role")
    if st.button("💾 บันทึกการแก้ไข"):
        ok, msg = auth.update_user(target_user, upd_pass, upd_role)
        st.success(msg) if ok else st.error(msg)
        st.rerun()

    st.markdown("### ❌ ลบผู้ใช้")
    del_user = st.text_input("Username ที่ต้องการลบ")
    if st.button("🗑 ลบผู้ใช้"):
        ok, msg = auth.delete_user(del_user)
        st.success(msg) if ok else st.error(msg)
        st.rerun()

    if st.button("⬅️ กลับเมนูหลัก"):
        st.session_state.page = "main"
        st.rerun()


# ----------- LEAVE FORM -----------
def leave_form():
    st.subheader("📄 รายการคำขอลา")

    user = st.session_state.user
    leaves = leave_gsheet.get_user_leaves(user["Username"], user["Role"])

    # ✅ แสดงเฉพาะที่ยังไม่ Approved
    leaves = [l for l in leaves if l["Status"] != "Approved"]

    if not leaves:
        st.info("✅ ไม่มีคำขอที่รอการดำเนินการ")
        if st.button("⬅️ กลับเมนูหลัก"):
            st.session_state.page = "main"
            st.rerun()
        return

    for leave in leaves:
        with st.expander(f"{leave['Username']} | {leave['LeaveType']} | {leave['StartDate']} → {leave['EndDate']} [{leave['Status']}]"):
            st.json(leave)

            # ถ้า User = เจ้าของคำขอ และยัง Pending → แก้ไขได้
            if user["Role"].lower() != "admin" and leave["Username"] == user["Username"] and leave["Status"] == "Pending":
                new_type = st.selectbox("ประเภทการลา", ["ลากิจ", "ลาป่วย", "ลาพักร้อน"], index=["ลากิจ","ลาป่วย","ลาพักร้อน"].index(leave["LeaveType"]))
                new_start = st.date_input("วันที่เริ่มลา", datetime.datetime.strptime(leave["StartDate"], "%Y-%m-%d").date())
                new_end = st.date_input("วันที่สิ้นสุด", datetime.datetime.strptime(leave["EndDate"], "%Y-%m-%d").date())
                new_reason = st.text_area("เหตุผลการลา", leave["Reason"])

                if st.button("💾 บันทึกการแก้ไข", key=f"edit_{leave['StartDate']}"):
                    ok, msg = leave_gsheet.update_leave_request(
                        leave["Username"], leave["StartDate"], new_type, new_start, new_end, new_reason
                    )
                    st.success(msg) if ok else st.error(msg)
                    st.rerun()

                if st.button("🗑 ยกเลิกการลา", key=f"cancel_{leave['StartDate']}"):
                    ok, msg = leave_gsheet.delete_leave_request(leave["Username"], leave["StartDate"])
                    st.success(msg) if ok else st.error(msg)
                    st.rerun()

            # ถ้า Admin → อนุมัติ/ปฏิเสธได้
            if user["Role"].lower() == "admin" and leave["Status"] == "Pending":
                if st.button("✅ อนุมัติ", key=f"approve_{leave['StartDate']}"):
                    ok, msg = leave_gsheet.update_leave_status(leave["Username"], leave["StartDate"], "Approved")
                    st.success(msg) if ok else st.error(msg)
                    st.rerun()
                if st.button("❌ ปฏิเสธ", key=f"reject_{leave['StartDate']}"):
                    ok, msg = leave_gsheet.update_leave_status(leave["Username"], leave["StartDate"], "Rejected")
                    st.warning(msg)
                    st.rerun()

    if st.button("⬅️ กลับเมนูหลัก"):
        st.session_state.page = "main"
        st.rerun()


    if st.button("⬅️ กลับเมนูหลัก"):
        st.session_state.page = "main"
        st.rerun()


# ----------- ROUTER -----------
if not st.session_state.logged_in:
    login_page()
else:
    if st.session_state.page == "main":
        main_menu()
    elif st.session_state.page == "user_mgmt":
        user_management()
    elif st.session_state.page == "leave_form":
        leave_form()

