# buro/services/notification_service.py
#
# Email notification service for user communications.
#
# Educational Notes for Junior Developers:
# - Async email sending: Non-blocking I/O for performance.
# - Background tasks: FastAPI background tasks prevent request blocking.
# - Email templates: Maintainable, reusable notification patterns.
# - SMTP vs email APIs: Self-hosted vs third-party tradeoffs.

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
import os
import logging

from fastapi import BackgroundTasks

from buro.models import User, Issue


class EmailNotificationService:
    """Service for sending email notifications to users.

    Why FastAPI BackgroundTasks over Celery:
    - Simpler deployment (single process)
    - Better async FastAPI integration
    - Appropriate for moderate email volume
    - Tradeoff: Less robust for high-volume/email-heavy apps

    Educational Note: Background tasks execute after response is sent.
    Perfect for operations that shouldn't delay user interaction.
    """

    def __init__(self):
        # Configuration from environment or constants
        # Why environment variables: Secure, configurable per environment
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)

        self.logger = logging.getLogger(__name__)
        enable_flag = os.getenv("ENABLE_EMAIL_NOTIFICATIONS", "false").lower() == "true"
        self.email_enabled = enable_flag and bool(self.smtp_username and self.smtp_password)

        # Email settings
        self.app_name = "Buro - Agile Project Management"

    async def send_issue_assigned_notification(
        self, background_tasks: BackgroundTasks, issue: Issue, assignee: User
    ):
        """Send notification when an issue is assigned to a user.

        Why background task: Email sending is slow, shouldn't block API response.
        Follows "respond fast, work later" principle of reactive architectures.
        """
        if not self.email_enabled:
            self.logger.debug("Email notifications disabled; skipping issue assignment email")
            return
        subject = f"[{issue.key}] Issue assigned to you"

        body = f"""
        Hi {assignee.full_name},

        You have been assigned to the following issue:

        **{issue.title}**
        Key: {issue.key}
        Type: {issue.issue_type.upper()}
        Priority: {issue.priority.upper()}

        Description:
        {issue.description or 'No description provided.'}

        You can view this issue at: http://localhost:4000/issues/{issue.key}

        Best regards,
        {self.app_name}
        """

        background_tasks.add_task(
            self._send_email,
            recipient_email=assignee.email,
            subject=subject,
            body=body
        )

    async def send_issue_status_changed_notification(
        self,
        background_tasks: BackgroundTasks,
        issue: Issue,
        old_status: str,
        new_status: str,
        changed_by: User,
        subscribers: List[User]
    ):
        """Send notification when issue status changes.

        Why subscriber list: Notify relevant team members.
        Future enhancement: Add explicit subscription management.
        """
        if not subscribers or not self.email_enabled:
            if not subscribers:
                self.logger.debug("No subscribers for status change email")
            else:
                self.logger.debug("Email notifications disabled; skipping status change email")
            return

        subject = f"[{issue.key}] Status changed: {old_status} → {new_status}"

        body = f"""
        Hi,

        The status of issue {issue.key} has been changed:

        **{issue.title}**

        Changed by: {changed_by.full_name}
        Status: {old_status} → {new_status}
        Type: {issue.issue_type.upper()}
        Priority: {issue.priority.upper()}

        Assigned to: {issue.assignee.full_name if issue.assignee else 'Unassigned'}

        You can view this issue at: http://localhost:4000/issues/{issue.key}

        Best regards,
        {self.app_name}
        """

        for subscriber in subscribers:
            background_tasks.add_task(
                self._send_email,
                recipient_email=subscriber.email,
                subject=subject,
                body=body
            )

    async def send_welcome_notification(
        self, background_tasks: BackgroundTasks, user: User
    ):
        """Send welcome email to new users.

        Why separate method: Standardized onboarding experience.
        Opportunity for welcome email templates and user guides.
        """
        if not self.email_enabled:
            self.logger.debug("Email notifications disabled; skipping welcome email")
            return

        subject = f"Welcome to {self.app_name}"

        body = f"""
        Welcome to {self.app_name}, {user.full_name}!

        Your account has been created successfully.

        Email: {user.email}
        Role: {user.role.upper()}

        You can start creating projects and managing your agile workflow at:
        http://localhost:4000

        If you have any questions, please don't hesitate to contact support.

        Happy project managing!

        Best regards,
        The {self.app_name} Team
        """

        background_tasks.add_task(
            self._send_email,
            recipient_email=user.email,
            subject=subject,
            body=body
        )

    async def _send_email(
        self,
        recipient_email: str,
        subject: str,
        body: str
    ):
        """Low-level email sending function.

        Why async: Awaits network I/O for SMTP server communication.
        Why try/catch: Network issues shouldn't crash background tasks.
        """
        if not self.email_enabled:
            self.logger.debug("Email notifications disabled; skipping send")
            return

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = recipient_email
            msg['Subject'] = subject

            # Add plain text body
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)

            # Send email via SMTP
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Secure connection
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()

            self.logger.info("📧 Email sent: %s → %s", subject, recipient_email)

        except Exception as e:
            self.logger.exception("❌ Failed to send email to %s", recipient_email)
            # In production: Log to error tracking system like Sentry

    # Future enhancement: HTML email templates
    def _create_html_email(self, subject: str, body_text: str) -> MIMEMultipart:
        """Future: Create HTML email with professional templates."""
        # Implementation for rich email formatting would go here
        raise NotImplementedError
