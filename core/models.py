import secrets
import string

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class PrayerFocus(models.TextChoices):
        PERSONAL = "personal", "Personal"
        FAMILY = "family", "Family"
        NATION = "nation", "Nation"
        ALL = "all", "All of the above"

    class AgeGroup(models.TextChoices):
        CHILD = "child", "Child (7-12)"
        TEEN = "teen", "Teen (13-17)"
        ADULT = "adult", "Adult (18-59)"
        SENIOR = "senior", "Senior (60+)"

    referral_code = models.CharField(max_length=8, unique=True, blank=True)
    points = models.IntegerField(default=0)
    streak = models.IntegerField(default=0)
    streak_freezes = models.PositiveIntegerField(default=1)
    grace_days_used = models.PositiveIntegerField(default=0)
    sabbath_mode = models.BooleanField(default=False)
    dark_mode = models.BooleanField(default=False)
    reminder_email_enabled = models.BooleanField(default=False)
    reminder_push_enabled = models.BooleanField(default=False)
    onboarding_complete = models.BooleanField(default=False)
    quiet_time = models.TimeField(null=True, blank=True)
    prayer_focus = models.CharField(
        max_length=50,
        choices=PrayerFocus.choices,
        default=PrayerFocus.PERSONAL,
    )
    email_reminders = models.BooleanField(default=True)
    senior_mode = models.BooleanField(default=False)
    age_group = models.CharField(
        max_length=20,
        choices=AgeGroup.choices,
        default=AgeGroup.ADULT,
    )
    last_active = models.DateField(null=True, blank=True)
    referred_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="referrals",
    )

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)

    @classmethod
    def generate_referral_code(cls):
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = "".join(secrets.choice(alphabet) for _ in range(8))
            if not cls.objects.filter(referral_code=code).exists():
                return code


class DailyVerse(models.Model):
    verse_text = models.TextField()
    reference = models.CharField(max_length=100)
    date = models.DateField(unique=True)

    def __str__(self):
        return f"{self.reference} - {self.date}"


class DailyDevotional(models.Model):
    title = models.CharField(max_length=160)
    scripture_reference = models.CharField(max_length=120)
    scripture_text = models.TextField()
    reflection = models.TextField()
    prayer_prompt = models.TextField()
    journal_prompt = models.TextField()
    date = models.DateField(unique=True)
    season = models.CharField(max_length=80, blank=True)

    class Meta:
        ordering = ("-date",)

    def __str__(self):
        return f"{self.title} - {self.date}"


class PrayerLog(models.Model):
    class Category(models.TextChoices):
        THANKSGIVING = "thanksgiving", "Thanksgiving"
        CONFESSION = "confession", "Confession"
        PETITION = "petition", "Petition"
        INTERCESSION = "intercession", "Intercession"
        HEALING = "healing", "Healing"
        FAMILY = "family", "Family"
        WORK_SCHOOL = "work_school", "Work or School"
        NATION = "nation", "Nation"
        CHURCH = "church", "Church"
        ANSWERED_PRAYER = "answered_prayer", "Answered Prayer"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.PETITION,
    )
    content = models.TextField()
    date = models.DateField(auto_now_add=True)
    is_answered = models.BooleanField(default=False)
    testimony_note = models.TextField(blank=True)
    testimony_notes = models.TextField(blank=True)
    verse_tag = models.CharField(max_length=200, blank=True)
    verse_reference = models.CharField(max_length=120, blank=True)
    verse_tags = models.CharField(
        max_length=240,
        blank=True,
        help_text="Comma-separated verse or theme tags for this journal entry.",
    )

    class Meta:
        unique_together = ("user", "date")

    def __str__(self):
        return f"{self.user} - {self.date}"


