# app/services/email.py
import os
import smtplib
import logging
from email.message import EmailMessage
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound
from ..config import settings

log = logging.getLogger("uvicorn.error")

# /app/app/services -> /app/app/templates
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)

def _render_html(template_name: str, **ctx) -> str | None:
    try:
        tpl = env.get_template(template_name)
        return tpl.render(**ctx)
    except TemplateNotFound:
        log.warning(f"email template '{template_name}' not found at {TEMPLATES_DIR}")
        return None
    except Exception as e:
        log.warning(f"email template error '{template_name}': {e}")
        return None

def _send(msg: EmailMessage) -> None:
    host = settings.SMTP_HOST
    port = int(settings.SMTP_PORT)
    user = (settings.SMTP_USER or "").strip()
    pwd  = (settings.SMTP_PASS or "").strip()

    # MailHog no requiere TLS ni login; si quisieras forzar STARTTLS, poné SMTP_STARTTLS=true en env
    use_starttls = os.getenv("SMTP_STARTTLS", "").lower() in ("1","true","yes")

    if port == 465:
        smtp = smtplib.SMTP_SSL(host, port, timeout=10)
    else:
        smtp = smtplib.SMTP(host, port, timeout=10)
        if use_starttls:
            smtp.starttls()

    if user and pwd:
        smtp.login(user, pwd)

    smtp.send_message(msg)
    smtp.quit()
    log.info("email sent to %s subj=%s", msg["To"], msg["Subject"])

def send_verify_email(to_email: str, to_name: str, token: str) -> None:
    base = (settings.FRONTEND_BASE_URL or "http://localhost:8080").rstrip("/")
    url  = f"{base}/verify-email?token={token}"

    subject = "Verifica tu email"
    text = f"Hola {to_name}, verificá tu email haciendo clic en: {url}"

    html = _render_html("verify_es.html", name=to_name, url=url)
    if html is None:
        # fallback si la plantilla falla o no existe
        html = f"""
        <html><body>
          <p>Hola {to_name},</p>
          <p>Verificá tu email haciendo clic en este enlace:</p>
          <p><a href="{url}">{url}</a></p>
        </body></html>
        """

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.MAIL_FROM
    msg["To"] = to_email
    msg.set_content(text)              # texto plano
    msg.add_alternative(html, subtype="html")  # HTML

    try:
        _send(msg)
    except Exception as e:
        # no rompemos el flujo de la API; queda registro
        log.exception(f"send_verify_email failed for {to_email}: {e}")
