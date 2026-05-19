import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from html import escape

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "FiltreLAB")
SMTP_REPLY_TO = os.getenv("SMTP_REPLY_TO", SMTP_FROM or SMTP_USER)
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() != "false"
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3002")


def _smtp_configured() -> bool:
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD)


def _sender() -> str:
    sender_email = SMTP_FROM or SMTP_USER
    return formataddr((SMTP_FROM_NAME, sender_email)) if SMTP_FROM_NAME else sender_email


def _send_email(to: str, subject: str, text: str, html: str) -> bool:
    if not _smtp_configured():
        return False
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = _sender()
        msg["To"] = to
        if SMTP_REPLY_TO:
            msg["Reply-To"] = SMTP_REPLY_TO
        msg["Message-ID"] = make_msgid(domain=(SMTP_FROM or SMTP_USER).split("@")[-1] if "@" in (SMTP_FROM or SMTP_USER) else None)
        msg["X-Auto-Response-Suppress"] = "All"
        msg.set_content(text, subtype="plain", charset="utf-8")
        msg.add_alternative(html, subtype="html", charset="utf-8")

        smtp_cls = smtplib.SMTP_SSL if SMTP_USE_SSL else smtplib.SMTP
        with smtp_cls(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.ehlo()
            if SMTP_USE_TLS and not SMTP_USE_SSL:
                server.starttls()
                server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg, from_addr=SMTP_FROM or SMTP_USER, to_addrs=[to])
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

    text = f"""Merhaba,

FiltreLAB hesabınızı doğrulamak için bu bağlantıyı açın:
{link}

Bu bağlantı 24 saat geçerlidir. Bu isteği siz yapmadıysanız bu e-postayı yok sayabilirsiniz.

FiltreLAB
"""
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
    if not _send_email(email, "FiltreLAB e-posta doğrulama", text, html):
        print(f"[email] SMTP failed — verification link for {email}: {link}")


def send_password_reset_email(email: str, token: str) -> None:
    link = f"{FRONTEND_URL}/reset-password?token={token}"

    if not _smtp_configured():
        print(f"[RESET LINK] {link}")
        return

    safe_link = escape(link, quote=True)
    text = f"""Merhaba,

FiltreLAB hesabınız için şifre sıfırlama talebi aldık.

Yeni şifre belirlemek için bu bağlantıyı açın:
{link}

Bu bağlantı 30 dakika geçerlidir ve yalnızca bir kez kullanılabilir.
Bu isteği siz yapmadıysanız bu e-postayı yok sayabilirsiniz.

FiltreLAB
"""
    html = f"""
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:560px;margin:0 auto;padding:32px;color:#191847;line-height:1.55">
      <h2 style="margin:0 0 16px;color:#191847;font-size:24px">FiltreLAB şifre sıfırlama</h2>
      <p style="margin:0 0 16px;color:#374151">FiltreLAB hesabınız için şifre sıfırlama talebi aldık.</p>
      <p style="margin:0 0 20px;color:#374151">Yeni şifre belirlemek için aşağıdaki bağlantıyı kullanabilirsiniz:</p>
      <a href="{safe_link}"
         style="display:inline-block;margin:8px 0 20px;padding:12px 22px;
                background:#191847;color:#ffffff;border-radius:10px;
                text-decoration:none;font-weight:700">
        Yeni şifre belirle
      </a>
      <p style="margin:0 0 12px;color:#6b7280;font-size:13px">
        Bu bağlantı 30 dakika geçerlidir ve yalnızca bir kez kullanılabilir.
      </p>
      <p style="margin:0;color:#6b7280;font-size:13px">Bu isteği siz yapmadıysanız bu e-postayı yok sayabilirsiniz.</p>
      <hr style="border:0;border-top:1px solid #e5e7eb;margin:24px 0" />
      <p style="margin:0;color:#9ca3af;font-size:12px">Buton çalışmazsa bu bağlantıyı tarayıcınıza yapıştırın:<br />
        <span style="word-break:break-all">{safe_link}</span>
      </p>
    </div>
    """
    if not _send_email(email, "FiltreLAB şifre sıfırlama bağlantınız", text, html):
        print(f"[RESET LINK] {link}")
