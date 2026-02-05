"""
SMTP 邮件发送模块（适配 Brevo SMTP Relay）
.env:
SENDER_EMAIL=a1afbb001@smtp-brevo.com
SENDER_PASSWORD=<Brevo SMTP Key>
SMTP_SERVER=smtp-relay.brevo.com
SMTP_PORT=587
EMAIL_USE_TLS=True

EMAIL_FROM=<user-facing from email> (optional)
EMAIL_FROM_NAME=<user-facing from name> (optional)
EMAIL_REPLY_TO=<reply-to email> (optional)
"""

import os
import smtplib
from datetime import datetime
from typing import Optional, List, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


def _str2bool(v: Optional[str], default: bool = True) -> bool:
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")


class EmailService:
    def __init__(
        self,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_login: Optional[str] = None,
        smtp_password: Optional[str] = None,
        use_tls: Optional[bool] = None,
        use_ssl: bool = False,
        # 用户看到的 From / Reply-To
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        debug_smtp: bool = False,
    ):
        self.smtp_server = (smtp_server or os.getenv("SMTP_SERVER") or "").strip()
        self.smtp_port = int(smtp_port or os.getenv("SMTP_PORT") or "587")

        self.smtp_login = (smtp_login or os.getenv("SENDER_EMAIL") or "").strip()
        self.smtp_password = (smtp_password or os.getenv("SENDER_PASSWORD") or "").strip()

        env_tls = _str2bool(os.getenv("EMAIL_USE_TLS"), default=True)
        self.use_tls = bool(env_tls if use_tls is None else use_tls)
        self.use_ssl = bool(use_ssl)
        self.debug_smtp = bool(debug_smtp)

        self.from_email = (from_email or os.getenv("EMAIL_FROM") or self.smtp_login).strip()
        self.from_name = (from_name or os.getenv("EMAIL_FROM_NAME") or "Ultra Travel Commander").strip()
        self.reply_to = (reply_to or os.getenv("EMAIL_REPLY_TO") or "").strip() or None

        if not self.smtp_server or not self.smtp_login or not self.smtp_password:
            raise ValueError("邮件配置不完整：需要 SMTP_SERVER / SENDER_EMAIL / SENDER_PASSWORD")

    @classmethod
    def test_connection(
        cls,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_login: Optional[str] = None,
        smtp_password: Optional[str] = None,
        use_tls: Optional[bool] = None,
        debug_smtp: bool = False,
    ) -> Tuple[bool, str]:
        try:
            svc = cls(
                smtp_server=smtp_server,
                smtp_port=smtp_port,
                smtp_login=smtp_login,
                smtp_password=smtp_password,
                use_tls=use_tls,
                debug_smtp=debug_smtp,
            )
            with smtplib.SMTP(svc.smtp_server, svc.smtp_port, timeout=20) as server:
                if svc.debug_smtp:
                    server.set_debuglevel(1)
                if svc.use_tls:
                    server.starttls()
                server.login(svc.smtp_login, svc.smtp_password)
            return True, "✅ SMTP 登录测试成功（Brevo SMTP Relay 连接正常）"
        except smtplib.SMTPAuthenticationError as e:
            return False, f"❌ SMTP 认证失败：请确认使用的是 Brevo 的 SMTP Key。详情: {e}"
        except Exception as e:
            return False, f"❌ SMTP 连接失败: {type(e).__name__}: {e}"

    def send_test_email(self, recipient_email: str) -> Tuple[bool, str]:
        subject = "✅ EmailService 测试邮件 - Ultra Travel Commander (Brevo SMTP)"
        html = f"""
        <html><body style="font-family:Segoe UI,Arial,sans-serif;">
            <h2>✅ 测试邮件发送成功</h2>
            <p>发送时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>SMTP Relay：{self.smtp_server}:{self.smtp_port}</p>
            <p>From：{self.from_name} &lt;{self.from_email}&gt;</p>
            <p>To：{recipient_email}</p>
        </body></html>
        """
        ok = self._send_email(to_email=recipient_email, subject=subject, html_content=html)
        return ok, ("✅ 测试邮件发送成功！" if ok else "❌ 测试邮件发送失败（请看控制台报错）")

    def send_booking_confirmation(self, recipient_email: str, booking_details: dict, payment_result: dict) -> Tuple[bool, str]:
        subject = f"✅ 预订确认 - {booking_details.get('title', '旅行订单')}"
        html = self._generate_booking_html(booking_details, payment_result)
        ok = self._send_email(to_email=recipient_email, subject=subject, html_content=html)
        return ok, ("✅ 预订确认邮件发送成功！" if ok else "❌ 预订确认邮件发送失败（请看控制台报错）")

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[tuple]] = None,  # (filename, bytes, content_type)
    ) -> bool:
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            msg["Subject"] = subject
            if self.reply_to:
                msg["Reply-To"] = self.reply_to

            if text_content:
                msg.attach(MIMEText(text_content, "plain", "utf-8"))
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            if attachments:
                for filename, file_bytes, content_type in attachments:
                    part = MIMEBase(*content_type.split("/", 1)) if content_type and "/" in content_type else MIMEBase("application", "octet-stream")
                    part.set_payload(file_bytes)
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
                    msg.attach(part)

            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=20) as server:
                if self.debug_smtp:
                    server.set_debuglevel(1)
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_login, self.smtp_password)
                server.send_message(msg)

            print(f"✅ 邮件已成功发送至 {to_email}")
            return True
        except Exception as e:
            print(f"❌ 邮件发送失败: {type(e).__name__}: {e}")
            return False

    def _generate_booking_html(self, booking: dict, payment: dict) -> str:
        return f"""
<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:Segoe UI,Arial,sans-serif; line-height:1.6; color:#333;">
<h2>✅ 预订确认</h2>
<p><b>项目：</b>{booking.get('title','N/A')}</p>
<p><b>路线：</b>{booking.get('route','N/A')}</p>
<p><b>时间：</b>{booking.get('start','N/A')} - {booking.get('end','N/A')}</p>
<hr/>
<p><b>金额：</b>${payment.get('amount',0):.2f} {payment.get('currency','USD')}</p>
<p><b>确认码：</b><b>{payment.get('confirmation_code','N/A')}</b></p>
<p style="color:#666;font-size:12px;">此邮件由系统自动发送，请勿直接回复。</p>
</body></html>
"""
