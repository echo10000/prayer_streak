from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from .models import Donation


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
                    "placeholder": "500.00",
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
