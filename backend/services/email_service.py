import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3002")


def _smtp_configured() -> bool:
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


def _send_email(to: str, subject: str, html: str) -> bool:
    if not _smtp_configured():
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM or SMTP_USER
        msg["To"] = to
        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM or SMTP_USER, to, msg.as_string())
        return True
    except Exception as e:
        print(f"[email] SMTP error: {e}")
        return False


def send_verification_email(email: str, token: str) -> None:
    link = f"{FRONTEND_URL}/verify-email?token={token}"

    if not _smtp_configured():
        print(f"[email] DEV MODE — verification link for {email}:")
        print(f"[email] {link}")
        return

    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:32px">
      <h2 style="color:#1a1a2e">FiltreLAB — E-posta Doğrulama</h2>
      <p>Hesabınızı doğrulamak için aşağıdaki butona tıklayın:</p>
      <a href="{link}"
         style="display:inline-block;margin:16px 0;padding:12px 24px;
                background:#3b82f6;color:#fff;border-radius:8px;
                text-decoration:none;font-weight:600">
        E-postamı Doğrula
      </a>
      <p style="color:#888;font-size:13px">
        Bu bağlantı 24 saat geçerlidir. Eğer bu isteği siz yapmadıysanız görmezden gelin.
      </p>
    </div>
    """
    if not _send_email(email, "FiltreLAB — E-posta Doğrulama", html):
        print(f"[email] SMTP failed — verification link for {email}: {link}")


def send_password_reset_email(email: str, token: str) -> None:
    link = f"{FRONTEND_URL}/reset-password?token={token}"

    if not _smtp_configured():
        print(f"[RESET LINK] {link}")
        return

    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:32px">
      <h2 style="color:#1a1a2e">FiltreLAB — Şifre Sıfırlama</h2>
      <p>Şifrenizi sıfırlamak için aşağıdaki butona tıklayın:</p>
      <a href="{link}"
         style="display:inline-block;margin:16px 0;padding:12px 24px;
                background:#ef4444;color:#fff;border-radius:8px;
                text-decoration:none;font-weight:600">
        Şifremi Sıfırla
      </a>
      <p style="color:#888;font-size:13px">
        Bu bağlantı 30 dakika geçerlidir ve yalnızca bir kez kullanılabilir.
        Eğer bu isteği siz yapmadıysanız görmezden gelin.
      </p>
    </div>
    """
    if not _send_email(email, "FiltreLAB — Şifre Sıfırlama", html):
        print(f"[RESET LINK] {link}")
