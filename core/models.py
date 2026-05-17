import secrets
import string

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    referral_code = models.CharField(max_length=8, unique=True, blank=True)
    points = models.IntegerField(default=0)
    streak = models.IntegerField(default=0)
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

    class Meta:
        unique_together = ("user", "date")

    def __str__(self):
        return f"{self.user} - {self.date}"


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

    def __str__(self):
        return f"{self.donor_name or self.user or 'Anonymous'} - {self.amount}"
