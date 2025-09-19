# app.py — AccountWorks Portal (Lovable UI) + Google Sheets backend
# ใช้ modules: modules/auth_gsheet.py, modules/leave_gsheet.py

import streamlit as st
import datetime
import traceback
from modules import auth_gsheet as auth
from modules import leave_gsheet

st.set_page_config(page_title="AccountWorks Portal", page_icon="🔐", layout="wide")

# ========================= CSS (Lovable-like) =========================
st.markdown("""
<style>
:root{
  --radius:16px; --card:#fff; --muted:#f6f7fb; --border:#eef0f5; --text:#111827; --text-muted:#6b7280;
  --blue:#3b82f6; --green:#22c55e; --violet:#8b5cf6; --amber:#f59e0b; --red:#ef4444;
}
*{font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,'Noto Sans Thai','Sarabun',Arial;}
.block-container{padding-top:.8rem;}
a.muted{color:#64748b;text-decoration:none;}

.topbar{position:sticky;top:0;z-index:99;backdrop-filter:saturate(180%) blur(8px);
  background:rgba(255,255,255,.8);border-bottom:1px solid var(--border);padding:.6rem 0;}
.icon{width:32px;height:32px;border-radius:12px;background:#f1f5f9;display:grid;place-items:center;}
.pill{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:999px;
  font-size:.78rem;border:1px solid var(--border);background:#f8fafc;}
.pill.admin{background:#fee2e2;border-color:#fecaca;color:#991b1b;font-weight:600;}
.pill.staff{background:#e0f2fe;border-color:#bae6fd;color:#075985;}
.pill.user{background:#e5e7eb;border-color:#e5e7eb;color:#374151;}

.card{background:#fff;border:1px solid var(--border);border-radius:16px;padding:18px;box-shadow:0 10px 24px rgba(17,24,39,.06);}
.card-hover:hover{box-shadow:0 16px 30px rgba(17,24,39,.10);transform:translateY(-1px);transition:.2s;}
.kpi-title{font-size:.9rem;color:var(--text-muted);margin-bottom:.2rem;}
.kpi-value{font-size:1.6rem;font-weight:800;}
.kpi-sub{font-size:.75rem;color:var(--text-muted);}
.grid{display:grid;gap:16px;}
.grid.cols-3{grid-template-columns:repeat(3,minmax(0,1fr));}
@media(max-width:900px){.grid.cols-3{grid-template-columns:1fr;}}

.progress{height:8px;background:var(--muted);border-radius:999px;overflow:hidden;}
.progress>span{display:block;height:100%;}

.badge{display:inline-flex;align-items:center;padding:4px 10px;border-radius:999px;font-size:.75rem;border:1px solid var(--border);background:#f8fafc;}
.badge.ok{background:#ecfdf5;border-color:#bbf7d0;color:#15803d}
.badge.wait{background:#fff7ed;border-color:#fed7aa;color:#b45309}
.badge.off{background:#f1f5f9;color:#64748b}

.login-card .hint{border:1px solid var(--border);border-radius:12px;padding:12px;background:#f8fafc;color:#334155;font-size:.9rem;}
.login-title{font-size:2rem;font-weight:800;text-align:center;margin-top:16px}
.login-sub{color:var(--text-muted);text-align:center;margin-bottom:12px}

.table-head{font-size:.8rem;color:var(--text-muted);padding:4px 6px 10px;}
.row{display:grid;grid-template-columns:1.6fr 1.8fr 1fr 1.2fr 1fr .8fr;gap:12px;align-items:center;padding:12px;background:#fff;border:1px solid var(--border);border-radius:12px;margin-bottom:10px;}
</style>
""", unsafe_allow_html=True)

# ========================= SESSION =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"

# ========================= HELPERS =========================
def _norm_role(role: str) -> str:
    if not role: return "user"
    r = str(role).strip().lower()
    if r in ("admin","administrator"): return "admin"
    if r in ("staff","operator"): return "staff"
    return "user"

def _to_df(maybe_df_or_list):
    import pandas as pd
    if maybe_df_or_list is None: return pd.DataFrame()
    if hasattr(maybe_df_or_list, "columns"): return maybe_df_or_list
    if isinstance(maybe_df_or_list, list): return pd.DataFrame(maybe_df_or_list)
    return pd.DataFrame([maybe_df_or_list])

