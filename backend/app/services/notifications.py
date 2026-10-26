import os
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from app.core.config import settings

logger = logging.getLogger("brandpulse.notifications")


class BaseNotificationProvider(ABC):
    """
    Abstract notification provider interface for multi-channel shop owner communication.
    Supports Email (Resend / SMTP), SMS, and WhatsApp (Twilio) with Mock fallbacks.
    """
    @abstractmethod
    def send_email(self, to_email: str, subject: str, body_text: str, body_html: Optional[str] = None) -> bool:
        pass

    @abstractmethod
    def send_sms(self, to_phone: str, message: str) -> bool:
        pass

    @abstractmethod
    def send_whatsapp(self, to_phone: str, message: str) -> bool:
        pass


class MockNotificationProvider(BaseNotificationProvider):
    """
    Mock notification provider for local testing and zero-credential environments.
    Records all dispatched messages in memory for assertions and test validation.
    """
    def __init__(self):
        self.sent_notifications: List[Dict[str, Any]] = []

    def send_email(self, to_email: str, subject: str, body_text: str, body_html: Optional[str] = None) -> bool:
        record = {
            "channel": "email",
            "to": to_email,
            "subject": subject,
            "body_text": body_text,
            "body_html": body_html,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "delivered_mock"
        }
        self.sent_notifications.append(record)
        logger.info(f"[MockNotificationProvider] Email sent to '{to_email}': {subject}")
        return True

    def send_sms(self, to_phone: str, message: str) -> bool:
        record = {
            "channel": "sms",
            "to": to_phone,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "delivered_mock"
        }
        self.sent_notifications.append(record)
        logger.info(f"[MockNotificationProvider] SMS sent to '{to_phone}': {message}")
        return True

    def send_whatsapp(self, to_phone: str, message: str) -> bool:
        record = {
            "channel": "whatsapp",
            "to": to_phone,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "delivered_mock"
        }
        self.sent_notifications.append(record)
        logger.info(f"[MockNotificationProvider] WhatsApp sent to '{to_phone}': {message}")
        return True


class ResendOrSMTPNotificationProvider(BaseNotificationProvider):
    """
    Production-ready email provider using Resend API or SMTP, with graceful fallback to Mock.
    """
    def __init__(self, mock_fallback: Optional[MockNotificationProvider] = None):
        self.mock = mock_fallback or MockNotificationProvider()

    def send_email(self, to_email: str, subject: str, body_text: str, body_html: Optional[str] = None) -> bool:
        # 1. Try Resend API if API Key provided
        if settings.RESEND_API_KEY:
            try:
                import urllib.request
                url = "https://api.resend.com/emails"
                payload = {
                    "from": settings.SMTP_FROM_EMAIL,
                    "to": [to_email],
                    "subject": subject,
                    "text": body_text
                }
                if body_html:
                    payload["html"] = body_html

                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status in (200, 201, 202):
                        logger.info(f"[ResendEmail] Delivered email to {to_email}")
                        return True
            except Exception as e:
                logger.warning(f"[ResendEmail] Failed to send via Resend ({e}). Falling back to mock.")

        # 2. Try SMTP if configured
        if settings.SMTP_HOST:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = settings.SMTP_FROM_EMAIL
                msg["To"] = to_email
                msg.attach(MIMEText(body_text, "plain", "utf-8"))
                if body_html:
                    msg.attach(MIMEText(body_html, "html", "utf-8"))

                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    server.starttls()
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.sendmail(settings.SMTP_FROM_EMAIL, [to_email], msg.as_string())
                logger.info(f"[SMTPEmail] Delivered email to {to_email}")
                return True
            except Exception as e:
                logger.warning(f"[SMTPEmail] Failed to send via SMTP ({e}). Falling back to mock.")

        # Fallback to mock
        return self.mock.send_email(to_email, subject, body_text, body_html)

    def send_sms(self, to_phone: str, message: str) -> bool:
        return self.mock.send_sms(to_phone, message)

    def send_whatsapp(self, to_phone: str, message: str) -> bool:
        return self.mock.send_whatsapp(to_phone, message)


