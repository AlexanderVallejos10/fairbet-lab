import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.betting.models import Event, Odd
from apps.responsible_gaming.models import DepositLimit, SelfExclusion
from apps.users.models import UserProfile
from apps.wallet.models import WalletAccount
from apps.wallet.services import ensure_user_accounts, deposit_virtual_chips


User = get_user_model()


def _unique_username(prefix: str = "user") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _unique_dni() -> str:
    return f"{uuid.uuid4().int % 100000000:08d}"


@pytest.fixture
def user_factory(db):
    def _create_user(
        *,
        username_prefix="user",
        password="testpass123",
        dni=None,
        birth_date=None,
        kyc_status=UserProfile.KYCStatus.VERIFIED,
        with_wallet=True,
        is_staff=False,
    ):
        user = User.objects.create_user(
            username=_unique_username(username_prefix),
            password=password,
            email="",
            first_name="",
            last_name="",
            is_staff=is_staff,
        )

        profile = UserProfile.objects.create(
            user=user,
            dni=dni or _unique_dni(),
            birth_date=birth_date or date(1990, 1, 1),
            kyc_status=kyc_status,
        )

        if with_wallet:
            ensure_user_accounts(user)

        return user, profile

    return _create_user


@pytest.fixture
def verified_user(user_factory):
    user, _ = user_factory(kyc_status=UserProfile.KYCStatus.VERIFIED)
    deposit_virtual_chips(user, "100.0000", f"seed-{uuid.uuid4().hex[:8]}")
    return user


@pytest.fixture
def autoexcluded_user(user_factory):
    user, profile = user_factory(kyc_status=UserProfile.KYCStatus.SELF_EXCLUDED)
    return user


@pytest.fixture
def admin_user(user_factory):
    user, _ = user_factory(kyc_status=UserProfile.KYCStatus.VERIFIED, is_staff=True)
    user.is_superuser = True
    user.save(update_fields=["is_superuser"])
    return user


@pytest.fixture
def event_with_odds(db):
    event = Event.objects.create(
        home_team="Peru",
        away_team="Chile",
        start_at=timezone.now() + timedelta(hours=3),
        status=Event.Status.PROGRAMADO,
    )

    local = Odd.objects.create(
        event=event,
        selection=Odd.Selection.LOCAL,
        decimal_odds=Decimal("2.5000"),
    )
    draw = Odd.objects.create(
        event=event,
        selection=Odd.Selection.EMPATE,
        decimal_odds=Decimal("3.1000"),
    )
    away = Odd.objects.create(
        event=event,
        selection=Odd.Selection.VISITANTE,
        decimal_odds=Decimal("3.8000"),
    )

    return event, {"gana_local": local, "empate": draw, "gana_visitante": away}