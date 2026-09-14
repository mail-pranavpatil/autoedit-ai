from __future__ import annotations

import logging
import secrets
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Tuple

import httpx

from autoedit.config import get_settings

logger = logging.getLogger("autoedit.email")


def generate_verification_code() -> str:
    """Generate a random 6-digit numeric verification code."""
    return "".join(secrets.choice("0123456789") for _ in range(6))


def send_verification_email(to_email: str, code: str, user_name: str | None = None) -> Tuple[bool, str]:
    """
    Send verification email using Resend, standard SMTP, or local fallback.
    Returns (success: bool, status_message: str).
    """
    settings = get_settings()
    greeting = f"Hi {user_name}," if user_name else "Hi Creator,"
    subject = f"{code} is your Eren verification code"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0d1117; color: #ffffff; padding: 24px; }}
        .container {{ max-width: 480px; margin: 0 auto; background: #161b22; border-radius: 16px; border: 1px solid #30363d; padding: 32px; text-align: center; }}
        .title {{ font-size: 24px; font-weight: 700; color: #ffffff; margin-bottom: 8px; }}
        .subtitle {{ font-size: 14px; color: #8b949e; margin-bottom: 24px; }}
        .code-box {{ font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #6366f1; background: #1e1e2e; border: 1px solid #4f46e5; border-radius: 12px; padding: 16px; margin: 24px 0; }}
        .footer {{ font-size: 12px; color: #6e7681; margin-top: 24px; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="title">Eren — AI Video Creator</div>
        <div class="subtitle">{greeting} Welcome to Eren! Please verify your email to continue.</div>
        <div class="code-box">{code}</div>
        <div class="subtitle">This code expires in 15 minutes. If you did not request this, please ignore this email.</div>
        <div class="footer">&copy; 2026 Eren AI. All rights reserved.</div>
      </div>
    </body>
    </html>
    """

    # 1. Resend API
    if settings.resend_api_key:
        try:
            headers = {
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "from": settings.smtp_from,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            }
            with httpx.Client(timeout=15) as client:
                res = client.post("https://api.resend.com/emails", json=payload, headers=headers)
                if res.status_code in (200, 201):
                    logger.info("Sent verification email via Resend to %s", to_email)
                    return True, "Email sent via Resend"
                logger.error("Resend API error: %s", res.text)
        except Exception as e:
            logger.exception("Failed to send email via Resend: %s", e)

    # 2. SMTP
    if settings.smtp_host and settings.smtp_user and settings.smtp_password:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.smtp_from
            msg["To"] = to_email
            msg.attach(MIMEText(f"Your Eren verification code is: {code}\nExpires in 15 minutes.", "plain"))
            msg.attach(MIMEText(html_content, "html"))

            if settings.smtp_port == 465:
                server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=15)
            else:
                server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15)
                if settings.smtp_use_tls:
                    server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from, [to_email], msg.as_string())
            server.quit()
            logger.info("Sent verification email via SMTP to %s", to_email)
            return True, "Email sent via SMTP"
        except Exception as e:
            logger.exception("Failed to send email via SMTP: %s", e)

    # 3. Development / Server fallback
    logger.info(
        "\n"
        "==============================================================\n"
        " [EREN EMAIL VERIFICATION CODE]\n"
        " To: %s\n"
        " Code: %s (Expires in 15 mins)\n"
        " (Configure SMTP or RESEND_API_KEY in .env for inbox delivery)\n"
        "==============================================================",
        to_email,
        code,
    )
    return True, f"Verification code generated (check logs if SMTP unconfigured): {code}"