class TwilioNotificationProvider(BaseNotificationProvider):
    """
    Twilio provider for SMS and WhatsApp with graceful fallback to Mock.
    """
    def __init__(self, mock_fallback: Optional[MockNotificationProvider] = None):
        self.mock = mock_fallback or MockNotificationProvider()

    def send_email(self, to_email: str, subject: str, body_text: str, body_html: Optional[str] = None) -> bool:
        return self.mock.send_email(to_email, subject, body_text, body_html)

    def send_sms(self, to_phone: str, message: str) -> bool:
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_FROM_PHONE:
            try:
                import urllib.request
                import urllib.parse
                import base64

                url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
                data = urllib.parse.urlencode({
                    "From": settings.TWILIO_FROM_PHONE,
                    "To": to_phone,
                    "Body": message
                }).encode("utf-8")

                auth_str = f"{settings.TWILIO_ACCOUNT_SID}:{settings.TWILIO_AUTH_TOKEN}"
                b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={"Authorization": f"Basic {b64_auth}"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status in (200, 201):
                        logger.info(f"[TwilioSMS] Sent SMS to {to_phone}")
                        return True
            except Exception as e:
                logger.warning(f"[TwilioSMS] Failed to send SMS via Twilio ({e}). Falling back to mock.")

        return self.mock.send_sms(to_phone, message)

    def send_whatsapp(self, to_phone: str, message: str) -> bool:
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_WHATSAPP_FROM:
            try:
                import urllib.request
                import urllib.parse
                import base64

                wa_to = to_phone if to_phone.startswith("whatsapp:") else f"whatsapp:{to_phone}"
                url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
                data = urllib.parse.urlencode({
                    "From": settings.TWILIO_WHATSAPP_FROM,
                    "To": wa_to,
                    "Body": message
                }).encode("utf-8")

                auth_str = f"{settings.TWILIO_ACCOUNT_SID}:{settings.TWILIO_AUTH_TOKEN}"
                b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={"Authorization": f"Basic {b64_auth}"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status in (200, 201):
                        logger.info(f"[TwilioWhatsApp] Sent WhatsApp message to {to_phone}")
                        return True
            except Exception as e:
                logger.warning(f"[TwilioWhatsApp] Failed to send WhatsApp via Twilio ({e}). Falling back to mock.")

        return self.mock.send_whatsapp(to_phone, message)


class WhatsAppCloudNotificationProvider(BaseNotificationProvider):
    """
    Direct Meta WhatsApp Business Cloud API provider for high-reliability crisis alerts.
    """
    def __init__(self, mock_fallback: Optional[MockNotificationProvider] = None):
        self.mock = mock_fallback or MockNotificationProvider()

    def send_email(self, to_email: str, subject: str, body_text: str, body_html: Optional[str] = None) -> bool:
        return self.mock.send_email(to_email, subject, body_text, body_html)

    def send_sms(self, to_phone: str, message: str) -> bool:
        return self.mock.send_sms(to_phone, message)

    def send_whatsapp(self, to_phone: str, message: str) -> bool:
        token = getattr(settings, "WHATSAPP_CLOUD_ACCESS_TOKEN", "")
        phone_id = getattr(settings, "WHATSAPP_CLOUD_PHONE_NUMBER_ID", "")

        if token and phone_id:
            try:
                import urllib.request
                import urllib.parse
                import json

                # Clean phone number to E.164 digits without 'whatsapp:' or '+'
                clean_phone = to_phone.replace("whatsapp:", "").replace("+", "").replace(" ", "").strip()
                url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"

                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": clean_phone,
                    "type": "text",
                    "text": {"preview_url": True, "body": message}
                }

                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status in (200, 201):
                        logger.info(f"[MetaWhatsAppCloud] Dispatched WhatsApp message to {clean_phone}")
                        return True
            except Exception as e:
                logger.warning(f"[MetaWhatsAppCloud] Delivery failed ({e}). Falling back to mock record.")

        return self.mock.send_whatsapp(to_phone, message)


def get_notification_provider() -> BaseNotificationProvider:
    """
    Factory to return the active notification provider.
    """
    prov = (settings.NOTIFICATION_PROVIDER or "mock").lower().strip()
    shared_mock = MockNotificationProvider()
    if prov in ("resend", "smtp"):
        return ResendOrSMTPNotificationProvider(mock_fallback=shared_mock)
    elif prov == "twilio":
        return TwilioNotificationProvider(mock_fallback=shared_mock)
    elif prov in ("whatsapp", "meta", "whatsapp_cloud"):
        return WhatsAppCloudNotificationProvider(mock_fallback=shared_mock)
    return shared_mock


# Global provider instance
notification_provider = get_notification_provider()


class NotificationDispatcher:
    """
    High-level business dispatcher that inspects business preferences,
    verifies user opt-ins, and dispatches alerts & digests across Email, SMS, or WhatsApp.
    """
    def __init__(self, provider: Optional[BaseNotificationProvider] = None):
        self.provider = provider or notification_provider

    def dispatch_bad_review_alert(self, brand: Dict[str, Any], mention: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatches an immediate alert when a 1-2 star review is received.
        Respects owner preferences (notify_bad_reviews) and opt-ins.
        """
        if brand.get("notify_bad_reviews") is False:
            return {"dispatched": False, "reason": "notify_bad_reviews_disabled"}

        rating = mention.get("rating", 1)
        author = mention.get("author", "A customer")
        source = mention.get("source") or mention.get("platform") or "Google Reviews"
        text = mention.get("content", "")
        short_text = text[:160] + ("..." if len(text) > 160 else "")
        business_name = brand.get("name", "Your Shop")

        subject = f"⚠️ [{business_name}] New {rating}-Star Review Needs Attention"
        body = (
            f"Hi {business_name} Team,\n\n"
            f"A customer ({author}) just posted a {rating}-star review on {source}:\n\n"
            f"\"{short_text}\"\n\n"
            f"Quick tip: Replying within 2 hours turns 33% of unhappy reviewers into repeat customers.\n"
            f"Log in to BrandPulse AI to see an AI-suggested polite response in the customer's language.\n\n"
            f"— BrandPulse AI Alerts"
        )

        results = {}
        email = brand.get("notification_email") or brand.get("owner_email")
        if email and brand.get("email_opt_in", True):
            results["email"] = self.provider.send_email(email, subject, body)

        phone = brand.get("notification_phone")
        if phone and brand.get("whatsapp_opt_in", False):
            wa_msg = f"⚠️ *{business_name} Alert*: New {rating}-star review on {source} from {author}:\n\"{short_text}\"\nLog in to BrandPulse to reply."
            results["whatsapp"] = self.provider.send_whatsapp(phone, wa_msg)
        elif phone and brand.get("sms_opt_in", False):
            sms_msg = f"{business_name} Alert: New {rating}-star review from {author}: \"{short_text[:80]}...\". Check BrandPulse."
            results["sms"] = self.provider.send_sms(phone, sms_msg)

        return {"dispatched": True, "results": results}

    def dispatch_spike_alert(self, brand: Dict[str, Any], count: int, time_window: str = "24 hours") -> Dict[str, Any]:
        """
        Dispatches an alert when an unusual volume of complaints occurs.
        """
        if brand.get("notify_spike") is False:
            return {"dispatched": False, "reason": "notify_spike_disabled"}

        business_name = brand.get("name", "Your Shop")
        subject = f"🚨 [{business_name}] Unusual Spike in Unhappy Reviews ({count} in {time_window})"
        body = (
            f"Notice for {business_name}:\n\n"
            f"We detected an unusual cluster of {count} negative reviews in the last {time_window}.\n"
            f"Common themes may include delays, staff, or food quality.\n"
            f"Please check your BrandPulse Dashboard immediately to see 'What to fix first'.\n\n"
            f"— BrandPulse AI Alerts"
        )

        results = {}
        email = brand.get("notification_email") or brand.get("owner_email")
        if email and brand.get("email_opt_in", True):
            results["email"] = self.provider.send_email(email, subject, body)

        phone = brand.get("notification_phone")
        if phone and brand.get("whatsapp_opt_in", False):
            wa_msg = f"🚨 *{business_name} Spike Alert*: {count} negative reviews detected in the last {time_window}. Check BrandPulse dashboard to review."
            results["whatsapp"] = self.provider.send_whatsapp(phone, wa_msg)

        return {"dispatched": True, "results": results}

    def dispatch_weekly_digest(self, brand: Dict[str, Any], summary_text: str, stats: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Dispatches the weekly plain-language AI briefing at the owner's configured digest day & time.
        """
        if brand.get("notify_weekly_summary") is False:
            return {"dispatched": False, "reason": "notify_weekly_summary_disabled"}

        business_name = brand.get("name", "Your Shop")
        subject = f"📊 [{business_name}] Your Weekly Customer Review Briefing"
        body = (
            f"Good morning {business_name}!\n\n"
            f"Here is your weekly customer briefing:\n\n"
            f"{summary_text}\n\n"
            f"Have a great week serving your customers!\n"
            f"— BrandPulse AI Team"
        )

        results = {}
        email = brand.get("notification_email") or brand.get("owner_email")
        if email and brand.get("email_opt_in", True):
            results["email"] = self.provider.send_email(email, subject, body)

        phone = brand.get("notification_phone")
        if phone and brand.get("whatsapp_opt_in", False):
            short_summary = summary_text[:300] + ("..." if len(summary_text) > 300 else "")
            wa_msg = f"📊 *{business_name} Weekly Briefing*:\n{short_summary}\n\nLog in for full insights."
            results["whatsapp"] = self.provider.send_whatsapp(phone, wa_msg)

        return {"dispatched": True, "results": results}


notification_dispatcher = NotificationDispatcher()
