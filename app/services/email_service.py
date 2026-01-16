"""
Email Service

Handles sending emails via SendGrid.
Provides methods for sending check-in and summary emails.
"""

import logging
from typing import Optional, Dict, Any

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending emails via SendGrid.
    
    Handles all email communications including:
    - Daily check-in emails
    - Verification summary emails
    """
    
    def __init__(self):
        """Initialize SendGrid client."""
        self.client = SendGridAPIClient(settings.sendgrid_api_key)
        self.from_email = Email(settings.sendgrid_from_email)
        self.reply_to_email = settings.sendgrid_reply_to_email
    
    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email via SendGrid.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content
            text_content: Plain text content (optional)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create mail object
            mail = Mail(
                from_email=self.from_email,
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            # Add plain text content if provided
            if text_content:
                mail.content = [
                    Content("text/plain", text_content),
                    Content("text/html", html_content)
                ]
            
            # Set reply-to
            mail.reply_to = Email(self.reply_to_email)
            
            # Send email
            response = self.client.send(mail)
            
            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"Email sent successfully to {to_email}: {subject}")
                return True
            else:
                logger.error(
                    f"Failed to send email to {to_email}. "
                    f"Status: {response.status_code}, Body: {response.body}"
                )
                return False
                
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}", exc_info=True)
            return False
    
    def send_daily_checkin(
        self,
        to_email: str,
        user_name: str,
        date_str: str
    ) -> bool:
        """
        Send daily check-in email asking about the user's day.
        
        Args:
            to_email: User's email address
            user_name: User's name or GitHub username
            date_str: Date string (e.g., "Monday, January 15, 2024")
        
        Returns:
            True if successful, False otherwise
        """
        subject = f"Daily Check-in - {date_str}"
        
        # HTML content
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4A90E2; color: white; padding: 20px; border-radius: 5px; }}
                    .content {{ padding: 20px; background-color: #f9f9f9; margin-top: 20px; border-radius: 5px; }}
                    .footer {{ margin-top: 20px; padding: 10px; font-size: 12px; color: #666; }}
                    .cta {{ background-color: #4A90E2; color: white; padding: 10px 20px; 
                           text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 15px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>Daily Check-in</h2>
                    </div>
                    <div class="content">
                        <p>Hi {user_name},</p>
                        <p>Hope you had a productive day!</p>
                        <p><strong>How was your day today ({date_str})?</strong></p>
                        <p>Just reply to this email and tell me:</p>
                        <ul>
                            <li>What did you work on?</li>
                            <li>Any wins or accomplishments?</li>
                            <li>Any challenges or blockers?</li>
                        </ul>
                        <p>I'll verify your GitHub activity and send you a summary later tonight.</p>
                    </div>
                    <div class="footer">
                        <p>This is an automated message from your Personal AI Agent.</p>
                        <p>Reply to this email to share your update.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        # Plain text content
        text_content = f"""
        Daily Check-in - {date_str}
        
        Hi {user_name},
        
        Hope you had a productive day!
        
        How was your day today ({date_str})?
        
        Just reply to this email and tell me:
        - What did you work on?
        - Any wins or accomplishments?
        - Any challenges or blockers?
        
        I'll verify your GitHub activity and send you a summary later tonight.
        
        ---
        This is an automated message from your Personal AI Agent.
        Reply to this email to share your update.
        """
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    def send_verification_summary(
        self,
        to_email: str,
        user_name: str,
        date_str: str,
        verification_data: Dict[str, Any]
    ) -> bool:
        """
        Send verification summary email with GitHub activity results.
        
        Args:
            to_email: User's email address
            user_name: User's name or GitHub username
            date_str: Date string
            verification_data: Dictionary containing verification results
        
        Returns:
            True if successful, False otherwise
        """
        passed = verification_data.get("passed", False)
        commits = verification_data.get("commits_count", 0)
        prs = verification_data.get("prs_count", 0)
        issues = verification_data.get("issues_count", 0)
        repos = verification_data.get("repositories", [])
        user_response = verification_data.get("user_response", "")
        
        # Determine message tone
        if passed:
            status_emoji = "✅"
            status_text = "Great work!"
            status_color = "#4CAF50"
        else:
            status_emoji = "⚠️"
            status_text = "No activity detected"
            status_color = "#FF9800"
        
        subject = f"Daily Summary - {date_str} {status_emoji}"
        
        # Build repos section
        repos_html = ""
        if repos:
            repos_html = "<h3>Repositories with Activity:</h3><ul>"
            for repo in repos[:5]:  # Limit to 5 repos
                repos_html += f"<li><strong>{repo}</strong></li>"
            repos_html += "</ul>"
        
        # Build user response section
        user_response_html = ""
        if user_response:
            user_response_html = f"""
            <h3>Your Update:</h3>
            <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; 
                        border-left: 4px solid #2196F3;">
                <p style="margin: 0; white-space: pre-wrap;">{user_response}</p>
            </div>
            """
        
        # HTML content
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: {status_color}; color: white; padding: 20px; border-radius: 5px; }}
                    .content {{ padding: 20px; background-color: #f9f9f9; margin-top: 20px; border-radius: 5px; }}
                    .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                    .stat {{ text-align: center; padding: 15px; background-color: white; border-radius: 5px; flex: 1; margin: 0 5px; }}
                    .stat-number {{ font-size: 32px; font-weight: bold; color: {status_color}; }}
                    .stat-label {{ font-size: 14px; color: #666; }}
                    .footer {{ margin-top: 20px; padding: 10px; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>{status_emoji} Daily Summary - {date_str}</h2>
                        <p style="margin: 0;">{status_text}</p>
                    </div>
                    <div class="content">
                        <p>Hi {user_name},</p>
                        <p>Here's your GitHub activity summary for today:</p>
                        
                        <div class="stats">
                            <div class="stat">
                                <div class="stat-number">{commits}</div>
                                <div class="stat-label">Commits</div>
                            </div>
                            <div class="stat">
                                <div class="stat-number">{prs}</div>
                                <div class="stat-label">Pull Requests</div>
                            </div>
                            <div class="stat">
                                <div class="stat-number">{issues}</div>
                                <div class="stat-label">Issues</div>
                            </div>
                        </div>
                        
                        {repos_html}
                        {user_response_html}
                        
                        <p style="margin-top: 20px;">
                            {'Keep up the great work! ' if passed else 'Remember to push your work to GitHub! '}
                        </p>
                    </div>
                    <div class="footer">
                        <p>This is an automated summary from your Personal AI Agent.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        # Plain text content
        repos_text = ""
        if repos:
            repos_text = "\n\nRepositories with Activity:\n" + "\n".join(f"- {repo}" for repo in repos[:5])
        
        user_response_text = ""
        if user_response:
            user_response_text = f"\n\nYour Update:\n{user_response}\n"
        
        text_content = f"""
        Daily Summary - {date_str} {status_emoji}
        {status_text}
        
        Hi {user_name},
        
        Here's your GitHub activity summary for today:
        
        Commits: {commits}
        Pull Requests: {prs}
        Issues: {issues}
        {repos_text}
        {user_response_text}
        
        {'Keep up the great work!' if passed else 'Remember to push your work to GitHub!'}
        
        ---
        This is an automated summary from your Personal AI Agent.
        """
        
        return self._send_email(to_email, subject, html_content, text_content)