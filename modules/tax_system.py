import streamlit as st
import pandas as pd
import datetime
import os, time, traceback, requests, smtplib, csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import urllib3
import plotly.graph_objects as go

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===== CONFIG =====
DOWNLOAD_ROOT = r"C:\EfilingDownloads"
LOG_FILE = os.path.join(DOWNLOAD_ROOT, "email_log.csv")
REQUEST_TIMEOUT = 30


# ---------------- Logging ----------------
def write_log(company, to_email, subject, status, error="", attachments=None,
              tax_type="", tax_month="", tax_year=""):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            company, to_email, subject, status, error,
            ";".join(attachments or []),
            tax_type, tax_month, tax_year
        ])


# ---------------- Email ----------------
def send_email(sender_email, sender_password, to_email, subject, body_html, attachments=None,
               company="", tax_type="", tax_month="", tax_year=""):
    attachments = attachments or []
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    for file_path in attachments:
        if not os.path.exists(file_path):
            continue
        with open(file_path, "rb") as f:
            part = MIMEBase("application", "pdf")
            part.set_payload(f.read())
        encoders.encode_base64(part)

        filename = os.path.basename(file_path)
        part.add_header("Content-Disposition", "attachment",
                        filename=("utf-8", "", filename))
        msg.attach(part)

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=60)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        write_log(company, to_email, subject, "สำเร็จ", "", attachments, tax_type, tax_month, tax_year)
        return True
    except Exception as e:
        write_log(company, to_email, subject, "ล้มเหลว", str(e), attachments, tax_type, tax_month, tax_year)
        return False


# ---------------- PDF Downloader ----------------
def download_pdf_from_popup(driver, wait, clickable, save_path):
    clickable.click()
    wait.until(lambda d: len(d.window_handles) > 1)
    driver.switch_to.window(driver.window_handles[-1])
    pdf_url = driver.current_url
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

    resp = requests.get(pdf_url, timeout=REQUEST_TIMEOUT, verify=False)
    ctype = (resp.headers.get("Content-Type") or "").lower()
    if not ctype.startswith("application/pdf"):
        raise ValueError(f"URL ไม่ใช่ PDF (Content-Type={ctype})")
    with open(save_path, "wb") as f:
        f.write(resp.content)
    return save_path if os.path.getsize(save_path) > 0 else None


# ---------------- Selenium Flow ----------------
def selenium_download(df, tax_type, tax_year, tax_month):
    results = []
    os.makedirs(DOWNLOAD_ROOT, exist_ok=True)

    for _, row in df.iterrows():
        company = str(row.get("ชื่อบริษัท", "Unknown")).strip()
        username = str(row.get("รหัส Efiling", "")).strip()
        password = str(row.get("Password", "")).strip()

        folder_path = os.path.join(DOWNLOAD_ROOT, company, tax_type, f"{tax_month}_{tax_year}")
        os.makedirs(folder_path, exist_ok=True)

        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        prefs = {"download.default_directory": folder_path}
        chrome_options.add_experimental_option("prefs", prefs)

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        wait = WebDriverWait(driver, 20)

        form_path, receipt_path = None, None
        try:
            driver.get("https://efiling.rd.go.th/rd-efiling-web/login")
            wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username)
            driver.find_element(By.ID, "passwordField").send_keys(password)
            driver.find_element(By.XPATH, '//button[contains(text(),"เข้าสู่ระบบ")]').click()
            time.sleep(2)

            # ไปหน้าตรวจสอบผล
            wait.until(EC.element_to_be_clickable((By.XPATH, '//a[contains(text(),"ตรวจสอบผลการยื่นแบบ")]'))).click()
            wait.until(EC.element_to_be_clickable((By.XPATH, '//span[text()="ค้นหาขั้นสูง"]'))).click()

            def choose_dropdown(idx, value):
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f'(//span[@class="ng-arrow-wrapper"])[{idx}]'))).click()
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f'//span[contains(text(),"{value}")]'))).click()

            choose_dropdown(1, tax_type)
            choose_dropdown(2, tax_year)
            choose_dropdown(3, tax_month)
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//button[contains(@class,"button-box-search")]'))).click()
            time.sleep(2)

            # เมนูดาวน์โหลด
            ellipsis_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//i[contains(@class,"fa-ellipsis-v")]')))
            ellipsis_btn.click()
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//a[contains(text(),"พิมพ์ภาพแบบ/ภาพใบเสร็จ")]'))).click()

            buttons = wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, '//button[contains(@class,"button-box-clean-dowload")]')
            ))

            try:
                form_path = download_pdf_from_popup(driver, wait, buttons[0],
                                                    os.path.join(folder_path,
                                                                 f"{company}_{tax_type}_{tax_month}_{tax_year}_แบบ.pdf"))
            except Exception: traceback.print_exc()

            try:
                receipt_path = download_pdf_from_popup(driver, wait, buttons[1],
                                                       os.path.join(folder_path,
                                                                    f"{company}_{tax_type}_{tax_month}_{tax_year}_ใบเสร็จ.pdf"))
            except Exception: traceback.print_exc()

            results.append((company, "สำเร็จ", form_path, receipt_path))
        except Exception as e:
            traceback.print_exc()
            results.append((company, "ล้มเหลว", None, None))
        finally:
            driver.quit()

    return results


