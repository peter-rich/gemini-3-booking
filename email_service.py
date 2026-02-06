"""
Email service using Brevo SMTP
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional, List
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending itineraries and alerts"""
    
    def __init__(self):
        """Initialize email service with Brevo credentials"""
        self.smtp_host = "smtp-relay.brevo.com"
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL", "a1afbb001@smtp-brevo.com")
        self.sender_password = os.getenv("SENDER_PASSWORD", "")
        self.email_from = os.getenv("EMAIL_FROM", "noreply@myagentbooking.com")
        self.email_from_name = os.getenv("EMAIL_FROM_NAME", "MyAgent Booking")
        self.email_reply_to = os.getenv("EMAIL_REPLY_TO", "support@myagentbooking.com")
        self.use_tls = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
    
    def send_email(self, to_email: str, subject: str, html_body: str,
                   attachments: Optional[List[dict]] = None) -> bool:
        """
        Send email via Brevo SMTP
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML email body
            attachments: List of dicts with 'filename' and 'content' keys
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.email_from_name} <{self.email_from}>"
            msg['To'] = to_email
            msg['Reply-To'] = self.email_reply_to
            
            # Attach HTML body
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Attach files if provided
            if attachments:
                for attachment in attachments:
                    part = MIMEApplication(
                        attachment['content'],
                        Name=attachment['filename']
                    )
                    part['Content-Disposition'] = f'attachment; filename="{attachment["filename"]}"'
                    msg.attach(part)
            
            # Connect and send
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.set_debuglevel(0)
            
            if self.use_tls:
                server.starttls()
            
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def send_itinerary_email(self, to_email: str, user_name: str,
                            trip_name: str, destination: str,
                            depart_date: str, return_date: str,
                            pdf_content: bytes, ics_content: bytes) -> bool:
        """Send trip itinerary with attachments"""
        
        subject = f"🎫 Your Trip Itinerary: {trip_name}"
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   color: white; padding: 30px; text-align: center; border-radius: 10px; }}
        .content {{ background: #f9f9f9; padding: 30px; margin: 20px 0; border-radius: 10px; }}
        .trip-info {{ background: white; padding: 20px; margin: 15px 0; border-left: 4px solid #667eea; }}
        .button {{ background: #667eea; color: white; padding: 12px 30px; text-decoration: none; 
                   border-radius: 5px; display: inline-block; margin: 10px 0; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; }}
        .alert-box {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✈️ Your Trip is Ready!</h1>
            <p>Complete itinerary with booking links</p>
        </div>
        
        <div class="content">
            <h2>Hello {user_name},</h2>
            <p>Your travel itinerary for <strong>{trip_name}</strong> is ready! We've attached your complete itinerary and calendar file.</p>
            
            <div class="trip-info">
                <h3>📍 Trip Details</h3>
                <p><strong>Destination:</strong> {destination}</p>
                <p><strong>Departure:</strong> {depart_date}</p>
                <p><strong>Return:</strong> {return_date}</p>
            </div>
            
            <h3>📎 Attachments</h3>
            <ul>
                <li><strong>travel_itinerary.pdf</strong> - Complete trip details with booking links</li>
                <li><strong>trip_calendar.ics</strong> - Import to your calendar app</li>
            </ul>
            
            <h3>⚡ Quick Actions</h3>
            <p>Open the PDF to find:</p>
            <ul>
                <li>✅ Flight comparison with direct booking links</li>
                <li>🏨 Hotel recommendations with prices</li>
                <li>🚖 Transportation estimates</li>
                <li>📋 Pre-booking checklist</li>
            </ul>
            
            <div class="alert-box">
                <strong>🔔 Real-Time Monitoring Active</strong><br>
                We'll monitor your flights and send alerts for any delays, gate changes, or price drops.
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="https://myagentbooking.com/trips" class="button">View on Dashboard</a>
            </div>
        </div>
        
        <div class="footer">
            <p>© 2025 MyAgent Booking | Powered by Gemini AI</p>
            <p>Need help? Reply to this email or visit our support center.</p>
        </div>
    </div>
</body>
</html>
"""
        
        attachments = [
            {'filename': 'travel_itinerary.pdf', 'content': pdf_content},
            {'filename': 'trip_calendar.ics', 'content': ics_content}
        ]
        
        return self.send_email(to_email, subject, html_body, attachments)
    
    def send_flight_alert(self, to_email: str, user_name: str, 
                         alert_type: str, flight_info: dict, 
                         message: str) -> bool:
        """Send flight status alert"""
        
        severity_colors = {
            'info': '#17a2b8',
            'warning': '#ffc107',
            'critical': '#dc3545'
        }
        
        severity = alert_type.split('_')[0] if '_' in alert_type else 'info'
        color = severity_colors.get(severity, '#17a2b8')
        
        subject = f"⚠️ Flight Alert: {flight_info.get('flight_number', 'Your Flight')}"
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: {color}; color: white; padding: 20px; text-align: center; border-radius: 10px; }}
        .content {{ background: #f9f9f9; padding: 30px; margin: 20px 0; border-radius: 10px; }}
        .alert-box {{ background: white; border-left: 4px solid {color}; padding: 20px; margin: 15px 0; }}
        .button {{ background: {color}; color: white; padding: 12px 30px; text-decoration: none; 
                   border-radius: 5px; display: inline-block; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚠️ Flight Status Update</h1>
        </div>
        
        <div class="content">
            <h2>Hello {user_name},</h2>
            
            <div class="alert-box">
                <h3>{message}</h3>
                <p><strong>Flight:</strong> {flight_info.get('flight_number', 'N/A')}</p>
                <p><strong>Route:</strong> {flight_info.get('route', 'N/A')}</p>
                <p><strong>Scheduled:</strong> {flight_info.get('scheduled_time', 'N/A')}</p>
                {f"<p><strong>Updated Time:</strong> {flight_info.get('updated_time', 'N/A')}</p>" if flight_info.get('updated_time') else ""}
            </div>
            
            <h3>💡 Recommended Actions:</h3>
            <ul>
                <li>Check airline website for latest updates</li>
                <li>Contact your airline if rebooking is needed</li>
                <li>Monitor our dashboard for real-time updates</li>
            </ul>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="https://myagentbooking.com/trips" class="button">View Dashboard</a>
            </div>
        </div>
        
        <div style="text-align: center; color: #666; font-size: 12px; margin-top: 30px;">
            <p>© 2025 MyAgent Booking | Real-Time Flight Monitoring</p>
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(to_email, subject, html_body)
    
    def send_budget_alert(self, to_email: str, user_name: str,
                         trip_name: str, budget: float, 
                         current_cost: float, over_budget: bool) -> bool:
        """Send budget warning email"""
        
        percent = (current_cost / budget * 100) if budget > 0 else 0
        
        if over_budget:
            subject = f"🚨 Budget Alert: {trip_name} Over Budget"
            alert_msg = f"Your trip spending has exceeded the budget by ${current_cost - budget:.2f}"
            color = "#dc3545"
        else:
            subject = f"⚠️ Budget Warning: {trip_name} at {percent:.0f}%"
            alert_msg = f"You've used {percent:.0f}% of your ${budget:.2f} budget"
            color = "#ffc107"
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: {color}; color: white; padding: 20px; text-align: center; border-radius: 10px; }}
        .content {{ background: #f9f9f9; padding: 30px; margin: 20px 0; border-radius: 10px; }}
        .budget-box {{ background: white; padding: 20px; margin: 15px 0; border-left: 4px solid {color}; }}
        .progress-bar {{ background: #e9ecef; height: 30px; border-radius: 15px; overflow: hidden; }}
        .progress-fill {{ background: {color}; height: 100%; text-align: center; line-height: 30px; 
                          color: white; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💰 Budget Alert</h1>
        </div>
        
        <div class="content">
            <h2>Hello {user_name},</h2>
            
            <div class="budget-box">
                <h3>{alert_msg}</h3>
                <p><strong>Trip:</strong> {trip_name}</p>
                <p><strong>Budget:</strong> ${budget:.2f}</p>
                <p><strong>Current Spending:</strong> ${current_cost:.2f}</p>
                <p><strong>Remaining:</strong> ${max(0, budget - current_cost):.2f}</p>
                
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {min(100, percent):.0f}%">
                        {percent:.0f}%
                    </div>
                </div>
            </div>
            
            <h3>💡 Tips to Stay on Budget:</h3>
            <ul>
                <li>Review your upcoming bookings</li>
                <li>Consider budget-friendly alternatives</li>
                <li>Look for discounts and deals</li>
                <li>Adjust your itinerary if needed</li>
            </ul>
        </div>
        
        <div style="text-align: center; color: #666; font-size: 12px; margin-top: 30px;">
            <p>© 2025 MyAgent Booking</p>
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(to_email, subject, html_body)


# Singleton instance
_email_service = None

def get_email_service() -> EmailService:
    """Get singleton email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
