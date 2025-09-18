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
        st.session_state.page = "leave_form"; st.rerun()

    if cols[1].button("📦 จองคิวแมสเซ็นเจอร์", use_container_width=True):
        st.info("⏳ กำลังพัฒนา...")

    if st.session_state.user["Role"].lower() == "admin":
        if cols[2].button("⚙️ จัดการผู้ใช้", use_container_width=True):
            st.session_state.page = "user_mgmt"; st.rerun()

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
        st.success(msg) if ok else st.error(msg); st.rerun()

    st.markdown("### 📝 อัปเดตผู้ใช้")
    target_user = st.text_input("เลือก Username ที่ต้องการแก้ไข")
    upd_pass = st.text_input("รหัสผ่านใหม่", type="password")
    upd_role = st.selectbox("Role ใหม่", ["Admin", "User", "Staff"], key="upd_role")
    if st.button("💾 บันทึกการแก้ไข"):
        ok, msg = auth.update_user(target_user, upd_pass, upd_role)
        st.success(msg) if ok else st.error(msg); st.rerun()

    st.markdown("### ❌ ลบผู้ใช้")
    del_user = st.text_input("Username ที่ต้องการลบ")
    if st.button("🗑 ลบผู้ใช้"):
        ok, msg = auth.delete_user(del_user)
        st.success(msg) if ok else st.error(msg); st.rerun()

    if st.button("⬅️ กลับเมนูหลัก"):
        st.session_state.page = "main"; st.rerun()

# ----------- LEAVE FORM -----------
def leave_form():
    st.subheader("🏖 แบบฟอร์มการลา")

    leave_type = st.selectbox("ประเภทการลา", ["ลากิจ", "ลาป่วย", "ลาพักร้อน"], key="leave_type")
    start_date = st.date_input("วันที่เริ่มลา", datetime.date.today(), key="start_date")
    end_date = st.date_input("วันที่สิ้นสุด", key="end_date")
    reason = st.text_area("เหตุผลการลา", key="reason")

    if st.button("✅ ส่งคำขอลา", key="submit_leave"):
        ok, msg = leave_gsheet.submit_leave(
            st.session_state.user["Username"], leave_type, start_date, end_date, reason
        )
        st.success(msg) if ok else st.error(msg)
        st.rerun()

    st.divider()
    st.subheader("📋 รายการคำขอลา (แสดงเฉพาะที่ยังไม่ Approved)")

    try:
        leaves = leave_gsheet.get_all_leaves()  # คืนค่าพร้อม row_index
    except Exception as e:
        st.error(f"อ่าน Google Sheet ไม่ได้: {e}")
        st.stop()

    for idx, leave in enumerate(leaves, start=1):
        # ซ่อนที่ Approved
        if leave.get("Status") == "Approved":
            continue
        # User ที่ไม่ใช่ admin เห็นเฉพาะของตัวเอง
        if st.session_state.user["Role"].lower() != "admin" and leave["Username"] != st.session_state.user["Username"]:
            continue

        header = f"{leave['Username']} | {leave['LeaveType']} | {leave['StartDate']} → {leave['EndDate']} [{leave['Status']}]"
        with st.expander(header):
            st.write(f"📝 เหตุผล: {leave.get('Reason','-')}")

            # ผู้ใช้เจ้าของคำขอ (Pending) → แก้ไข/ยกเลิกได้
            if (st.session_state.user["Role"].lower() != "admin"
                and leave["Username"] == st.session_state.user["Username"]
                and leave.get("Status") == "Pending"):
                new_type = st.selectbox(
                    "แก้ไขประเภทลา", ["ลากิจ", "ลาป่วย", "ลาพักร้อน"],
                    index=["ลากิจ","ลาป่วย","ลาพักร้อน"].index(leave["LeaveType"]),
                    key=f"type_{idx}"
                )
                new_start = st.date_input(
                    "แก้ไขวันที่เริ่ม",
                    datetime.date.fromisoformat(leave["StartDate"]),
                    key=f"start_{idx}"
                )
                new_end = st.date_input(
                    "แก้ไขวันที่สิ้นสุด",
                    datetime.date.fromisoformat(leave["EndDate"]),
                    key=f"end_{idx}"
                )
                new_reason = st.text_area("แก้ไขเหตุผล", leave.get("Reason",""), key=f"reason_{idx}")

                if st.button("💾 บันทึกการแก้ไข", key=f"update_{idx}"):
                    ok, msg = leave_gsheet.update_leave_request(
                        leave["row_index"], new_type, new_start, new_end, new_reason
                    )
                    st.success(msg) if ok else st.error(msg); st.rerun()

                if st.button("❌ ยกเลิกการลา", key=f"cancel_{idx}"):
                    ok, msg = leave_gsheet.cancel_leave_request(leave["row_index"])
                    st.success(msg) if ok else st.error(msg); st.rerun()

            # Admin → อนุมัติ/ปฏิเสธ (เฉพาะ Pending)
            if st.session_state.user["Role"].lower() == "admin" and leave.get("Status") == "Pending":
                colA, colB = st.columns(2)
                if colA.button("✅ อนุมัติ", key=f"approve_{idx}"):
                    ok, msg = leave_gsheet.update_leave_status(leave["row_index"], "Approved")
                    st.success(msg) if ok else st.error(msg); st.rerun()
                if colB.button("❌ ไม่อนุมัติ", key=f"reject_{idx}"):
                    ok, msg = leave_gsheet.update_leave_status(leave["row_index"], "Rejected")
                    st.warning(msg) if ok else st.error(msg); st.rerun()

    st.divider()
    if st.button("⬅️ กลับเมนูหลัก", key="back_main"):
        st.session_state.page = "main"; st.rerun()

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
