from django.urls import path

from . import views


urlpatterns = [
    path("", views.home_view, name="home"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("donate/", views.donate_view, name="donate"),
    path("invite/", views.invite_view, name="invite"),
    path("leaderboard/", views.leaderboard_view, name="leaderboard"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
]
