import streamlit as st
import datetime
from modules import auth_gsheet as auth
from modules import leave_gsheet

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
    st.subheader("🏖 แบบฟอร์มการลา")

    leave_type = st.selectbox("ประเภทการลา", ["ลากิจ", "ลาป่วย", "ลาพักร้อน"])
    start_date = st.date_input("วันที่เริ่มลา", datetime.date.today())
    end_date = st.date_input("วันที่สิ้นสุด")
    reason = st.text_area("เหตุผลการลา")

    if st.button("✅ ส่งคำขอลา"):
        ok, msg = leave_gsheet.submit_leave(
            st.session_state.user["Username"],
            leave_type,
            start_date,
            end_date,
            reason
        )
        st.success(msg) if ok else st.error(msg)
        st.rerun()

    st.divider()
    st.markdown("### 📋 รายการคำขอลา")

    leaves = leave_gsheet.get_all_leaves()
    if st.session_state.user["Role"].lower() != "admin":
        leaves = [l for l in leaves if l["Username"] == st.session_state.user["Username"]]

    for lv in leaves:
        with st.expander(f'{lv["Username"]} | {lv["LeaveType"]} | {lv["StartDate"]} → {lv["EndDate"]} [{lv["Status"]}]'):
            st.write(f"📝 เหตุผล: {lv['Reason']}")

            # User: edit / cancel
            if st.session_state.user["Role"].lower() != "admin" and lv["Status"] == "Pending":
                new_type = st.selectbox("แก้ประเภทลา", ["ลากิจ", "ลาป่วย", "ลาพักร้อน"], index=["ลากิจ", "ลาป่วย", "ลาพักร้อน"].index(lv["LeaveType"]), key=f"type_{lv['StartDate']}")
                new_start = st.date_input("แก้วันที่เริ่ม", datetime.date.fromisoformat(lv["StartDate"]), key=f"start_{lv['StartDate']}")
                new_end = st.date_input("แก้วันที่สิ้นสุด", datetime.date.fromisoformat(lv["EndDate"]), key=f"end_{lv['StartDate']}")
                new_reason = st.text_area("แก้เหตุผล", lv["Reason"], key=f"reason_{lv['StartDate']}")

                if st.button("💾 บันทึกการแก้ไข", key=f"update_{lv['StartDate']}"):
                    ok, msg = leave_gsheet.update_leave_request(
                        lv["Username"], lv["StartDate"], new_type, new_start, new_end, new_reason
                    )
                    st.success(msg) if ok else st.error(msg)
                    st.rerun()

                if st.button("🗑 ยกเลิกคำขอ", key=f"cancel_{lv['StartDate']}"):
                    ok, msg = leave_gsheet.cancel_leave_request(lv["Username"], lv["StartDate"])
                    st.warning(msg)
                    st.rerun()

            # Admin: approve / reject
            if st.session_state.user["Role"].lower() == "admin" and lv["Status"] == "Pending":
                if st.button("✅ อนุมัติ", key=f"approve_{lv['StartDate']}_{lv['Username']}"):
                    leave_gsheet.update_leave_status(lv["Username"], lv["StartDate"], "Approved")
                    st.success("อนุมัติแล้ว")
                    st.rerun()
                if st.button("❌ ปฏิเสธ", key=f"reject_{lv['StartDate']}_{lv['Username']}"):
                    leave_gsheet.update_leave_status(lv["Username"], lv["StartDate"], "Rejected")
                    st.error("ปฏิเสธแล้ว")
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
