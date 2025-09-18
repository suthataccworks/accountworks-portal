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

# ========== HELPERS ==========
def _norm_role(role: str) -> str:
    """normalize role string -> admin|user|staff"""
    if not role:
        return "user"
    r = role.strip().lower()
    if r in ("admin", "administrator"):
        return "admin"
    if r in ("user", "employee", "emp"):
        return "user"
    if r in ("staff", "operator"):
        return "staff"
    # อื่นๆ ปัดลงเป็น user
    return "user"

def _to_df(maybe_df_or_list):
    """แปลงผลลัพธ์จาก auth.get_all_users() ให้แสดงผลได้เสมอ"""
    import pandas as pd
    if maybe_df_or_list is None:
        return pd.DataFrame()
    if hasattr(maybe_df_or_list, "columns"):
        return maybe_df_or_list  # already DataFrame
    if isinstance(maybe_df_or_list, list):
        return pd.DataFrame(maybe_df_or_list)
    return pd.DataFrame([maybe_df_or_list])

def _ensure_row_index(leaves):
    """ถ้าไม่มี row_index ให้คำนวณจากลำดับ (1-based สำหรับ Google Sheets)"""
    for i, row in enumerate(leaves, start=2):  # เฮดเดอร์อยู่แถว 1 → ข้อมูลเริ่มที่ 2
        if "row_index" not in row or row["row_index"] in (None, "", 0):
            row["row_index"] = i
    return leaves

def _guard_dates(start_date: datetime.date, end_date: datetime.date) -> tuple[bool, str]:
    if not isinstance(start_date, datetime.date) or not isinstance(end_date, datetime.date):
        return False, "รูปแบบวันที่ไม่ถูกต้อง"
    if end_date < start_date:
        return False, "วันที่สิ้นสุด ต้องไม่ก่อน วันที่เริ่ม"
    return True, ""