def _ensure_row_index(leaves):
    for i, row in enumerate(leaves, start=2):  # header = row 1
        if "row_index" not in row or row["row_index"] in (None,"",0):
            row["row_index"] = i
    return leaves

def _guard_dates(start_date: datetime.date, end_date: datetime.date) -> tuple[bool, str]:
    if not isinstance(start_date, datetime.date) or not isinstance(end_date, datetime.date):
        return False, "รูปแบบวันที่ไม่ถูกต้อง"
    if end_date < start_date:
        return False, "วันที่สิ้นสุด ต้องไม่ก่อน วันที่เริ่ม"
    return True, ""

def _role_pill_class(role: str) -> str:
    r = _norm_role(role)
    return f"pill {r}"

def _topbar():
    u = st.session_state.user or {}
    email = u.get("Username","")
    role  = _norm_role(u.get("Role","user"))
    name  = u.get("DisplayName", email)
    st.markdown(f"""
    <div class='topbar'>
      <div class='block-container' style='padding:0'>
        <div style='display:flex;align-items:center;justify-content:space-between;'>
          <div style='display:flex;gap:12px;align-items:center;'>
            <div style="width:36px;height:36px;border-radius:12px;background:#e8f0ff;display:grid;place-items:center;">🏢</div>
            <div>
              <div style="font-weight:800;">AccountWorks</div>
              <div class="meta">Company Management System</div>
            </div>
          </div>
          <div style='display:flex;gap:12px;align-items:center;'>
            <span class='{_role_pill_class(role)}'>{role.title()}</span>
            <div class='icon'>🔔</div><div class='icon'>⚙️</div>
            <div class='icon'>👤</div>
            <div class="meta" style="min-width:160px;text-align:right">
              <div style="font-weight:600">{name}</div>
              <div>{email}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ========================= LOGIN PAGE =========================
def login_page():
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    cols = st.columns([1,1,1])
    with cols[1]:
        st.markdown("<div class='card login-card'>", unsafe_allow_html=True)
        st.markdown("<div class='login-title'>AccountWorks</div>", unsafe_allow_html=True)
        st.markdown("<div class='login-sub'>เข้าสู่ระบบด้วยบัญชีของคุณ</div>", unsafe_allow_html=True)

        # 🧪 Debug self-test
        with st.expander("🧪 ตรวจสุขภาพการเชื่อมต่อ (ชั่วคราว)"):
            if st.button("Run auth.self_test()"):
                res = auth.self_test()
                st.json(res)

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("👤 Username", value=st.session_state.user.get("Username","") if st.session_state.user else "")
            password = st.text_input("🔑 Password", type="password")
            c1, c2 = st.columns([1,1])
            with c1: st.checkbox("จดจำฉัน", value=True)
            with c2: st.markdown("<div style='text-align:right'><a class='muted' href='#'>ลืมรหัสผ่าน?</a></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("เข้าสู่ระบบ", use_container_width=True)

        if submitted:
            try:
                user = auth.check_login(username, password)
            except Exception as e:
                st.error("เกิดข้อผิดพลาดระหว่างตรวจสอบผู้ใช้ (ดูรายละเอียดด้านล่าง)")
                st.exception(e)
                st.code("".join(traceback.format_exc()), language="text")
                return

            # ✅ อนุญาตเฉพาะผู้ใช้ที่ยืนยันจาก Google Sheet เท่านั้น
            if user and user.get("_verified") is True and user.get("_source") == "gsheet":
                sheet_uname = str(user.get("Username","")).strip().lower()
                if sheet_uname == str(username).strip().lower():
                    user["Role"] = _norm_role(user.get("Role", "user"))
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    st.session_state.page = "main"
                    st.rerun()

            st.error("❌ Username หรือ Password ไม่ถูกต้อง")

        st.markdown("</div>", unsafe_allow_html=True)

# ========================= MAIN MENU =========================
def main_menu():
    _topbar()
    st.header("📌 เมนูหลัก")

    cols = st.columns(3)
    if cols[0].button("🏖 ลางาน", use_container_width=True):
        st.session_state.page = "leave_form"; st.rerun()

    if cols[1].button("📦 จองคิวแมสเซ็นเจอร์", use_container_width=True):
        st.info("⏳ อยู่ระหว่างพัฒนา…")

    if _norm_role(st.session_state.user.get("Role")) == "admin":
        if cols[2].button("⚙️ จัดการผู้ใช้", use_container_width=True):
            st.session_state.page = "user_mgmt"; st.rerun()
    else:
        cols[2].markdown("<div class='card' style='text-align:center;color:#9ca3af'>สำหรับผู้ดูแลระบบ</div>", unsafe_allow_html=True)

    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.page = "login"
        st.rerun()

# ========================= USER MANAGEMENT =========================
def user_management():
    _topbar()
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

    st.markdown("<div class='table-head'>ชื่อ | อีเมล/ชื่อผู้ใช้ | แผนก | บทบาท | สถานะ | การจัดการ</div>", unsafe_allow_html=True)
    if users_df.empty:
        st.markdown("<div class='card'>ไม่มีข้อมูลผู้ใช้</div>", unsafe_allow_html=True)
    else:
        cols_map = {c.lower(): c for c in users_df.columns}
        for _, r in users_df.iterrows():
            name = r.get(cols_map.get("displayname","DisplayName"), r.get(cols_map.get("name","Name"), r.get(cols_map.get("username","Username"), "-")))
            uname = r.get(cols_map.get("username","Username"), "-")
            email = r.get(cols_map.get("email","Email"), "-")
            dept  = r.get(cols_map.get("department","Department"), r.get("Dept","-"))
            role  = _norm_role(r.get(cols_map.get("role","Role"), "user"))
            status = r.get(cols_map.get("status","Status"), "ใช้งาน")

            st.markdown("<div class='row'>", unsafe_allow_html=True)
            st.write(name)
            st.write(f"📧 {email or '-'} / 👤 {uname}")
            st.write(dept or "-")
            st.markdown(f"<span class='{_role_pill_class(role)}'>{role.title()}</span>", unsafe_allow_html=True)
            st.markdown(f"<span class='{'badge ok' if str(status).strip() in ('ใช้งาน','Active') else 'badge off'}'>{status}</span>", unsafe_allow_html=True)
            c = st.columns([1,1])
            with c[0]:
                st.button("✏️", key=f"edit_{uname}")
            with c[1]:
                st.button("🗑️", key=f"del_{uname}")
            st.markdown("</div>", unsafe_allow_html=True)

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

# ========================= LEAVE FORM =========================
def leave_form():
    _topbar()
    st.subheader("🏖 แบบฟอร์มการลา")

    today = datetime.date.today()
    col1, col2 = st.columns(2)
    with col1:
        leave_type = st.selectbox("ประเภทการลา", ["ลากิจ", "ลาป่วย", "ลาพักร้อน"], key="leave_type")
        start_date = st.date_input("วันที่เริ่มลา", today, key="start_date")
    with col2:
        end_date = st.date_input("วันที่สิ้นสุด", today, key="end_date")
        reason = st.text_area("เหตุผลการลา", key="reason")

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
        return

    leaves = _ensure_row_index(leaves)

    for idx, leave in enumerate(leaves, start=1):
        status = (leave.get("Status","") or "").strip()
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
                types = ["ลากิจ","ลาป่วย","ลาพักร้อน"]
                def _parse_date(s, fallback=today):
                    try: return datetime.date.fromisoformat(str(s))
                    except Exception: return fallback

                new_type = st.selectbox("แก้ไขประเภทลา", types, index=types.index(leave.get("LeaveType","ลากิจ")), key=f"type_{idx}")
                new_start = st.date_input("แก้ไขวันที่เริ่ม", _parse_date(leave.get("StartDate"), today), key=f"start_{idx}")
                new_end   = st.date_input("แก้ไขวันที่สิ้นสุด", _parse_date(leave.get("EndDate"), today), key=f"end_{idx}")
                new_reason= st.text_area("แก้ไขเหตุผล", leave.get("Reason",""), key=f"reason_{idx}")

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

# ========================= ROUTER =========================
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
    else:
        st.session_state.page = "main"; st.rerun()
