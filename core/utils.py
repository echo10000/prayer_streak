from datetime import timedelta

from django.utils import timezone

from .models import StreakLog


def update_streak(user):
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)

    if user.last_active == today:
        return user.streak

    has_yesterday_log = StreakLog.objects.filter(user=user, date=yesterday).exists()
    has_previous_logs = StreakLog.objects.filter(user=user, date__lt=today).exists()

    if has_yesterday_log:
        user.streak += 1
    elif not has_previous_logs:
        user.streak = 1
    else:
        user.streak = 1

    user.last_active = today
    user.save(update_fields=["streak", "last_active"])
    return user.streak
