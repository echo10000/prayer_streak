import os
import csv
import calendar
from datetime import date, datetime, timedelta
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db import IntegrityError, transaction
from django.db.models import Count, F, Q, Sum
from django.http import FileResponse, HttpResponse, JsonResponse
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import DonationForm, PrayerReminderForm, PrayerRequestForm, RegisterForm
from .models import (
    BibleBook,
    BibleChapter,
    BibleReadingPlan,
    BibleReadingPlanDay,
    BibleReadingPlanProgress,
    BibleReadingProgress,
    DailyDevotional,
    DailyVerse,
    Family,
    FamilyMember,
    FamilyPrayerRequest,
    GroupGoal,
    PrayerLog,
    PrayerGroup,
    PrayerRequest,
    PrayerReminder,
    PublicTestimony,
    PushSubscription,
    PrayerPlan,
    UserBibleReadingPlan,
    UserPrayerPlan,
    Referral,
    StreakLog,
)
from .utils import update_streak


def service_worker(request):
    sw_path = os.path.join(settings.BASE_DIR, "core", "static", "core", "sw.js")
    return FileResponse(open(sw_path, "rb"), content_type="application/javascript")


def home_view(request):
    return render(request, "core/index.html")


def build_prayer_stats(user, today):
    prayer_dates = set(
        PrayerLog.objects.filter(user=user).values_list("date", flat=True)
    )
    streak_dates = set(
        StreakLog.objects.filter(user=user).values_list("date", flat=True)
    )
    all_dates = prayer_dates | streak_dates
    total_days = len(all_dates)
    last_30_days = [today - timedelta(days=offset) for offset in range(29, -1, -1)]
    missed_days = sum(1 for day in last_30_days if day not in all_dates)
    heatmap_days = [
        {"date": day, "prayed": day in all_dates}
        for day in [today - timedelta(days=offset) for offset in range(41, -1, -1)]
    ]

    longest_streak = 0
    current_run = 0
    previous_day = None
    for day in sorted(all_dates):
        if previous_day and day == previous_day + timedelta(days=1):
            current_run += 1
        else:
            current_run = 1
        longest_streak = max(longest_streak, current_run)
        previous_day = day

    month_counts = {}
    for day in all_dates:
        month_key = day.strftime("%B %Y")
        month_counts[month_key] = month_counts.get(month_key, 0) + 1
    best_month = max(month_counts.items(), key=lambda item: item[1], default=(None, 0))

    prompts = [
        "Pray for someone who feels unseen today.",
        "Pray for your family and the conversations around your table.",
        "Pray for healing where there has been weariness.",
        "Pray with gratitude for one specific mercy from this week.",
        "Pray for guidance in one decision you have been carrying.",
        "Pray for your church and local community.",
        "Pray for the Philippines with hope and patience.",
    ]

    return {
        "longest_streak": longest_streak,
        "current_streak": user.streak,
        "total_prayer_days": total_days,
        "missed_days": missed_days,
        "best_month_name": best_month[0] or "Not yet",
        "best_month_days": best_month[1],
        "heatmap_days": heatmap_days,
        "rotating_prompt": prompts[today.toordinal() % len(prompts)],
    }


def send_push_to_user(user, title, body, url="/dashboard/"):
    if not settings.VAPID_PUBLIC_KEY or not settings.VAPID_PRIVATE_KEY:
        return 0
    try:
        from pywebpush import WebPushException, webpush
    except ImportError:
        return 0

    sent_count = 0
    for subscription in PushSubscription.objects.filter(user=user, is_active=True):
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
                },
                data=json.dumps({"title": title, "body": body, "url": url}),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": f"mailto:{settings.VAPID_ADMIN_EMAIL}"},
            )
            sent_count += 1
        except WebPushException as exc:
            if getattr(exc.response, "status_code", None) in {404, 410}:
                subscription.is_active = False
                subscription.save(update_fields=["is_active"])
    return sent_count


