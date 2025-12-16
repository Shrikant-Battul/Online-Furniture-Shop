from django import forms
from django.contrib.auth.models import User
from .models import Order
import re

PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$")

class RegistrationForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = User
        fields = ["username", "email"]

    def clean_password1(self):
        pwd = self.cleaned_data.get("password1")
        if not PASSWORD_PATTERN.match(pwd or ""):
            raise forms.ValidationError(
                "Password must be at least 8 characters and include at least one uppercase letter, one lowercase letter, and one number."
            )
        return pwd

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        # Simple uniqueness check (case-insensitive)
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        # Simple rules: min length 3, letters/digits/underscore only, unique (case-insensitive)
        if len(username) < 3:
            raise forms.ValidationError("Username must be at least 3 characters long.")
        if not re.fullmatch(r"^[A-Za-z0-9_]+$", username):
            raise forms.ValidationError("Use only letters, numbers, or underscores.")
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Passwords do not match.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    otp = forms.CharField(max_length=6, required=False)


class CheckoutForm(forms.Form):
    name = forms.CharField(max_length=150)
    phone = forms.CharField(max_length=20)
    email = forms.EmailField()
    address = forms.CharField(widget=forms.Textarea)
    city = forms.CharField(max_length=80)
    postal_code = forms.CharField(max_length=12)
    payment_method = forms.ChoiceField(choices=Order.PAYMENT_CHOICES, initial=Order.PAYMENT_COD, widget=forms.RadioSelect)
