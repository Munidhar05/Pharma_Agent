import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
import httpx
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models.audit import Notification, AgentExecutionLog
from backend.app.models.user import User, UserPreferences

logger = logging.getLogger(__name__)


class NotificationAgent:
    """
    Agent 11: Multi-Channel Notification Agent.
    Dispatches alerts via In-App Dashboard, SMTP Email, and Telegram.
    Enforces user preferences and avoids notification fatigue.
    """

    def __init__(self, db: Session):
        self.db = db

    def dispatch(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "JobMatch",
        preferred_channel: Optional[str] = None
    ) -> List[Notification]:
        """
        Dispatches a notification across the user's enabled notification channels.
        Always saves in-app dashboard notification.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"Notification user {user_id} not found.")
            return []

        # Check user preferences
        prefs = self.db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
        channels = prefs.notification_channels if (prefs and prefs.notification_channels) else ["dashboard"]
        if preferred_channel and preferred_channel not in channels:
            channels.append(preferred_channel)

        created_notifications: List[Notification] = []

        # 1. In-App Dashboard Notification (Always Created)
        dash_notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            channel="dashboard",
            is_read=False,
            sent_at=datetime.utcnow()
        )
        self.db.add(dash_notif)
        created_notifications.append(dash_notif)

        # 2. SMTP Email Dispatch
        if "email" in channels and settings.SMTP_HOST and user.email:
            self._send_email(to_email=user.email, subject=title, body_text=message)
            email_notif = Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                channel="email",
                is_read=True,
                sent_at=datetime.utcnow()
            )
            self.db.add(email_notif)
            created_notifications.append(email_notif)

        # 3. Telegram Dispatch
        if "telegram" in channels and settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
            self._send_telegram(message=f"*{title}*\n\n{message}")
            tg_notif = Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                channel="telegram",
                is_read=True,
                sent_at=datetime.utcnow()
            )
            self.db.add(tg_notif)
            created_notifications.append(tg_notif)

        self.db.commit()
        for n in created_notifications:
            self.db.refresh(n)

        # Audit Agent Log
        exec_id = f"notif-{uuid.uuid4().hex[:6]}"
        exec_log = AgentExecutionLog(
            agent_name="NotificationAgent",
            execution_id=exec_id,
            task_type="dispatch_notification",
            status="SUCCESS",
            items_processed=len(created_notifications),
            items_failed=0,
            metadata_json={
                "user_id": user_id,
                "title": title,
                "channels": channels,
                "notification_type": notification_type
            },
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow()
        )
        self.db.add(exec_log)
        self.db.commit()

        return created_notifications

    def _send_email(self, to_email: str, subject: str, body_text: str):
        """Sends an email notification via SMTP."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.EMAILS_FROM_EMAIL
            msg["To"] = to_email

            part = MIMEText(body_text, "plain")
            msg.attach(part)

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.starttls()
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.EMAILS_FROM_EMAIL, [to_email], msg.as_string())
            logger.info(f"Email notification successfully sent to {to_email}.")
        except Exception as e:
            logger.warning(f"Could not dispatch SMTP email to {to_email}: {e}")

    def _send_telegram(self, message: str):
        """Sends a notification via Telegram Bot API."""
        try:
            tg_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown"
            }
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(tg_url, json=payload)
                if resp.status_code == 200:
                    logger.info("Telegram notification successfully sent.")
                else:
                    logger.warning(f"Telegram dispatch failed with code {resp.status_code}.")
        except Exception as e:
            logger.warning(f"Could not dispatch Telegram alert: {e}")

    # Helper milestone methods
    def notify_high_match(self, user_id: int, job_title: str, company_name: str, match_score: float, job_id: int):
        title = f"⭐ Strong Pharma Match ({round(match_score)}%): {company_name}"
        msg = (
            f"A high-scoring opportunity matching your verified profile has been discovered:\n"
            f"Position: {job_title}\n"
            f"Company: {company_name}\n"
            f"Match Score: {round(match_score)}%\n\n"
            f"Log in to your dashboard to review ATS keyword coverage and prepare your application."
        )
        return self.dispatch(user_id=user_id, title=title, message=msg, notification_type="StrongMatch")

    def notify_awaiting_approval(self, user_id: int, job_title: str, company_name: str, app_id: int):
        title = f"⏳ Application Awaiting Your Approval: {company_name}"
        msg = (
            f"Your application for '{job_title}' at {company_name} is mapped and ready.\n"
            f"Per your preference (Assisted application with approval), your explicit consent is required before submission.\n"
            f"Please verify the mapped form fields and screening questions."
        )
        return self.dispatch(user_id=user_id, title=title, message=msg, notification_type="ActionRequired")

    def notify_application_confirmed(self, user_id: int, job_title: str, company_name: str, ref_id: str):
        title = f"✅ Application Confirmed: {company_name}"
        msg = (
            f"Your application for '{job_title}' at {company_name} has been successfully submitted and confirmed.\n"
            f"Official Submission Reference: {ref_id}.\n"
            f"The application tracking agent is actively monitoring this vacancy."
        )
        return self.dispatch(user_id=user_id, title=title, message=msg, notification_type="Submitted")

    def notify_interview_scheduled(self, user_id: int, job_title: str, company_name: str, notes: Optional[str] = None):
        title = f"🎉 Interview Scheduled: {company_name}"
        msg = (
            f"Great news! An interview stage has been scheduled for your application:\n"
            f"Role: {job_title}\n"
            f"Company: {company_name}\n"
            f"Details: {notes or 'Check your email for calendar invite and interview instructions.'}"
        )
        return self.dispatch(user_id=user_id, title=title, message=msg, notification_type="Interview")

    def notify_assessment_pending(self, user_id: int, job_title: str, company_name: str, notes: Optional[str] = None):
        title = f"📝 Assessment Pending: {company_name}"
        msg = (
            f"An online assessment or technical challenge has been requested for your application for {job_title} at {company_name}.\n"
            f"Notes: {notes or 'Please complete before the deadline.'}"
        )
        return self.dispatch(user_id=user_id, title=title, message=msg, notification_type="Assessment")

