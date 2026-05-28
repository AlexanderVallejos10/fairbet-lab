from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password

from apps.users.models import UserProfile
from apps.users.validators import validate_document_number, validate_adult_birth_date


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "w-full rounded-lg border border-slate-300 px-3 py-2",
                "placeholder": "Usuario",
                "autocomplete": "username",
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full rounded-lg border border-slate-300 px-3 py-2",
                "placeholder": "Contraseña",
                "autocomplete": "current-password",
            }
        )
    )


class RegisterForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            "class": "w-full rounded-lg border border-slate-300 px-3 py-2",
            "placeholder": "Usuario",
        }),
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            "class": "w-full rounded-lg border border-slate-300 px-3 py-2",
            "placeholder": "Correo (opcional)",
        }),
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "w-full rounded-lg border border-slate-300 px-3 py-2",
            "placeholder": "Contraseña",
        }),
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "w-full rounded-lg border border-slate-300 px-3 py-2",
            "placeholder": "Repetir contraseña",
        }),
    )
    document_type = forms.ChoiceField(
        choices=UserProfile.DocumentType.choices,
        widget=forms.Select(attrs={
            "class": "w-full rounded-lg border border-slate-300 px-3 py-2",
        }),
    )
    document_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            "class": "w-full rounded-lg border border-slate-300 px-3 py-2",
            "placeholder": "Número de documento",
        }),
    )
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={
            "class": "w-full rounded-lg border border-slate-300 px-3 py-2",
            "type": "date",
        }),
    )

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        validate_password(p1)
        return p2

    def clean(self):
        cleaned_data = super().clean()

        document_type = cleaned_data.get("document_type")
        document_number = cleaned_data.get("document_number")
        birth_date = cleaned_data.get("birth_date")

        if document_type and document_number:
            cleaned_data["document_number"] = validate_document_number(document_type, document_number)

        if birth_date:
            cleaned_data["birth_date"] = validate_adult_birth_date(birth_date)

        return cleaned_data