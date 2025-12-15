import os
import smtplib
import ssl
from email.message import EmailMessage

SMTP_DEFAULTS = {
    "host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
    "port": int(os.environ.get("SMTP_PORT", "465") or 465),
    "user": os.environ.get("SMTP_USER") or os.environ.get("EMAIL_USER") or "fureverhome2103@gmail.com",
    "password": os.environ.get("SMTP_PASS") or os.environ.get("EMAIL_PASS") or "blwb zcyp ogrl wudz",
    "sender": os.environ.get("SMTP_FROM") or "fureverhome2103@gmail.com",
}


def send_otp_email(to_email: str, code: str):
    """
    Send OTP to the specified email using SMTP env vars.
    """
    host = os.environ.get("SMTP_HOST") or SMTP_DEFAULTS["host"]
    port = int(os.environ.get("SMTP_PORT") or SMTP_DEFAULTS["port"] or 0)
    user = os.environ.get("SMTP_USER") or os.environ.get("EMAIL_USER") or SMTP_DEFAULTS["user"]
    password = os.environ.get("SMTP_PASS") or os.environ.get("EMAIL_PASS") or SMTP_DEFAULTS["password"]
    sender = os.environ.get("SMTP_FROM") or SMTP_DEFAULTS["sender"] or user

    if not all([host, port, user, password, sender]):
        raise RuntimeError("Missing SMTP configuration. Set SMTP_HOST/PORT/USER/PASS/FROM env vars.")

    msg = EmailMessage()
    msg["Subject"] = "Your FurEver Home OTP Code"
    msg["From"] = sender
    msg["To"] = to_email
    msg.set_content(
        f"Use this code to reset your FurEver Home password: {code}\n\n"
        f"If you did not request this, you can ignore this email."
    )

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(host, port, context=context, timeout=30) as server:
        server.login(user, password)
        server.send_message(msg)
