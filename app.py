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
            reason,
        )
        st.success(msg) if ok else st.error(msg)

    st.divider()
    st.markdown("### 📋 รายการคำขอลา")

    # User เห็นเฉพาะตัวเอง, Admin เห็นทั้งหมด
    leaves = leave_gsheet.get_user_leaves(
        st.session_state.user["Username"],
        st.session_state.user["Role"],
    )

    for i, row in enumerate(leaves, start=1):
        with st.expander(
            f"{row['Username']} | {row['LeaveType']} | {row['StartDate']} → {row['EndDate']} | {row['Status']}"
        ):
            st.write(f"📝 เหตุผล: {row['Reason']}")

            # User: ยกเลิกหรือแก้ไขได้ ถ้ายัง Pending และเป็นของตัวเอง
            if (
                st.session_state.user["Role"].lower() == "user"
                and row["Username"] == st.session_state.user["Username"]
                and row["Status"] == "Pending"
            ):
                if st.button(f"✏️ แก้ไขคำขอ #{i}"):
                    new_leave_type = st.selectbox(
                        "ประเภทการลาใหม่", ["ลากิจ", "ลาป่วย", "ลาพักร้อน"], key=f"edit_type_{i}"
                    )
                    new_start = st.date_input("เริ่มลาใหม่", datetime.date.today(), key=f"edit_start_{i}")
                    new_end = st.date_input("สิ้นสุดใหม่", datetime.date.today(), key=f"edit_end_{i}")
                    new_reason = st.text_area("เหตุผลใหม่", key=f"edit_reason_{i}")
                    if st.button("💾 บันทึก", key=f"save_edit_{i}"):
                        ok, msg = leave_gsheet.update_leave_request(
                            row["Username"],
                            row["StartDate"],
                            new_leave_type,
                            new_start,
                            new_end,
                            new_reason,
                        )
                        st.success(msg) if ok else st.error(msg)
                        st.rerun()

                if st.button(f"🗑 ยกเลิกคำขอ #{i}"):
                    ok, msg = leave_gsheet.delete_leave_request(row["Username"], row["StartDate"])
                    st.success(msg) if ok else st.error(msg)
                    st.rerun()

            # Admin: อนุมัติหรือปฏิเสธได้
            if st.session_state.user["Role"].lower() == "admin" and row["Status"] == "Pending":
                col1, col2 = st.columns(2)
                if col1.button(f"✅ อนุมัติ #{i}"):
                    ok, msg = leave_gsheet.update_leave_status(row["Username"], row["StartDate"], "Approved")
                    st.success(msg) if ok else st.error(msg)
                    st.rerun()
                if col2.button(f"❌ ปฏิเสธ #{i}"):
                    ok, msg = leave_gsheet.update_leave_status(row["Username"], row["StartDate"], "Rejected")
                    st.warning(msg) if ok else st.error(msg)
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
