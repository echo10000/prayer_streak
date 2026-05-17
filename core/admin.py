from datetime import timedelta

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.db import IntegrityError

from .models import (
    BibleBook,
    BibleChapter,
    BibleReadingProgress,
    DailyDevotional,
    DailyVerse,
    Donation,
    Family,
    FamilyMember,
    FamilyPrayerRequest,
    GroupGoal,
    BibleReadingPlan,
    BibleReadingPlanDay,
    BibleReadingPlanProgress,
    PrayerGroup,
    PrayerGroupMembership,
    PrayerLog,
    PrayerPlan,
    PrayerPlanDay,
    PrayerRequest,
    PrayerReminder,
    PublicTestimony,
    PushSubscription,
    ReminderDelivery,
    Referral,
    StreakLog,
    UserPrayerPlan,
    UserBibleReadingPlan,
    User,
)


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
                    "streak_freezes",
                    "grace_days_used",
                    "sabbath_mode",
                    "dark_mode",
                    "reminder_email_enabled",
                    "reminder_push_enabled",
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
                    "streak_freezes",
                    "grace_days_used",
                    "sabbath_mode",
                    "dark_mode",
                    "reminder_email_enabled",
                    "reminder_push_enabled",
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
        "streak_freezes",
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


@admin.register(DailyDevotional)
class DailyDevotionalAdmin(admin.ModelAdmin):
    list_display = ("date", "title", "scripture_reference", "season")
    list_filter = ("season", "date")
    search_fields = ("title", "scripture_reference", "scripture_text", "reflection")
    ordering = ("-date",)


@admin.register(PrayerLog)
class PrayerLogAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "category", "is_answered", "verse_reference", "content_preview")
    list_filter = ("category", "is_answered", "date")
    search_fields = ("user__username", "content", "verse_reference", "verse_tags")

    @admin.display(description="Content preview")
    def content_preview(self, obj):
        return obj.content[:60]


@admin.register(PrayerRequest)
class PrayerRequestAdmin(admin.ModelAdmin):
    list_display = (
        "date",
        "short_content",
        "status",
        "priority",
        "is_anonymous",
        "group",
        "prayed_count",
        "is_active",
    )
    list_editable = ("status", "priority", "is_active")
    list_filter = ("status", "priority", "is_anonymous", "is_active", "group")
    search_fields = ("content", "user__username")

    @admin.display(description="Content preview")
    def short_content(self, obj):
        return obj.content[:60]


class PrayerPlanDayInline(admin.TabularInline):
    model = PrayerPlanDay
    extra = 1


class PrayerGroupMembershipInline(admin.TabularInline):
    model = PrayerGroupMembership
    extra = 1


@admin.register(PrayerGroup)
class PrayerGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "goal_per_week", "created_at")
    search_fields = ("name", "owner__username")
    inlines = (PrayerGroupMembershipInline,)


@admin.register(GroupGoal)
class GroupGoalAdmin(admin.ModelAdmin):
    list_display = ("title", "group", "goal_type", "target_count", "start_date", "end_date", "is_active")
    list_filter = ("goal_type", "is_active", "group")
    search_fields = ("title", "group__name")


@admin.register(PrayerReminder)
class PrayerReminderAdmin(admin.ModelAdmin):
    list_display = ("user", "routine", "label", "time", "is_active", "email_enabled", "push_enabled")
    list_filter = ("routine", "is_active", "email_enabled", "push_enabled")
    search_fields = ("user__username", "label")


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("user__username", "endpoint")


@admin.register(ReminderDelivery)
class ReminderDeliveryAdmin(admin.ModelAdmin):
    list_display = ("user", "reminder", "channel", "sent_for_date", "sent_at")
    list_filter = ("channel", "sent_for_date")
    search_fields = ("user__username",)


@admin.register(PrayerPlan)
class PrayerPlanAdmin(admin.ModelAdmin):
    list_display = ("title", "days", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "description")
    inlines = (PrayerPlanDayInline,)


@admin.register(UserPrayerPlan)
class UserPrayerPlanAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "started_at", "current_day", "is_completed")
    list_filter = ("plan", "is_completed")
    search_fields = ("user__username", "plan__title")


class BibleReadingPlanDayInline(admin.TabularInline):
    model = BibleReadingPlanDay
    extra = 1


@admin.register(BibleReadingPlan)
class BibleReadingPlanAdmin(admin.ModelAdmin):
    list_display = ("title", "days", "theme", "is_active")
    list_filter = ("theme", "is_active")
    search_fields = ("title", "description")
    inlines = (BibleReadingPlanDayInline,)


@admin.register(UserBibleReadingPlan)
class UserBibleReadingPlanAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "started_at", "current_day", "is_completed")
    list_filter = ("plan", "is_completed")
    search_fields = ("user__username", "plan__title")


@admin.register(BibleReadingPlanProgress)
class BibleReadingPlanProgressAdmin(admin.ModelAdmin):
    list_display = ("user_plan", "plan_day", "completed_at")
    list_filter = ("plan_day__plan",)


@admin.register(BibleBook)
class BibleBookAdmin(admin.ModelAdmin):
    list_display = ("name", "abbreviation", "testament", "total_chapters", "sort_order")
    search_fields = ("name", "abbreviation")


@admin.register(BibleChapter)
class BibleChapterAdmin(admin.ModelAdmin):
    list_display = ("book", "number", "title")
    list_filter = ("book",)
    search_fields = ("book__name", "title", "text")


@admin.register(BibleReadingProgress)
class BibleReadingProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "chapter", "completed_at")
    list_filter = ("chapter__book", "completed_at")
    search_fields = ("user__username", "chapter__book__name")


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
        "is_recurring",
        "receipt_sent",
        "date",
    )
    list_filter = ("method", "is_verified", "is_recurring", "receipt_sent")
    list_editable = ("is_verified", "receipt_sent")
    search_fields = ("donor_name", "reference_number")
    actions = (mark_selected_as_verified,)


@admin.register(PublicTestimony)
class PublicTestimonyAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "is_anonymous", "is_approved", "created_at", "amen_count")
    list_filter = ("is_approved", "is_anonymous")
    list_editable = ("is_approved",)
    search_fields = ("title", "content", "user__username")

    @admin.display(description="Amen")
    def amen_count(self, obj):
        return obj.amen_by.count()


class FamilyMemberInline(admin.TabularInline):
    model = FamilyMember
    extra = 1


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by", "invite_code", "created_at")
    search_fields = ("name", "invite_code", "created_by__username")
    inlines = (FamilyMemberInline,)


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ("family", "user", "nickname", "role", "joined_at")
    list_filter = ("role", "family")
    search_fields = ("family__name", "user__username", "nickname")


@admin.register(FamilyPrayerRequest)
class FamilyPrayerRequestAdmin(admin.ModelAdmin):
    list_display = ("family", "user", "is_answered", "date", "content_preview")
    list_filter = ("is_answered", "family")
    search_fields = ("content", "family__name", "user__username")

    @admin.display(description="Content preview")
    def content_preview(self, obj):
        return obj.content[:60]
