"""
Email Service for sending email reminders and notifications.
Uses Gmail SMTP (100% FREE - No API needed!).
"""

import os
import logging
from typing import Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications via Gmail SMTP (FREE)."""
    
    def __init__(self):
        """Initialize email service with Gmail SMTP configuration."""
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.smtp_from_email = os.getenv('SMTP_FROM_EMAIL', self.smtp_username)
        
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Validate that necessary configuration is present."""
        if not all([self.smtp_username, self.smtp_password]):
            logger.warning("⚠️ Email service not configured. Set SMTP_USERNAME and SMTP_PASSWORD in .env")
            self.is_configured = False
        else:
            logger.info(f"✅ Email service initialized with Gmail SMTP (FREE)")
            self.is_configured = True
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> dict:
        """
        Send an email via Gmail SMTP (FREE).
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            cc: Optional list of CC recipients
            bcc: Optional list of BCC recipients
            
        Returns:
            dict: Result with success status and details
        """
        if not self.is_configured:
            return {
                'success': False,
                'error': 'Email service is not configured. Set SMTP credentials in .env file.'
            }
        
        try:
            return await self._send_via_smtp(to_email, subject, body, html_body, cc, bcc)
        except Exception as e:
            logger.error(f"❌ Error sending email: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str],
        cc: Optional[List[str]],
        bcc: Optional[List[str]]
    ) -> dict:
        """Send email via SMTP."""
        try:
            logger.info(f"📧 Sending email to {to_email} via SMTP")
            
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.smtp_from_email
            message['To'] = to_email
            
            if cc:
                message['Cc'] = ', '.join(cc)
            
            # Attach plain text and HTML parts
            text_part = MIMEText(body, 'plain')
            message.attach(text_part)
            
            if html_body:
                html_part = MIMEText(html_body, 'html')
                message.attach(html_part)
            
            # Prepare recipient list
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.smtp_from_email, recipients, message.as_string())
            
            logger.info(f"✅ Email sent successfully to {to_email}")
            
            return {
                'success': True,
                'message': 'Email sent successfully via SMTP',
                'to': to_email,
                'subject': subject
            }
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP authentication failed: {e}")
            return {
                'success': False,
                'error': 'SMTP authentication failed. Check username and password.'
            }
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error: {e}")
            return {
                'success': False,
                'error': f'SMTP error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"❌ Error sending email via SMTP: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def send_reminder_email(
        self,
        to_email: str,
        reminder_message: str,
        scheduled_time: str
    ) -> dict:
        """
        Send a reminder email with a standard template.
        
        Args:
            to_email: Recipient email
            reminder_message: The reminder message
            scheduled_time: When the reminder was scheduled for
            
        Returns:
            dict: Result with success status
        """
        subject = "⏰ Reminder Notification"
        
        body = f"""
Hello!

This is your scheduled reminder:

{reminder_message}

Scheduled for: {scheduled_time}

---
This is an automated reminder from your Traffic Prediction System.
        """.strip()
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <h2 style="color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px;">
                    ⏰ Reminder Notification
                </h2>
                <div style="margin: 20px 0; padding: 15px; background-color: #ecf0f1; border-left: 4px solid #3498db; border-radius: 5px;">
                    <p style="font-size: 16px; color: #34495e; margin: 0;">
                        {reminder_message}
                    </p>
                </div>
                <p style="color: #7f8c8d; font-size: 14px;">
                    <strong>Scheduled for:</strong> {scheduled_time}
                </p>
                <hr style="border: none; border-top: 1px solid #ecf0f1; margin: 20px 0;">
                <p style="color: #95a5a6; font-size: 12px; text-align: center;">
                    This is an automated reminder from your Traffic Prediction System.
                </p>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(to_email, subject, body, html_body)


# Global service instance
email_service = EmailService()


# Convenience function
async def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None
) -> dict:
    """
    Send an email (convenience wrapper).
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Plain text body
        html_body: Optional HTML body
        
    Returns:
        dict: Result with success status
    """
    return await email_service.send_email(to_email, subject, body, html_body)
