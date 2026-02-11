"""
邮件通知器
通过SMTP发送告警邮件
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List
from .base_notifier import BaseNotifier


class EmailNotifier(BaseNotifier):
    """邮件通知器"""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        to_emails: List[str]
    ):
        super().__init__("email")
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails

    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        """发送告警邮件"""
        subject = f"[{alert['severity'].upper()}] {alert['title']}"
        body = self._format_html_email(alert)

        return await self._send_email(subject, body, html=True)

    async def send_resolution(self, alert: Dict[str, Any]) -> bool:
        """发送告警解决邮件"""
        subject = f"[RESOLVED] {alert['title']}"
        body = f"""
        <html>
        <body>
            <h2 style="color: green;">Alert Resolved</h2>
            <p><strong>{alert['title']}</strong></p>
            <p>Resolved at: {alert['resolved_at']}</p>
        </body>
        </html>
        """

        return await self._send_email(subject, body, html=True)

    async def _send_email(self, subject: str, body: str, html: bool = True) -> bool:
        """发送邮件"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = subject

            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            self.logger.info(f"Email sent successfully to {self.to_emails}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            return False

    def _format_html_email(self, alert: Dict[str, Any]) -> str:
        """格式化HTML邮件"""
        severity_colors = {
            'info': '#17a2b8',
            'warning': '#ffc107',
            'critical': '#dc3545'
        }

        color = severity_colors.get(alert.get('severity', 'info'), '#6c757d')

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .alert-box {{
                    border-left: 4px solid {color};
                    padding: 15px;
                    background-color: #f8f9fa;
                    margin: 20px 0;
                }}
                .severity {{
                    color: {color};
                    font-weight: bold;
                    text-transform: uppercase;
                }}
                .label {{ font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="alert-box">
                <h2>{alert['title']}</h2>
                <p><span class="label">Severity:</span> <span class="severity">{alert['severity']}</span></p>
                <p><span class="label">Time:</span> {alert['fired_at']}</p>
                <p><span class="label">Description:</span></p>
                <p>{alert['description']}</p>
        """

        if alert.get('labels'):
            html += "<p><span class='label'>Labels:</span></p><ul>"
            for key, value in alert['labels'].items():
                html += f"<li>{key}: {value}</li>"
            html += "</ul>"

        html += """
            </div>
        </body>
        </html>
        """

        return html
