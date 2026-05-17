import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.utils import timezone

from core.models import (
    DailyVerse,
    PrayerReminder,
    PushSubscription,
    ReminderDelivery,
)


class Command(BaseCommand):
    help = "Send due email and push prayer reminders."

    def handle(self, *args, **options):
        # Railway cron: run `python manage.py send_reminders` every minute.
        now = timezone.localtime(timezone.now())
        today = timezone.localdate()
        verse = DailyVerse.objects.filter(date=today).first()
        verse_text = (
            verse.verse_text
            if verse
            else "The Lord is near to all who call on him, to all who call on him in truth."
        )
        reference = verse.reference if verse else "Psalm 145:18"
        reminders = (
            PrayerReminder.objects.filter(
                is_active=True,
                time__hour=now.hour,
                time__minute=now.minute,
                user__onboarding_complete=True,
            )
            .select_related("user")
            .exclude(user__last_active=today)
        )
        sent_email = 0
        sent_push = 0

        for reminder in reminders:
            user = reminder.user
            title = f"{reminder.label or reminder.get_routine_display()} prayer time"
            body = (
                f"Hi {user.username},\n\n"
                "Your quiet hour is now.\n\n"
                "Today's verse:\n"
                f"\"{verse_text}\"\n"
                f"- {reference}\n\n"
                "Open your journal and write what's on your heart today.\n\n"
                f"{settings.SITE_URL}/dashboard/\n\n"
                "- PrayerStreak PH\n\n"
                f"To stop receiving reminders, update your settings at {settings.SITE_URL}/profile/"
            )

            if (
                reminder.email_enabled
                and user.email
                and user.email_reminders
                and user.reminder_email_enabled
            ):
                if self.create_delivery(user, reminder, ReminderDelivery.Channel.EMAIL, today):
                    send_mail(
                        f"Your quiet hour - {today.strftime('%A')}, {today.strftime('%B %d, %Y')}",
                        body,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                    )
                    sent_email += 1

            if reminder.push_enabled and user.reminder_push_enabled:
                if self.create_delivery(user, reminder, ReminderDelivery.Channel.PUSH, today):
                    sent_push += self.send_push_notifications(user, title, verse_text, reference)

        self.stdout.write(
            self.style.SUCCESS(
                f"Sent {sent_email} email reminder(s) and {sent_push} push notification(s)."
            )
        )

    def create_delivery(self, user, reminder, channel, today):
        try:
            ReminderDelivery.objects.create(
                user=user,
                reminder=reminder,
                channel=channel,
                sent_for_date=today,
            )
            return True
        except IntegrityError:
            return False

    def send_push_notifications(self, user, title, verse_text, reference):
        if not settings.VAPID_PUBLIC_KEY or not settings.VAPID_PRIVATE_KEY:
            return 0

        try:
            from pywebpush import WebPushException, webpush
        except ImportError:
            return 0

        sent_count = 0
        subscriptions = PushSubscription.objects.filter(user=user, is_active=True)
        for subscription in subscriptions:
            payload = json.dumps(
                {
                    "title": title,
                    "body": f"{reference}: {verse_text[:120]}",
                    "url": f"{settings.SITE_URL}/dashboard/",
                }
            )
            try:
                webpush(
                    subscription_info={
                        "endpoint": subscription.endpoint,
                        "keys": {
                            "p256dh": subscription.p256dh,
                            "auth": subscription.auth,
                        },
                    },
                    data=payload,
                    vapid_private_key=settings.VAPID_PRIVATE_KEY,
                    vapid_claims={"sub": f"mailto:{settings.VAPID_ADMIN_EMAIL}"},
                )
                sent_count += 1
            except WebPushException as exc:
                if getattr(exc.response, "status_code", None) in {404, 410}:
                    subscription.is_active = False
                    subscription.save(update_fields=["is_active"])
        return sent_count