# ---------------- Table Renderer ----------------
def make_file_link(path):
    if not path or path == "-" or path is None:
        return "-"
    filename = os.path.basename(path)
    return f"<a href='file:///{path}' target='_blank' style='color:#2980b9;text-decoration:none;'>{filename}</a>"


def render_result_table(df):
    df["ไฟล์แบบ"] = df["ไฟล์แบบ"].apply(lambda x: make_file_link(x) if x not in [None, "-"] else "-")
    df["ไฟล์ใบเสร็จ"] = df["ไฟล์ใบเสร็จ"].apply(lambda x: make_file_link(x) if x not in [None, "-"] else "-")

    table_html = df.to_html(escape=False, index=False, classes="styled-table")

    st.markdown("""
        <style>
        .styled-table {
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 15px;
            width: 100%;
            box-shadow: 0 2px 12px rgba(0,0,0,0.1);
        }
        .styled-table th {
            background-color: #2575fc;
            color: #fff;
            text-align: center;
            padding: 10px;
            white-space: nowrap;
        }
        .styled-table td {
            border-bottom: 1px solid #ddd;
            padding: 8px;
            white-space: nowrap;
        }
        .styled-table td:first-child {
            text-align: left; /* ✅ บริษัทชิดซ้าย */
            padding-left: 12px;
            font-weight: 500;
        }
        .styled-table td:not(:first-child) {
            text-align: center;
        }
        .styled-table tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .styled-table tr:hover {
            background-color: #f1f1f1;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(table_html, unsafe_allow_html=True)


# ---------------- Main App ----------------
def program_tax():
    st.header("📑 AccountWorks Tax Automation Portal")

    uploaded_file = st.file_uploader("แนบไฟล์ Excel (รายชื่อบริษัท)", type=["xlsx"])
    df = None
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file, dtype={'รหัส Efiling': str, 'Password': str}).fillna("")
            st.success("✅ โหลดข้อมูล Excel สำเร็จ")
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"อ่านไฟล์ไม่สำเร็จ: {e}")

    col1, col2, col3 = st.columns(3)
    with col1:
        tax_types = st.multiselect("📌 เลือกประเภทภาษี",
                                   ["ภ.ง.ด.1", "ภ.ง.ด.3", "ภ.ง.ด.53", "ภ.พ.30"],
                                   default=["ภ.ง.ด.1"])
    with col2:
        months = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
        tax_month = st.selectbox("🗓️ เดือนภาษี", months)
    with col3:
        years = [str(y) for y in range(2565, datetime.datetime.now().year + 544)]
        tax_year = st.selectbox("📅 ปีภาษี", years, index=len(years) - 1)

    st.subheader("📧 ตั้งค่าอีเมล")
    col1, col2 = st.columns(2)
    with col1: sender_email = st.text_input("Gmail ผู้ส่ง")
    with col2: sender_password = st.text_input("App Password", type="password")
    send_mail = st.checkbox("ส่งอีเมลอัตโนมัติ", value=True)

    mail_subject = st.text_input("หัวเรื่องอีเมล",
                                 "เอกสารภาษี {tax_type} เดือน {tax_month}/{tax_year} - {company}")
    mail_body = st.text_area("ข้อความอีเมล (รองรับ placeholder)",
                             "<p>เรียน {company},</p><p>ไฟล์แนบคือเอกสารภาษี {tax_type} เดือน {tax_month}/{tax_year}</p>")

    if st.button("🚀 เริ่มดาวน์โหลด + ส่งอีเมล"):
        if df is None:
            st.error("กรุณาอัพโหลด Excel ก่อน")
        elif not tax_types:
            st.error("กรุณาเลือกอย่างน้อย 1 ประเภทภาษี")
        else:
            progress = st.progress(0)
            status_placeholder = st.empty()
            report_data = []

            total = len(df) * len(tax_types)
            count = 0

            for _, row in df.iterrows():
                company = str(row.get("ชื่อบริษัท", "Unknown")).strip()
                to_email = str(row.get("Email", "")).strip()
                attachments_all = []

                for tax_type in tax_types:
                    count += 1
                    status_placeholder.info(f"⏳ {company} - {tax_type} ({count}/{total})")

                    try:
                        results = selenium_download(pd.DataFrame([row]), tax_type, tax_year, tax_month)
                        comp, result, form_path, receipt_path = results[0]

                        if form_path: attachments_all.append(form_path)
                        if receipt_path: attachments_all.append(receipt_path)

                        status_badge = f"<span style='color:white;background:#2ecc71;padding:4px 10px;border-radius:12px;'>สำเร็จ</span>" if result == "สำเร็จ" else f"<span style='color:white;background:#e74c3c;padding:4px 10px;border-radius:12px;'>ล้มเหลว</span>"

                        report_data.append({
                            "บริษัท": comp,
                            "ประเภทภาษี": tax_type,
                            "สถานะ": status_badge,
                            "ไฟล์แบบ": form_path or "-",
                            "ไฟล์ใบเสร็จ": receipt_path or "-"
                        })
                    except Exception as e:
                        traceback.print_exc()
                        report_data.append({
                            "บริษัท": company,
                            "ประเภทภาษี": tax_type,
                            "สถานะ": f"<span style='color:white;background:#e74c3c;padding:4px 10px;border-radius:12px;'>ล้มเหลว ({e})</span>",
                            "ไฟล์แบบ": "-",
                            "ไฟล์ใบเสร็จ": "-"
                        })

                    progress.progress(count / total)

                if send_mail and attachments_all:
                    subj = mail_subject.format(company=company, tax_type="รวม",
                                               tax_month=tax_month, tax_year=tax_year)
                    body = mail_body.format(company=company, tax_type="รวม",
                                            tax_month=tax_month, tax_year=tax_year)
                    send_email(sender_email, sender_password, to_email, subj, body, attachments_all,
                               company, "รวม", tax_month, tax_year)

            st.success("✅ เสร็จสิ้น")

            st.subheader("📊 สรุปผลการทำงาน")
            result_df = pd.DataFrame(report_data)
            render_result_table(result_df)

            if not result_df.empty:
                success_count = (result_df["สถานะ"].str.contains("สำเร็จ")).sum()
                fail_count = (result_df["สถานะ"].str.contains("ล้มเหลว")).sum()

                fig = go.Figure(data=[go.Pie(
                    labels=["สำเร็จ", "ล้มเหลว"],
                    values=[success_count, fail_count],
                    marker=dict(colors=["#2ecc71", "#e74c3c"]),
                    hole=0.4
                )])
                fig.update_layout(title="ภาพรวมผลลัพธ์", height=400, showlegend=True)
                st.plotly_chart(fig, use_container_width=True)
