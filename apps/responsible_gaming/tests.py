import pytest
from decimal import Decimal

from apps.responsible_gaming.models import SelfExclusion
from apps.responsible_gaming.services import (
    get_or_create_deposit_limit,
    is_self_excluded,
    lower_limits,
    request_limit_increase,
    self_exclude,
)


pytestmark = pytest.mark.django_db


def test_lower_limits_apply_immediately(verified_user):
    limits = lower_limits(
        verified_user,
        daily=Decimal("50.0000"),
        weekly=Decimal("200.0000"),
        monthly=Decimal("500.0000"),
    )

    assert limits.daily_limit == Decimal("50.0000")
    assert limits.weekly_limit == Decimal("200.0000")
    assert limits.monthly_limit == Decimal("500.0000")
    assert limits.limit_change_available_at is None


def test_limit_increase_becomes_pending(verified_user):
    limits = request_limit_increase(
        verified_user,
        daily=Decimal("150.0000"),
        weekly=Decimal("300.0000"),
        monthly=Decimal("600.0000"),
    )

    assert limits.pending_daily_limit == Decimal("150.0000")
    assert limits.pending_weekly_limit == Decimal("300.0000")
    assert limits.pending_monthly_limit == Decimal("600.0000")
    assert limits.limit_change_available_at is not None


def test_self_exclusion_activates_user(verified_user):
    exclusion = self_exclude(verified_user, SelfExclusion.Duration.SEVEN)

    assert exclusion.active is True
    assert exclusion.duration == SelfExclusion.Duration.SEVEN
    assert is_self_excluded(verified_user) is True