def register_view(request):
    ref_code = request.GET.get("ref") or request.POST.get("ref")
    referrer = None

    if ref_code:
        referrer = get_user_model().objects.filter(referral_code=ref_code).first()

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                if referrer:
                    user.referred_by = referrer
                user.save()

                if referrer:
                    Referral.objects.create(
                        referrer=referrer,
                        referred_user=user,
                        points_awarded=100,
                    )
                    get_user_model().objects.filter(pk=referrer.pk).update(
                        points=F("points") + 100
                    )
                    messages.success(request, "Welcome! Your friend invited you.")

            login(request, user)
            return redirect("/onboarding/")
        messages.error(request, "Please check the form and try again.")
    else:
        form = RegisterForm()

    return render(
        request,
        "core/register.html",
        {
            "form": form,
            "ref_code": ref_code,
            "has_referral": referrer is not None,
        },
    )


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("/dashboard/")
    else:
        form = AuthenticationForm(request)

    return render(request, "core/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("/")


@login_required(login_url="/login/")
def onboarding_view(request):
    if request.user.onboarding_complete:
        return redirect("/dashboard/")

    if request.method == "POST":
        request.user.quiet_time = request.POST.get("quiet_time") or "06:00"
        request.user.prayer_focus = request.POST.get(
            "prayer_focus",
            get_user_model().PrayerFocus.PERSONAL,
        )
        request.user.onboarding_complete = True
        request.user.save(
            update_fields=["quiet_time", "prayer_focus", "onboarding_complete"]
        )
        return redirect("/dashboard/")

    return render(request, "core/onboarding.html")


@login_required(login_url="/login/")
def dashboard_view(request):
    if not request.user.onboarding_complete:
        return redirect("/onboarding/")

    today = timezone.localdate()
    devotional = DailyDevotional.objects.filter(date=today).first()
    daily_verse = DailyVerse.objects.filter(date=today).first()
    prayer_log = PrayerLog.objects.filter(user=request.user, date=today).first()

    if request.method == "POST" and prayer_log is None:
        content = request.POST.get("content", "").strip()
        category = request.POST.get("category", PrayerLog.Category.PETITION)
        verse_reference = request.POST.get("verse_reference", "").strip()
        verse_tags = request.POST.get("verse_tags", "").strip()
        if content:
            try:
                with transaction.atomic():
                    locked_user = (
                        get_user_model()
                        .objects.select_for_update()
                        .get(pk=request.user.pk)
                    )
                    prayer_log, created = PrayerLog.objects.get_or_create(
                        user=locked_user,
                        date=today,
                        defaults={
                            "content": content,
                            "category": category,
                            "verse_reference": verse_reference,
                            "verse_tags": verse_tags,
                        },
                    )

                    if created:
                        StreakLog.objects.get_or_create(user=locked_user, date=today)
                        update_streak(locked_user)
                        get_user_model().objects.filter(pk=locked_user.pk).update(
                            points=F("points") + 20
                        )
                        messages.success(request, "Prayer logged. God hears you.")
            except IntegrityError:
                pass
            return redirect("/dashboard/")
        messages.error(request, "Please check the form and try again.")

    request.user.refresh_from_db()
    rank = (
        get_user_model()
        .objects.filter(points__gt=request.user.points)
        .count()
        + 1
    )
    total_referrals = Referral.objects.filter(referrer=request.user).count()
    answered_count = PrayerLog.objects.filter(
        user=request.user,
        is_answered=True,
    ).count()
    prayers_written = PrayerLog.objects.filter(user=request.user).count()
    recent_prayers = PrayerLog.objects.filter(user=request.user).order_by("-date")[:10]
    active_requests = PrayerRequest.objects.filter(
        Q(user=request.user) | Q(group__members=request.user),
        status=PrayerRequest.Status.ACTIVE,
    ).distinct()[:5]
    recent_answered_requests = PrayerRequest.objects.filter(
        Q(user=request.user) | Q(group__members=request.user),
        status=PrayerRequest.Status.ANSWERED,
    ).distinct()[:5]
    reminders = PrayerReminder.objects.filter(user=request.user, is_active=True)[:3]
    prayer_stats = build_prayer_stats(request.user, today)
    active_plan = (
        UserPrayerPlan.objects.filter(user=request.user, is_completed=False)
        .select_related("plan")
        .first()
    )
    featured_plan = PrayerPlan.objects.filter(is_active=True).first()
    bible_book = BibleBook.objects.filter(abbreviation="John").first()
    bible_progress = None
    next_bible_chapter = None

    if bible_book:
        completed_chapter_ids = BibleReadingProgress.objects.filter(
            user=request.user,
            chapter__book=bible_book,
        ).values_list("chapter_id", flat=True)
        completed_count = len(completed_chapter_ids)
        bible_progress = {
            "book": bible_book,
            "completed_count": completed_count,
            "total_chapters": bible_book.total_chapters,
            "percent": round((completed_count / bible_book.total_chapters) * 100)
            if bible_book.total_chapters
            else 0,
        }
        next_bible_chapter = (
            bible_book.chapters.exclude(id__in=completed_chapter_ids)
            .order_by("number")
            .first()
        )

    context = {
        "devotional": devotional,
        "daily_verse": daily_verse,
        "today_verse_text": devotional.scripture_text if devotional else (daily_verse.verse_text if daily_verse else "The Lord is near to all who call on him, to all who call on him in truth."),
        "today_verse_reference": devotional.scripture_reference if devotional else (daily_verse.reference if daily_verse else "Psalm 145:18"),
        "prayer_categories": PrayerLog.Category.choices,
        "fallback_verse_text": "The Lord is near to all who call on him, to all who call on him in truth.",
        "fallback_verse_reference": "Psalm 145:18",
        "fallback_reflection": "Prayer is not a performance. It is returning to the Father who is already near. Take a quiet moment today to name what you are carrying, receive God's nearness, and offer your day back to Him.",
        "fallback_prayer_prompt": "Lord, draw my heart close to You today. Teach me to trust Your presence in ordinary moments, and help me love my family, neighbors, and country with patience and grace.",
        "fallback_journal_prompt": "Where do I need to become still and trust God today?",
        "prayer_log": prayer_log,
        "recent_prayers": recent_prayers,
        "active_requests": active_requests,
        "recent_answered_requests": recent_answered_requests,
        "reminders": reminders,
        "prayer_stats": prayer_stats,
        "active_plan": active_plan,
        "featured_plan": featured_plan,
        "bible_progress": bible_progress,
        "next_bible_chapter": next_bible_chapter,
        "rank": rank,
        "total_referrals": total_referrals,
        "answered_count": answered_count,
        "prayers_written": prayers_written,
        "today": today,
    }
    return render(request, "core/dashboard.html", context)


@login_required(login_url="/login/")
def bible_book_view(request, abbreviation="John"):
    book = get_object_or_404(BibleBook, abbreviation__iexact=abbreviation)
    chapters = list(book.chapters.all())
    completed_chapter_ids = set(
        BibleReadingProgress.objects.filter(
            user=request.user,
            chapter__book=book,
        ).values_list("chapter_id", flat=True)
    )
    completed_count = len(completed_chapter_ids)
    current_chapter = next(
        (chapter for chapter in chapters if chapter.id not in completed_chapter_ids),
        chapters[-1] if chapters else None,
    )

    if request.method == "POST":
        chapter_id = request.POST.get("chapter_id")
        chapter = get_object_or_404(BibleChapter, pk=chapter_id, book=book)
        progress, created = BibleReadingProgress.objects.get_or_create(
            user=request.user,
            chapter=chapter,
        )
        if created:
            get_user_model().objects.filter(pk=request.user.pk).update(
                points=F("points") + 10
            )
            messages.success(
                request,
                f"Marked {chapter} as read. Keep going, one chapter at a time.",
            )
        return redirect("bible_book", abbreviation=book.abbreviation)

    total_chapters = len(chapters)
    completed_chapters = {chapter.number for chapter in chapters if chapter.id in completed_chapter_ids}
    next_chapter = next(
        (chapter for chapter in chapters if chapter.number not in completed_chapters),
        None,
    )
    context = {
        "book": book,
        "chapters": chapters,
        "completed_chapter_ids": completed_chapter_ids,
        "completed_chapters": completed_chapters,
        "completed_count": completed_count,
        "next_chapter": next_chapter,
        "next_chapter_url": f"#chapter-{next_chapter.number}" if next_chapter else "",
        "progress_percent": int((completed_count / total_chapters) * 100)
        if total_chapters
        else 0,
        "total_chapters": total_chapters,
        "current_chapter": current_chapter,
    }
    return render(request, "core/bible_book.html", context)


@login_required(login_url="/login/")
def bible_plans_view(request):
    plans = BibleReadingPlan.objects.filter(is_active=True).prefetch_related("plan_days")
    user_plans = {
        user_plan.plan_id: user_plan
        for user_plan in UserBibleReadingPlan.objects.filter(user=request.user)
    }
    return render(
        request,
        "core/bible_plans.html",
        {"plans": plans, "user_plans": user_plans},
    )


@login_required(login_url="/login/")
def bible_plan_detail_view(request, pk):
    plan = get_object_or_404(BibleReadingPlan, pk=pk, is_active=True)
    user_plan = UserBibleReadingPlan.objects.filter(
        user=request.user,
        plan=plan,
    ).first()
    completed_day_ids = set()
    if user_plan:
        completed_day_ids = set(
            user_plan.completed_days.values_list("plan_day_id", flat=True)
        )
    return render(
        request,
        "core/bible_plan_detail.html",
        {
            "plan": plan,
            "user_plan": user_plan,
            "completed_day_ids": completed_day_ids,
            "completed_count": len(completed_day_ids),
        },
    )


@login_required(login_url="/login/")
@require_POST
def start_bible_plan_view(request, pk):
    plan = get_object_or_404(BibleReadingPlan, pk=pk, is_active=True)
    UserBibleReadingPlan.objects.get_or_create(user=request.user, plan=plan)
    messages.success(request, "Bible reading plan started.")
    return redirect("bible_plan_detail", pk=plan.pk)


@login_required(login_url="/login/")
@require_POST
def complete_bible_plan_day_view(request, pk, day_pk):
    plan = get_object_or_404(BibleReadingPlan, pk=pk, is_active=True)
    plan_day = get_object_or_404(BibleReadingPlanDay, pk=day_pk, plan=plan)
    user_plan, _ = UserBibleReadingPlan.objects.get_or_create(
        user=request.user,
        plan=plan,
    )
    BibleReadingPlanProgress.objects.get_or_create(
        user_plan=user_plan,
        plan_day=plan_day,
    )
    completed_count = user_plan.completed_days.count()
    user_plan.current_day = min(completed_count + 1, plan.days)
    user_plan.is_completed = completed_count >= plan.days
    user_plan.save(update_fields=["current_day", "is_completed"])
    messages.success(request, "Reading marked complete.")
    return redirect("bible_plan_detail", pk=plan.pk)


@login_required(login_url="/login/")
@require_POST
def mark_answered_view(request, pk):
    prayer_log = get_object_or_404(PrayerLog, pk=pk, user=request.user)
    if not prayer_log.is_answered:
        prayer_log.is_answered = True
    testimony_note = (
        request.POST.get("testimony_note", "").strip()
        or request.POST.get("testimony_notes", "").strip()
    )
    update_fields = ["is_answered"]
    if testimony_note:
        prayer_log.testimony_note = testimony_note
        prayer_log.testimony_notes = testimony_note
        update_fields.extend(["testimony_note", "testimony_notes"])
    prayer_log.save(update_fields=update_fields)
    messages.success(request, "Praise God! Prayer answered.")
    return redirect("journal_detail", pk=prayer_log.pk)


@login_required(login_url="/login/")
@require_POST
def simple_pray_view(request):
    today = timezone.localdate()
    try:
        with transaction.atomic():
            locked_user = (
                get_user_model().objects.select_for_update().get(pk=request.user.pk)
            )
            prayer_log, created = PrayerLog.objects.get_or_create(
                user=locked_user,
                date=today,
                defaults={
                    "content": "Prayed today",
                    "category": PrayerLog.Category.PETITION,
                },
            )
            if created:
                StreakLog.objects.get_or_create(user=locked_user, date=today)
                update_streak(locked_user)
                get_user_model().objects.filter(pk=locked_user.pk).update(
                    points=F("points") + 20
                )
                messages.success(request, "Prayer logged. God hears you.")
    except IntegrityError:
        pass
    return redirect("/dashboard/")


@login_required(login_url="/login/")
def invite_view(request):
    invite_path = f"/register/?ref={request.user.referral_code}"
    invite_link = request.build_absolute_uri(invite_path)
    referrals = (
        Referral.objects.filter(referrer=request.user)
        .select_related("referred_user")
        .order_by("-date")
    )
    total_referrals = referrals.count()
    total_referral_points = (
        referrals.aggregate(total=Sum("points_awarded"))["total"] or 0
    )

    context = {
        "invite_link": invite_link,
        "total_referrals": total_referrals,
        "total_referral_points": total_referral_points,
        "recent_referrals": referrals[:10],
    }
    return render(request, "core/invite.html", context)


def leaderboard_view(request):
    User = get_user_model()
    top_streaks = User.objects.order_by("-streak", "username")[:20]
    top_points = User.objects.order_by("-points", "username")[:20]
    current_user_streak_rank = None
    current_user_points_rank = None

    if request.user.is_authenticated:
        current_user_streak_rank = (
            User.objects.filter(streak__gt=request.user.streak).count() + 1
        )
        current_user_points_rank = (
            User.objects.filter(points__gt=request.user.points).count() + 1
        )

    context = {
        "top_streaks": top_streaks,
        "top_points": top_points,
        "current_user_streak_rank": current_user_streak_rank,
        "current_user_points_rank": current_user_points_rank,
    }
    return render(request, "core/leaderboard.html", context)


@login_required(login_url="/login/")
def analytics_view(request):
    today = timezone.localdate()
    stats = build_prayer_stats(request.user, today)
    last_30_start = today - timedelta(days=29)
    last_30_count = StreakLog.objects.filter(
        user=request.user,
        date__gte=last_30_start,
        date__lte=today,
    ).count()
    category_breakdown = (
        PrayerLog.objects.filter(user=request.user)
        .values("category")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    weekday_counts = {}
    for day in StreakLog.objects.filter(user=request.user).values_list("date", flat=True):
        weekday = day.strftime("%A")
        weekday_counts[weekday] = weekday_counts.get(weekday, 0) + 1
    best_weekday = max(weekday_counts.items(), key=lambda item: item[1], default=("Not yet", 0))

    return render(
        request,
        "core/analytics.html",
        {
            "stats": stats,
            "last_30_count": last_30_count,
            "category_breakdown": category_breakdown,
            "best_weekday": best_weekday,
            "weekday_counts": weekday_counts,
        },
    )


def filtered_journal_entries(request):
    entries = PrayerLog.objects.filter(user=request.user).order_by("-date")
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    answered = request.GET.get("answered", "").strip()
    start_date = request.GET.get("start", "").strip()
    end_date = request.GET.get("end", "").strip()
    tag = request.GET.get("tag", "").strip()

    if query:
        entries = entries.filter(
            Q(content__icontains=query)
            | Q(testimony_note__icontains=query)
            | Q(testimony_notes__icontains=query)
            | Q(verse_tag__icontains=query)
            | Q(verse_reference__icontains=query)
            | Q(verse_tags__icontains=query)
        )
    if category in PrayerLog.Category.values:
        entries = entries.filter(category=category)
    if answered == "yes":
        entries = entries.filter(is_answered=True)
    elif answered == "no":
        entries = entries.filter(is_answered=False)
    if start_date:
        entries = entries.filter(date__gte=start_date)
    if end_date:
        entries = entries.filter(date__lte=end_date)
    if tag:
        entries = entries.filter(Q(verse_tag__icontains=tag) | Q(verse_tags__icontains=tag))

    return entries


@login_required(login_url="/login/")
def journal_view(request):
    entries = filtered_journal_entries(request)
    return render(
        request,
        "core/journal.html",
        {
            "entries": entries[:100],
            "categories": PrayerLog.Category.choices,
            "selected_category": request.GET.get("category", ""),
            "answered": request.GET.get("answered", ""),
            "query": request.GET.get("q", ""),
            "start": request.GET.get("start", ""),
            "end": request.GET.get("end", ""),
            "tag": request.GET.get("tag", ""),
            "total_entries": entries.count(),
        },
    )


@login_required(login_url="/login/")
def journal_detail_view(request, pk):
    prayer_log = get_object_or_404(PrayerLog, pk=pk, user=request.user)

    if request.method == "POST":
        testimony_note = (
            request.POST.get("testimony_note", "").strip()
            or request.POST.get("testimony_notes", "").strip()
        )
        update_fields = []
        if not prayer_log.is_answered:
            prayer_log.is_answered = True
            update_fields.append("is_answered")
        if testimony_note:
            prayer_log.testimony_note = testimony_note
            prayer_log.testimony_notes = testimony_note
            update_fields.extend(["testimony_note", "testimony_notes"])
        if update_fields:
            prayer_log.save(update_fields=update_fields)
        messages.success(request, "Journal entry updated.")
        return redirect("journal_detail", pk=prayer_log.pk)

    previous_prayer = (
        PrayerLog.objects.filter(user=request.user, date__lt=prayer_log.date)
        .order_by("-date")
        .first()
    )
    next_prayer = (
        PrayerLog.objects.filter(user=request.user, date__gt=prayer_log.date)
        .order_by("date")
        .first()
    )
    verse_tag = prayer_log.verse_tag or prayer_log.verse_reference or prayer_log.verse_tags

    return render(
        request,
        "core/journal_detail.html",
        {
            "entry": prayer_log,
            "previous_prayer": previous_prayer,
            "next_prayer": next_prayer,
            "testimony_note": prayer_log.testimony_note or prayer_log.testimony_notes,
            "verse_tag": verse_tag,
        },
    )


@login_required(login_url="/login/")
def journal_export_csv_view(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="filtered-prayer-journal.csv"'
    writer = csv.writer(response)
    writer.writerow(["date", "category", "content", "answered", "testimony_note", "testimony_notes", "verse_tag", "verse_reference", "verse_tags"])
    for entry in filtered_journal_entries(request):
        writer.writerow([
            entry.date.isoformat(),
            entry.get_category_display(),
            entry.content,
            "yes" if entry.is_answered else "no",
            entry.testimony_note,
            entry.testimony_notes,
            entry.verse_tag,
            entry.verse_reference,
            entry.verse_tags,
        ])
    return response


@login_required(login_url="/login/")
def journal_export_pdf_view(request):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="prayer-journal.pdf"'
    document = SimpleDocTemplate(response, pagesize=letter, title="Prayer Journal")
    styles = getSampleStyleSheet()
    story = [Paragraph("PrayerStreak PH Journal", styles["Title"]), Spacer(1, 12)]
    for entry in filtered_journal_entries(request)[:200]:
        story.append(Paragraph(f"{entry.date:%B %d, %Y} - {entry.get_category_display()}", styles["Heading3"]))
        if entry.verse_reference:
            story.append(Paragraph(f"Verse: {entry.verse_reference}", styles["Normal"]))
        story.append(Paragraph(entry.content.replace("\n", "<br/>"), styles["BodyText"]))
        testimony = entry.testimony_note or entry.testimony_notes
        if testimony:
            story.append(Paragraph(f"Testimony: {testimony}", styles["Italic"]))
        story.append(Spacer(1, 12))
    document.build(story)
    return response


def build_month_grid(year, month):
    month_calendar = calendar.Calendar(firstweekday=6)
    weeks = []
    for week in month_calendar.monthdatescalendar(year, month):
        weeks.append([day if day.month == month else None for day in week])
    return weeks


@login_required(login_url="/login/")
def profile_view(request):
    if request.method == "POST":
        request.user.quiet_time = request.POST.get("quiet_time") or None
        request.user.prayer_focus = request.POST.get(
            "prayer_focus",
            request.user.prayer_focus,
        )
        request.user.email_reminders = request.POST.get("email_reminders") == "on"
        request.user.age_group = request.POST.get("age_group", request.user.age_group)
        request.user.senior_mode = (
            request.POST.get("senior_mode") == "on"
            or request.user.age_group == get_user_model().AgeGroup.SENIOR
        )
        request.user.save(
            update_fields=[
                "quiet_time",
                "prayer_focus",
                "email_reminders",
                "age_group",
                "senior_mode",
            ]
        )
        messages.success(request, "Profile settings saved.")
        return redirect("/profile/")

    today = timezone.localdate()
    month_param = request.GET.get("month", "")
    try:
        viewed_month = datetime.strptime(month_param, "%Y-%m").date().replace(day=1)
    except ValueError:
        viewed_month = today.replace(day=1)

    _, last_day = calendar.monthrange(viewed_month.year, viewed_month.month)
    month_start = viewed_month
    month_end = viewed_month.replace(day=last_day)
    current_month_logs = set(
        StreakLog.objects.filter(
            user=request.user,
            date__gte=month_start,
            date__lte=month_end,
        ).values_list("date", flat=True)
    )
    prev_month = (month_start - timedelta(days=1)).replace(day=1)
    next_month = (month_end + timedelta(days=1)).replace(day=1)

    total_prayers = PrayerLog.objects.filter(user=request.user).count()
    answered_prayers = PrayerLog.objects.filter(
        user=request.user,
        is_answered=True,
    ).count()

    return render(
        request,
        "core/profile.html",
        {
            "current_month_logs": current_month_logs,
            "calendar_weeks": build_month_grid(viewed_month.year, viewed_month.month),
            "current_month_name": viewed_month.strftime("%B %Y"),
            "prev_month": prev_month.strftime("%Y-%m"),
            "next_month": next_month.strftime("%Y-%m"),
            "today": today,
            "days_prayed_this_month": len(current_month_logs),
            "total_prayers": total_prayers,
            "answered_prayers": answered_prayers,
            "prayer_focus_choices": get_user_model().PrayerFocus.choices,
            "age_group_choices": get_user_model().AgeGroup.choices,
        },
    )


@login_required(login_url="/login/")
def prayer_board_view(request):
    if request.method == "POST":
        action = request.POST.get("action", "create_request")
        if action == "create_group":
            name = request.POST.get("name", "").strip()
            description = request.POST.get("description", "").strip()
            if name:
                group = PrayerGroup.objects.create(
                    name=name,
                    description=description,
                    owner=request.user,
                )
                group.members.add(request.user)
                messages.success(request, "Prayer group created.")
            return redirect("/community/")

        form = PrayerRequestForm(request.POST, user=request.user)
        if form.is_valid():
            prayer_request = form.save(commit=False)
            prayer_request.user = request.user
            prayer_request.status = PrayerRequest.Status.ACTIVE
            prayer_request.is_active = True
            prayer_request.save()
            messages.success(request, "Prayer request shared.")
            return redirect("/community/")
        messages.error(request, "Please check the form and try again.")
    else:
        form = PrayerRequestForm(user=request.user)

    today = timezone.localdate()
    status_filter = request.GET.get("status", PrayerRequest.Status.ACTIVE)
    priority_filter = request.GET.get("priority", "")
    query = request.GET.get("q", "").strip()
    prayer_requests = (
        PrayerRequest.objects.filter(
            Q(group__isnull=True) | Q(user=request.user) | Q(group__members=request.user),
        )
        .select_related("user")
        .select_related("group")
        .prefetch_related("prayed_by")
        .order_by("-date")
        .distinct()
    )
    if status_filter in PrayerRequest.Status.values:
        prayer_requests = prayer_requests.filter(status=status_filter)
    if priority_filter in PrayerRequest.Priority.values:
        prayer_requests = prayer_requests.filter(priority=priority_filter)
    if query:
        prayer_requests = prayer_requests.filter(
            Q(content__icontains=query) | Q(testimony_notes__icontains=query)
        )

    total_prayers_today = PrayerRequest.objects.filter(date__date=today).count()
    my_groups = request.user.prayer_groups.all()
    follow_up_requests = PrayerRequest.objects.filter(
        Q(user=request.user) | Q(group__members=request.user),
        follow_up_date__isnull=False,
        follow_up_date__lte=today,
        status=PrayerRequest.Status.ACTIVE,
    ).distinct()

    return render(
        request,
        "core/prayer_board.html",
        {
            "requests": prayer_requests,
            "form": form,
            "total_prayers_today": total_prayers_today,
            "status_filter": status_filter,
            "priority_filter": priority_filter,
            "query": query,
            "my_groups": my_groups,
            "follow_up_requests": follow_up_requests,
            "statuses": PrayerRequest.Status.choices,
            "priorities": PrayerRequest.Priority.choices,
        },
    )


@login_required(login_url="/login/")
@require_POST
def pray_for_view(request, pk):
    prayer_request = get_object_or_404(PrayerRequest, pk=pk, is_active=True)
    if not prayer_request.prayed_by.filter(pk=request.user.pk).exists():
        prayer_request.prayed_by.add(request.user)
        PrayerRequest.objects.filter(pk=prayer_request.pk).update(
            prayed_count=F("prayed_count") + 1,
        )
        messages.success(request, "Your intercession was counted.")
    return redirect("/community/")


@login_required(login_url="/login/")
def routine_settings_view(request):
    if request.method == "POST":
        action = request.POST.get("action", "settings")
        if action == "add_reminder":
            form = PrayerReminderForm(request.POST)
            if form.is_valid():
                reminder = form.save(commit=False)
                reminder.user = request.user
                reminder.save()
                messages.success(request, "Prayer reminder saved.")
                return redirect("/settings/")
        else:
            quiet_time = request.POST.get("quiet_time", "").strip()
            prayer_focus = request.POST.get("prayer_focus", request.user.prayer_focus)
            if prayer_focus not in get_user_model().PrayerFocus.values:
                prayer_focus = request.user.prayer_focus
            request.user.quiet_time = quiet_time or None
            request.user.prayer_focus = prayer_focus
            request.user.sabbath_mode = request.POST.get("sabbath_mode") == "on"
            request.user.dark_mode = request.POST.get("dark_mode") == "on"
            request.user.reminder_email_enabled = (
                request.POST.get("reminder_email_enabled") == "on"
            )
            request.user.reminder_push_enabled = (
                request.POST.get("reminder_push_enabled") == "on"
            )
            request.user.save(
                update_fields=[
                    "quiet_time",
                    "prayer_focus",
                    "sabbath_mode",
                    "dark_mode",
                    "reminder_email_enabled",
                    "reminder_push_enabled",
                ]
            )
            messages.success(request, "Routine settings updated.")
            return redirect("/settings/")
    else:
        form = PrayerReminderForm()

    plans = PrayerPlan.objects.filter(is_active=True)
    active_plans = UserPrayerPlan.objects.filter(user=request.user).select_related("plan")
    active_plan_map = {active_plan.plan_id: active_plan for active_plan in active_plans}
    plan_cards = [
        {
            "plan": plan,
            "active_plan": active_plan_map.get(plan.pk),
            "progress_percent": int(
                (min(active_plan_map[plan.pk].current_day, plan.days) / plan.days) * 100
            )
            if plan.pk in active_plan_map and plan.days
            else 0,
        }
        for plan in plans
    ]

    return render(
        request,
        "core/settings.html",
        {
            "form": form,
            "reminders": PrayerReminder.objects.filter(user=request.user),
            "plans": plans,
            "active_plans": active_plans,
            "plan_cards": plan_cards,
            "prayer_focus_choices": get_user_model().PrayerFocus.choices,
            "vapid_public_key": settings.VAPID_PUBLIC_KEY,
        },
    )


@login_required(login_url="/login/")
@require_POST
def save_push_subscription_view(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
        keys = payload.get("keys", {})
        endpoint = payload["endpoint"]
        p256dh = keys["p256dh"]
        auth = keys["auth"]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid subscription."}, status=400)

    PushSubscription.objects.update_or_create(
        endpoint=endpoint,
        defaults={
            "user": request.user,
            "p256dh": p256dh,
            "auth": auth,
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "is_active": True,
        },
    )
    request.user.reminder_push_enabled = True
    request.user.save(update_fields=["reminder_push_enabled"])
    return JsonResponse({"ok": True})


@login_required(login_url="/login/")
@require_POST
def delete_reminder_view(request, pk):
    PrayerReminder.objects.filter(pk=pk, user=request.user).delete()
    return redirect("/settings/")


@login_required(login_url="/login/")
@require_POST
def start_prayer_plan_view(request, pk):
    plan = get_object_or_404(PrayerPlan, pk=pk, is_active=True)
    UserPrayerPlan.objects.get_or_create(user=request.user, plan=plan)
    return redirect("/settings/")


@login_required(login_url="/login/")
def export_journal_csv_view(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="prayer-journal.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "date",
            "category",
            "content",
            "is_answered",
            "testimony_note",
            "testimony_notes",
            "verse_tag",
            "verse_reference",
            "verse_tags",
        ]
    )
    for entry in PrayerLog.objects.filter(user=request.user).order_by("date"):
        writer.writerow(
            [
                entry.date.isoformat(),
                entry.get_category_display(),
                entry.content,
                "yes" if entry.is_answered else "no",
                entry.testimony_note,
                entry.testimony_notes,
                entry.verse_tag,
                entry.verse_reference,
                entry.verse_tags,
            ]
        )
    return response


@login_required(login_url="/login/")
@require_POST
def prayer_request_status_view(request, pk):
    prayer_request = get_object_or_404(
        PrayerRequest.objects.filter(Q(user=request.user) | Q(group__members=request.user)),
        pk=pk,
    )
    status = request.POST.get("status")
    if status in PrayerRequest.Status.values:
        prayer_request.status = status
        prayer_request.is_active = status == PrayerRequest.Status.ACTIVE
    testimony_notes = request.POST.get("testimony_notes", "").strip()
    if testimony_notes:
        prayer_request.testimony_notes = testimony_notes
    prayer_request.save(update_fields=["status", "is_active", "testimony_notes"])
    if prayer_request.status == PrayerRequest.Status.ANSWERED:
        messages.success(request, "Praise God! Prayer answered.")
    return redirect("/community/")


@login_required(login_url="/login/")
def family_view(request):
    membership = (
        FamilyMember.objects.filter(user=request.user)
        .select_related("family")
        .first()
    )
    family = membership.family if membership else None

    if request.method == "POST" and family:
        content = request.POST.get("content", "").strip()
        if content:
            FamilyPrayerRequest.objects.create(
                family=family,
                user=request.user,
                content=content[:500],
            )
            messages.success(request, "Family prayer request shared.")
            return redirect("/family/")
        messages.error(request, "Please check the form and try again.")

    members = []
    prayer_requests = []
    weekly_prayers = 0
    if family:
        members = family.members.select_related("user").order_by("joined_at")
        prayer_requests = family.prayer_requests.select_related("user").prefetch_related("prayed_by")
        week_start = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
        weekly_prayers = PrayerLog.objects.filter(
            user__family_memberships__family=family,
            date__gte=week_start,
        ).distinct().count()

    return render(
        request,
        "core/family.html",
        {
            "membership": membership,
            "family": family,
            "members": members,
            "family_prayer_requests": prayer_requests,
            "weekly_prayers": weekly_prayers,
        },
    )


@login_required(login_url="/login/")
@require_POST
def create_family_view(request):
    name = request.POST.get("name", "").strip()
    if not name:
        messages.error(request, "Please check the form and try again.")
        return redirect("/family/")
    family = Family.objects.create(name=name[:100], created_by=request.user)
    FamilyMember.objects.create(
        family=family,
        user=request.user,
        role=FamilyMember.Role.ADMIN,
    )
    messages.success(request, "Family prayer group created.")
    return redirect("/family/")


@login_required(login_url="/login/")
@require_POST
def join_family_view(request):
    invite_code = request.POST.get("invite_code", "").strip().upper()
    family = Family.objects.filter(invite_code=invite_code).first()
    if not family:
        messages.error(request, "Please check the form and try again.")
        return redirect("/family/")
    FamilyMember.objects.get_or_create(family=family, user=request.user)
    messages.success(request, "Joined family prayer group.")
    return redirect("/family/")


@login_required(login_url="/login/")
@require_POST
def family_pray_view(request, pk):
    prayer_request = get_object_or_404(
        FamilyPrayerRequest.objects.filter(family__members__user=request.user),
        pk=pk,
    )
    prayer_request.prayed_by.add(request.user)
    messages.success(request, "Your intercession was counted.")
    return redirect("/family/")


@login_required(login_url="/login/")
@require_POST
def family_mark_answered_view(request, pk):
    prayer_request = get_object_or_404(
        FamilyPrayerRequest.objects.filter(family__members__user=request.user),
        pk=pk,
    )
    is_admin = FamilyMember.objects.filter(
        family=prayer_request.family,
        user=request.user,
        role=FamilyMember.Role.ADMIN,
    ).exists()
    if is_admin:
        prayer_request.is_answered = True
        prayer_request.save(update_fields=["is_answered"])
        messages.success(request, "Praise God! Prayer answered.")
    return redirect("/family/")


def donate_view(request):
    initial = {}
    if request.user.is_authenticated:
        initial["donor_name"] = request.user.get_full_name() or request.user.username

    if request.method == "POST":
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            if request.user.is_authenticated:
                donation.user = request.user
            donation.save()
            messages.success(
                request,
                "Thank you for your support.",
            )
            return redirect("/donate/")
        messages.error(request, "Please check the form and try again.")
    else:
        form = DonationForm(initial=initial)

    return render(request, "core/donate.html", {"form": form})
