from datetime import timedelta

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.db import IntegrityError

from .models import DailyVerse, Donation, PrayerLog, Referral, StreakLog, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "PrayerStreak",
            {
                "fields": (
                    "referral_code",
                    "points",
                    "streak",
                    "last_active",
                    "referred_by",
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "PrayerStreak",
            {
                "fields": (
                    "referral_code",
                    "points",
                    "streak",
                    "last_active",
                    "referred_by",
                )
            },
        ),
    )
    list_display = (
        "username",
        "email",
        "points",
        "streak",
        "referral_code",
        "last_active",
        "date_joined",
    )
    search_fields = ("username", "email")
    list_filter = ("date_joined",)
    readonly_fields = ("referral_code", "referred_by")


@admin.action(description="Duplicate verse to tomorrow")
def duplicate_verse_to_tomorrow(modeladmin, request, queryset):
    created_count = 0
    skipped_count = 0

    for verse in queryset:
        try:
            DailyVerse.objects.create(
                verse_text=verse.verse_text,
                reference=verse.reference,
                date=verse.date + timedelta(days=1),
            )
            created_count += 1
        except IntegrityError:
            skipped_count += 1

    if created_count:
        messages.success(request, f"Duplicated {created_count} verse(s) to tomorrow.")
    if skipped_count:
        messages.warning(
            request,
            f"Skipped {skipped_count} verse(s) because tomorrow already has a verse.",
        )


@admin.register(DailyVerse)
class DailyVerseAdmin(admin.ModelAdmin):
    list_display = ("date", "reference", "verse_preview")
    ordering = ("-date",)
    actions = (duplicate_verse_to_tomorrow,)

    @admin.display(description="Verse preview")
    def verse_preview(self, obj):
        return obj.verse_text[:60]


@admin.register(PrayerLog)
class PrayerLogAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "is_answered", "content_preview")
    list_filter = ("is_answered", "date")
    search_fields = ("user__username",)

    @admin.display(description="Content preview")
    def content_preview(self, obj):
        return obj.content[:60]


@admin.register(StreakLog)
class StreakLogAdmin(admin.ModelAdmin):
    list_display = ("user", "date")
    list_filter = ("date",)


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ("referrer", "referred_user", "date", "points_awarded")
    search_fields = ("referrer__username",)


@admin.action(description="Mark selected as verified")
def mark_selected_as_verified(modeladmin, request, queryset):
    updated_count = queryset.update(is_verified=True)
    messages.success(request, f"Marked {updated_count} donation(s) as verified.")


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = (
        "donor_name",
        "amount",
        "method",
        "reference_number",
        "is_verified",
        "date",
    )
    list_filter = ("method", "is_verified")
    list_editable = ("is_verified",)
    search_fields = ("donor_name", "reference_number")
    actions = (mark_selected_as_verified,)
