from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from .models import Donation, PrayerReminder, PrayerRequest


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = get_user_model()
        fields = ("username", "email", "password1", "password2")


class DonationForm(forms.ModelForm):
    class Meta:
        model = Donation
        fields = ("donor_name", "amount", "reference_number", "method", "note")
        widgets = {
            "donor_name": forms.TextInput(
                attrs={
                    "class": "w-full rounded-xl border border-amber-100 px-4 py-3 text-ps-blue outline-none transition focus:border-ps-gold focus:ring-2 focus:ring-amber-100",
                    "placeholder": "Your name",
                }
            ),
            "amount": forms.NumberInput(
                attrs={
                    "class": "w-full rounded-xl border border-amber-100 px-4 py-3 text-ps-blue outline-none transition focus:border-ps-gold focus:ring-2 focus:ring-amber-100",
                    "placeholder": "e.g. 100",
                    "min": "1",
                    "step": "0.01",
                }
            ),
            "reference_number": forms.TextInput(
                attrs={
                    "class": "w-full rounded-xl border border-amber-100 px-4 py-3 text-ps-blue outline-none transition focus:border-ps-gold focus:ring-2 focus:ring-amber-100",
                    "placeholder": "Payment reference number",
                }
            ),
            "method": forms.Select(
                attrs={
                    "class": "w-full rounded-xl border border-amber-100 px-4 py-3 text-ps-blue outline-none transition focus:border-ps-gold focus:ring-2 focus:ring-amber-100",
                }
            ),
            "note": forms.Textarea(
                attrs={
                    "class": "w-full resize-none rounded-xl border border-amber-100 px-4 py-3 text-ps-blue outline-none transition focus:border-ps-gold focus:ring-2 focus:ring-amber-100",
                    "placeholder": "Optional note",
                    "rows": 4,
                }
            ),
        }


class PrayerRequestForm(forms.ModelForm):
    class Meta:
        model = PrayerRequest
        fields = ("content", "priority", "follow_up_date", "is_anonymous", "group")
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "w-full resize-none rounded-xl border border-[#DDD5C0] bg-[#FDFAF4] px-4 py-3 text-ps-blue outline-none transition placeholder:text-[#6B5B3E] focus:border-ps-gold focus:ring-2 focus:ring-[#DDD5C0]",
                    "placeholder": "Share your prayer request...",
                    "rows": 5,
                    "maxlength": 500,
                }
            ),
            "priority": forms.Select(
                attrs={
                    "class": "w-full rounded-xl border border-[#DDD5C0] bg-[#FDFAF4] px-4 py-3 text-ps-blue outline-none transition focus:border-ps-gold focus:ring-2 focus:ring-[#DDD5C0]",
                }
            ),
            "follow_up_date": forms.DateInput(
                attrs={
                    "class": "w-full rounded-xl border border-[#DDD5C0] bg-[#FDFAF4] px-4 py-3 text-ps-blue outline-none transition focus:border-ps-gold focus:ring-2 focus:ring-[#DDD5C0]",
                    "type": "date",
                }
            ),
            "group": forms.Select(
                attrs={
                    "class": "w-full rounded-xl border border-[#DDD5C0] bg-[#FDFAF4] px-4 py-3 text-ps-blue outline-none transition focus:border-ps-gold focus:ring-2 focus:ring-[#DDD5C0]",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["is_anonymous"].required = False
        self.fields["is_anonymous"].initial = True
        self.fields["group"].required = False
        if user is not None:
            self.fields["group"].queryset = user.prayer_groups.all()


class PrayerReminderForm(forms.ModelForm):
    class Meta:
        model = PrayerReminder
        fields = ("routine", "label", "time", "email_enabled", "push_enabled", "is_active")
        widgets = {
            "routine": forms.Select(
                attrs={
                    "class": "w-full rounded-xl border border-[#DDD5C0] bg-[#FDFAF4] px-4 py-3 text-ps-blue outline-none transition focus:border-ps-gold focus:ring-2 focus:ring-[#DDD5C0]",
                }
            ),
            "label": forms.TextInput(
                attrs={
                    "class": "w-full rounded-xl border border-[#DDD5C0] bg-[#FDFAF4] px-4 py-3 text-ps-blue outline-none transition focus:border-ps-gold focus:ring-2 focus:ring-[#DDD5C0]",
                    "placeholder": "Morning prayer",
                }
            ),
            "time": forms.TimeInput(
                attrs={
                    "class": "w-full rounded-xl border border-[#DDD5C0] bg-[#FDFAF4] px-4 py-3 text-ps-blue outline-none transition focus:border-ps-gold focus:ring-2 focus:ring-[#DDD5C0]",
                    "type": "time",
                }
            ),
        }
