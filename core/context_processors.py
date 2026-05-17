def user_preferences(request):
    if request.user.is_authenticated:
        return {
            "senior_mode": request.user.senior_mode,
            "has_family": request.user.family_memberships.exists(),
        }
    return {"senior_mode": False, "has_family": False}
