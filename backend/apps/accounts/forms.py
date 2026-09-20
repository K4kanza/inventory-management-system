"""User creation form."""

from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    role = forms.ChoiceField(choices=User.Role.choices)

    class Meta:
        model = User
        fields = ["username", "email", "role"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class SettingForm(forms.Form):
    key = forms.SlugField(
        max_length=100, label="Setting key", help_text="Lowercase slug, e.g. low_stock_email"
    )
    value = forms.CharField(max_length=2000, required=False)
    description = forms.CharField(max_length=255, required=False)
