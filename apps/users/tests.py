import pytest
from datetime import date

from apps.users.models import UserProfile
from apps.users.serializers import RegisterSerializer


pytestmark = pytest.mark.django_db


def test_register_serializer_creates_profile():
    data = {
        "username": "juan123",
        "email": "juan@example.com",
        "password": "secret123",
        "first_name": "Juan",
        "last_name": "Perez",
        "dni": "12345678",
        "birth_date": "1995-01-01",
    }

    serializer = RegisterSerializer(data=data)
    assert serializer.is_valid(), serializer.errors

    profile = serializer.save()

    assert profile.dni == "12345678"
    assert profile.kyc_status == UserProfile.KYCStatus.PENDING
    assert profile.user.username == "juan123"


def test_underage_birthdate_rejected():
    data = {
        "username": "menor123",
        "password": "secret123",
        "dni": "12345679",
        "birth_date": date.today().replace(year=date.today().year - 17).isoformat(),
    }

    serializer = RegisterSerializer(data=data)
    assert not serializer.is_valid()
    assert "birth_date" in serializer.errors


def test_invalid_dni_rejected():
    data = {
        "username": "dni_invalido",
        "password": "secret123",
        "dni": "12AB5678",
        "birth_date": "1995-01-01",
    }

    serializer = RegisterSerializer(data=data)
    assert not serializer.is_valid()
    assert "dni" in serializer.errors