# ----------- LOGIN -----------
def login_page():
    st.title("🔐 AccountWorks Portal")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("👤 Username")
        password = st.text_input("🔑 Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        try:
            user = auth.check_login(username, password)
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดระหว่างตรวจสอบผู้ใช้: {e}")
            return

        if user:
            # make sure necessary keys exist
            user.setdefault("Username", username)
            user["Role"] = _norm_role(user.get("Role", "user"))

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

    if _norm_role(st.session_state.user.get("Role")) == "admin":
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

    if _norm_role(st.session_state.user.get("Role")) != "admin":
        st.error("จำกัดสิทธิ์สำหรับผู้ดูแลระบบเท่านั้น")
        if st.button("⬅️ กลับเมนูหลัก"):
            st.session_state.page = "main"; st.rerun()
        return

    try:
        users_df = _to_df(auth.get_all_users(mask_password=True))
    except Exception as e:
        st.error(f"อ่านรายการผู้ใช้ไม่ได้: {e}")
        users_df = _to_df([])

    st.dataframe(users_df, use_container_width=True)

    st.markdown("### ➕ เพิ่มผู้ใช้ใหม่")
    with st.form("add_user_form", clear_on_submit=True):
        new_user = st.text_input("Username (ใหม่)")
        new_pass = st.text_input("Password (ใหม่)", type="password")
        new_role = st.selectbox("Role", ["Admin", "User", "Staff"])
        submitted_add = st.form_submit_button("✅ เพิ่มผู้ใช้")
    if submitted_add:
        try:
            ok, msg = auth.add_user(new_user, new_pass, new_role)
            st.success(msg) if ok else st.error(msg)
            st.rerun()
        except Exception as e:
            st.error(f"เพิ่มผู้ใช้ล้มเหลว: {e}")

    st.markdown("### 📝 อัปเดตผู้ใช้")
    with st.form("update_user_form", clear_on_submit=True):
        target_user = st.text_input("เลือก Username ที่ต้องการแก้ไข")
        upd_pass = st.text_input("รหัสผ่านใหม่ (เว้นว่างถ้าไม่เปลี่ยน)", type="password")
        upd_role = st.selectbox("Role ใหม่", ["Admin", "User", "Staff"])
        submitted_upd = st.form_submit_button("💾 บันทึกการแก้ไข")
    if submitted_upd:
        try:
            ok, msg = auth.update_user(target_user, upd_pass, upd_role)
            st.success(msg) if ok else st.error(msg)
            st.rerun()
        except Exception as e:
            st.error(f"อัปเดตผู้ใช้ล้มเหลว: {e}")

    st.markdown("### ❌ ลบผู้ใช้")
    with st.form("delete_user_form", clear_on_submit=True):
        del_user = st.text_input("Username ที่ต้องการลบ")
        submitted_del = st.form_submit_button("🗑 ลบผู้ใช้")
    if submitted_del:
        try:
            ok, msg = auth.delete_user(del_user)
            st.success(msg) if ok else st.error(msg)
            st.rerun()
        except Exception as e:
            st.error(f"ลบผู้ใช้ล้มเหลว: {e}")

    if st.button("⬅️ กลับเมนูหลัก"):
        st.session_state.page = "main"; st.rerun()

# ----------- LEAVE FORM -----------
def leave_form():
    st.subheader("🏖 แบบฟอร์มการลา")

    # ค่าเริ่มต้นที่ปลอดภัยเสมอ
    today = datetime.date.today()
    col1, col2 = st.columns(2)
    with col1:
        leave_type = st.selectbox("ประเภทการลา", ["ลากิจ", "ลาป่วย", "ลาพักร้อน"], key="leave_type")
        start_date = st.date_input("วันที่เริ่มลา", today, key="start_date")
    with col2:
        end_date = st.date_input("วันที่สิ้นสุด", today, key="end_date")
        reason = st.text_area("เหตุผลการลา", key="reason")

    # ตรวจสอบวันที่
    ok_date, msg_date = _guard_dates(start_date, end_date)
    if not ok_date:
        st.warning(msg_date)

    if st.button("✅ ส่งคำขอลา", key="submit_leave", disabled=not ok_date):
        try:
            ok, msg = leave_gsheet.submit_leave(
                st.session_state.user["Username"], leave_type, start_date, end_date, reason
            )
            st.success(msg) if ok else st.error(msg)
            st.rerun()
        except Exception as e:
            st.error(f"ส่งคำขอลาไม่สำเร็จ: {e}")

    st.divider()
    st.subheader("📋 รายการคำขอลา (แสดงเฉพาะที่ยังไม่ Approved)")

    try:
        leaves = leave_gsheet.get_all_leaves()  # ต้องคืน list[dict]
        if not isinstance(leaves, list):
            leaves = []
    except Exception as e:
        st.error(f"อ่าน Google Sheet ไม่ได้: {e}")
        st.stop()

    leaves = _ensure_row_index(leaves)

    for idx, leave in enumerate(leaves, start=1):
        status = leave.get("Status", "").strip()
        if status == "Approved":
            continue

        is_admin = _norm_role(st.session_state.user.get("Role")) == "admin"
        is_owner = leave.get("Username") == st.session_state.user.get("Username")

        # คนที่ไม่ใช่ admin เห็นเฉพาะของตัวเอง
        if not is_admin and not is_owner:
            continue

        header = f"{leave.get('Username','?')} | {leave.get('LeaveType','?')} | {leave.get('StartDate','?')} → {leave.get('EndDate','?')} [{status or '-'}]"
        with st.expander(header):
            st.write(f"📝 เหตุผล: {leave.get('Reason','-')}")

            # เจ้าของคำขอ (Pending) → แก้ไข/ยกเลิกได้
            if (not is_admin) and is_owner and status == "Pending":
                new_type = st.selectbox(
                    "แก้ไขประเภทลา",
                    ["ลากิจ", "ลาป่วย", "ลาพักร้อน"],
                    index=["ลากิจ","ลาป่วย","ลาพักร้อน"].index(leave.get("LeaveType","ลากิจ")),
                    key=f"type_{idx}"
                )
                def _parse_date(s, fallback=today):
                    try:
                        return datetime.date.fromisoformat(str(s))
                    except Exception:
                        return fallback

                new_start = st.date_input(
                    "แก้ไขวันที่เริ่ม",
                    _parse_date(leave.get("StartDate"), today),
                    key=f"start_{idx}"
                )
                new_end = st.date_input(
                    "แก้ไขวันที่สิ้นสุด",
                    _parse_date(leave.get("EndDate"), today),
                    key=f"end_{idx}"
                )
                new_reason = st.text_area("แก้ไขเหตุผล", leave.get("Reason",""), key=f"reason_{idx}")

                ok_date2, msg_date2 = _guard_dates(new_start, new_end)
                if not ok_date2:
                    st.warning(msg_date2)

                cols_act = st.columns(2)
                if cols_act[0].button("💾 บันทึกการแก้ไข", key=f"update_{idx}", disabled=not ok_date2):
                    try:
                        ok, msg = leave_gsheet.update_leave_request(
                            leave["row_index"], new_type, new_start, new_end, new_reason
                        )
                        st.success(msg) if ok else st.error(msg); st.rerun()
                    except Exception as e:
                        st.error(f"อัปเดตคำขอไม่สำเร็จ: {e}")

                if cols_act[1].button("❌ ยกเลิกการลา", key=f"cancel_{idx}"):
                    try:
                        ok, msg = leave_gsheet.cancel_leave_request(leave["row_index"])
                        st.success(msg) if ok else st.error(msg); st.rerun()
                    except Exception as e:
                        st.error(f"ยกเลิกคำขอไม่สำเร็จ: {e}")

            # Admin → อนุมัติ/ปฏิเสธ (เฉพาะ Pending)
            if is_admin and status == "Pending":
                colA, colB = st.columns(2)
                if colA.button("✅ อนุมัติ", key=f"approve_{idx}"):
                    try:
                        ok, msg = leave_gsheet.update_leave_status(leave["row_index"], "Approved")
                        st.success(msg) if ok else st.error(msg); st.rerun()
                    except Exception as e:
                        st.error(f"อนุมัติไม่สำเร็จ: {e}")
                if colB.button("❌ ไม่อนุมัติ", key=f"reject_{idx}"):
                    try:
                        ok, msg = leave_gsheet.update_leave_status(leave["row_index"], "Rejected")
                        st.warning(msg) if ok else st.error(msg); st.rerun()
                    except Exception as e:
                        st.error(f"ปฏิเสธไม่สำเร็จ: {e}")

    st.divider()
    if st.button("⬅️ กลับเมนูหลัก", key="back_main"):
        st.session_state.page = "main"; st.rerun()

# ----------- ROUTER -----------
if not st.session_state.logged_in:
    login_page()
else:
    page = st.session_state.page
    if page == "main":
        main_menu()
    elif page == "user_mgmt":
        user_management()
    elif page == "leave_form":
        leave_form()