class PrayerRequest(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ANSWERED = "answered", "Answered"
        ARCHIVED = "archived", "Archived"

    class Priority(models.TextChoices):
        NORMAL = "normal", "Normal"
        URGENT = "urgent", "Urgent"
        ONGOING = "ongoing", "Ongoing"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    group = models.ForeignKey(
        "PrayerGroup",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="requests",
    )
    content = models.TextField(max_length=500)
    is_anonymous = models.BooleanField(default=True)
    prayed_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL,
    )
    testimony_notes = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    prayed_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="prayed_for",
        blank=True,
    )

    class Meta:
        ordering = ("-date",)

    def __str__(self):
        return self.content[:60]


class PrayerGroup(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_prayer_groups",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="PrayerGroupMembership",
        related_name="prayer_groups",
        blank=True,
    )
    goal_per_week = models.PositiveIntegerField(default=7)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class GroupGoal(models.Model):
    class GoalType(models.TextChoices):
        PRAYER_COUNT = "prayer_count", "Prayer count"
        MEMBER_COVERAGE = "member_coverage", "Member coverage"
        REQUEST_COVERAGE = "request_coverage", "Request coverage"

    group = models.ForeignKey(
        PrayerGroup,
        related_name="goals",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=160)
    goal_type = models.CharField(
        max_length=30,
        choices=GoalType.choices,
        default=GoalType.PRAYER_COUNT,
    )
    target_count = models.PositiveIntegerField(default=30)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-is_active", "end_date")

    def __str__(self):
        return self.title


class PrayerGroupMembership(models.Model):
    group = models.ForeignKey(PrayerGroup, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("group", "user")

    def __str__(self):
        return f"{self.user} in {self.group}"


class PrayerReminder(models.Model):
    class Routine(models.TextChoices):
        MORNING = "morning", "Morning"
        MIDDAY = "midday", "Midday"
        EVENING = "evening", "Evening"
        CUSTOM = "custom", "Custom"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="prayer_reminders",
    )
    routine = models.CharField(
        max_length=20,
        choices=Routine.choices,
        default=Routine.MORNING,
    )
    label = models.CharField(max_length=120, blank=True)
    time = models.TimeField()
    is_active = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("time",)

    def __str__(self):
        return self.label or self.get_routine_display()


class PushSubscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="push_subscriptions",
    )
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    user_agent = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)

    def __str__(self):
        return f"{self.user} push subscription"


class ReminderDelivery(models.Model):
    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        PUSH = "push", "Push"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reminder = models.ForeignKey(
        PrayerReminder,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    channel = models.CharField(max_length=10, choices=Channel.choices)
    sent_for_date = models.DateField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "reminder", "channel", "sent_for_date")
        ordering = ("-sent_at",)

    def __str__(self):
        return f"{self.user} {self.channel} reminder on {self.sent_for_date}"


class PrayerPlan(models.Model):
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    days = models.PositiveIntegerField(default=7)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("title",)

    def __str__(self):
        return self.title


class PrayerPlanDay(models.Model):
    plan = models.ForeignKey(
        PrayerPlan,
        on_delete=models.CASCADE,
        related_name="plan_days",
    )
    day_number = models.PositiveIntegerField()
    title = models.CharField(max_length=160)
    prompt = models.TextField()
    verse_reference = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ("plan", "day_number")
        unique_together = ("plan", "day_number")

    def __str__(self):
        return f"{self.plan} day {self.day_number}"


class UserPrayerPlan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(PrayerPlan, on_delete=models.CASCADE)
    started_at = models.DateField(auto_now_add=True)
    current_day = models.PositiveIntegerField(default=1)
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "plan")

    def __str__(self):
        return f"{self.user} - {self.plan}"


class BibleBook(models.Model):
    name = models.CharField(max_length=80, unique=True)
    abbreviation = models.CharField(max_length=12, unique=True)
    testament = models.CharField(max_length=30, blank=True)
    total_chapters = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "name")

    def __str__(self):
        return self.name


class BibleChapter(models.Model):
    book = models.ForeignKey(
        BibleBook,
        on_delete=models.CASCADE,
        related_name="chapters",
    )
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=160, blank=True)
    text = models.TextField()

    class Meta:
        ordering = ("book__sort_order", "number")
        unique_together = ("book", "number")

    def __str__(self):
        return f"{self.book.name} {self.number}"


class BibleReadingProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    chapter = models.ForeignKey(BibleChapter, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-completed_at",)
        unique_together = ("user", "chapter")

    def __str__(self):
        return f"{self.user} read {self.chapter}"


class BibleReadingPlan(models.Model):
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    days = models.PositiveIntegerField(default=7)
    theme = models.CharField(max_length=80, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("title",)

    def __str__(self):
        return self.title


class BibleReadingPlanDay(models.Model):
    plan = models.ForeignKey(
        BibleReadingPlan,
        related_name="plan_days",
        on_delete=models.CASCADE,
    )
    day_number = models.PositiveIntegerField()
    title = models.CharField(max_length=160)
    passage_reference = models.CharField(max_length=120)
    passage_text = models.TextField(blank=True)
    reflection = models.TextField(blank=True)
    prayer_prompt = models.TextField(blank=True)

    class Meta:
        ordering = ("plan", "day_number")
        unique_together = ("plan", "day_number")

    def __str__(self):
        return f"{self.plan} day {self.day_number}"


class UserBibleReadingPlan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(BibleReadingPlan, on_delete=models.CASCADE)
    started_at = models.DateField(auto_now_add=True)
    current_day = models.PositiveIntegerField(default=1)
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "plan")

    def __str__(self):
        return f"{self.user} - {self.plan}"


class BibleReadingPlanProgress(models.Model):
    user_plan = models.ForeignKey(
        UserBibleReadingPlan,
        related_name="completed_days",
        on_delete=models.CASCADE,
    )
    plan_day = models.ForeignKey(BibleReadingPlanDay, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-completed_at",)
        unique_together = ("user_plan", "plan_day")

    def __str__(self):
        return f"{self.user_plan.user} completed {self.plan_day}"


class StreakLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()

    class Meta:
        unique_together = ("user", "date")

    def __str__(self):
        return f"{self.user} - {self.date}"


class Referral(models.Model):
    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="referrals_made",
    )
    referred_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="referral_record",
    )
    date = models.DateTimeField(auto_now_add=True)
    points_awarded = models.IntegerField(default=100)

    def __str__(self):
        return f"{self.referrer} referred {self.referred_user}"


class Donation(models.Model):
    class Method(models.TextChoices):
        GCASH = "GCash", "GCash"
        BPI = "BPI", "BPI"
        OTHERS = "Others", "Others"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    donor_name = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference_number = models.CharField(max_length=100)
    method = models.CharField(max_length=20, choices=Method.choices)
    date = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    is_recurring = models.BooleanField(default=False)
    receipt_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.donor_name or self.user or 'Anonymous'} - {self.amount}"


class PublicTestimony(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    title = models.CharField(max_length=160)
    content = models.TextField(max_length=1000)
    is_anonymous = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    amen_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="amen_testimonies",
        blank=True,
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.title


class Family(models.Model):
    name = models.CharField(max_length=100)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="families_created",
        on_delete=models.CASCADE,
    )
    invite_code = models.CharField(max_length=8, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)

    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = User.generate_referral_code()
            while Family.objects.filter(invite_code=self.invite_code).exists():
                self.invite_code = User.generate_referral_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class FamilyMember(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"

    family = models.ForeignKey(
        Family,
        related_name="members",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="family_memberships",
        on_delete=models.CASCADE,
    )
    nickname = models.CharField(max_length=50, blank=True)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER,
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("family", "user")

    def __str__(self):
        return f"{self.user} in {self.family}"


class FamilyPrayerRequest(models.Model):
    family = models.ForeignKey(
        Family,
        related_name="prayer_requests",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField(max_length=500)
    prayed_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="family_prayers_prayed",
        blank=True,
    )
    date = models.DateTimeField(auto_now_add=True)
    is_answered = models.BooleanField(default=False)

    class Meta:
        ordering = ("-date",)

    def __str__(self):
        return self.content[:60]
