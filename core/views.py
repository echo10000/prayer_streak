from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db import IntegrityError, transaction
from django.db.models import F, Sum
from django.utils import timezone
from django.shortcuts import redirect, render

from .forms import DonationForm, RegisterForm
from .models import DailyVerse, PrayerLog, Referral, StreakLog
from .utils import update_streak


def home_view(request):
    return render(request, "core/index.html")


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

            login(request, user)
            return redirect("/dashboard/")
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
def dashboard_view(request):
    today = timezone.localdate()
    daily_verse = DailyVerse.objects.filter(date=today).first()
    prayer_log = PrayerLog.objects.filter(user=request.user, date=today).first()

    if request.method == "POST" and prayer_log is None:
        content = request.POST.get("content", "").strip()
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
                        defaults={"content": content},
                    )

                    if created:
                        StreakLog.objects.get_or_create(user=locked_user, date=today)
                        update_streak(locked_user)
                        get_user_model().objects.filter(pk=locked_user.pk).update(
                            points=F("points") + 20
                        )
            except IntegrityError:
                pass
            return redirect("/dashboard/")

    request.user.refresh_from_db()
    rank = (
        get_user_model()
        .objects.filter(points__gt=request.user.points)
        .count()
        + 1
    )
    total_referrals = Referral.objects.filter(referrer=request.user).count()

    context = {
        "daily_verse": daily_verse,
        "fallback_verse_text": "The Lord is near to all who call on him, to all who call on him in truth.",
        "fallback_verse_reference": "Psalm 145:18",
        "prayer_log": prayer_log,
        "rank": rank,
        "total_referrals": total_referrals,
        "today": today,
    }
    return render(request, "core/dashboard.html", context)


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
                "\U0001F64F Thank you! Your support keeps PrayerStreak PH running.",
            )
            return redirect("/donate/")
    else:
        form = DonationForm(initial=initial)

    return render(request, "core/donate.html", {"form": form})
