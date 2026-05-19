import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_FROM, EMAIL_TO


def send_report_email(report: str):
    if not SMTP_USER or not SMTP_PASS or not EMAIL_TO:
        print("[email] 邮箱未配置，跳过邮件发送")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    subject = f"技术热点日报 {today}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM or SMTP_USER
    msg["To"] = EMAIL_TO

    # 提取纯文本摘要（去除 Markdown 标记的简版）
    plain = report.replace("#", "").replace("*", "").replace("`", "")[:3000]
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(report, "html", "utf-8"))

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(msg["From"], [EMAIL_TO], msg.as_string())
