from datetime import timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import DepositLimit, SelfExclusion


def get_or_create_deposit_limit(user) -> DepositLimit:
    obj, _ = DepositLimit.objects.get_or_create(user=user)
    return obj


def lower_limits(user, daily=None, weekly=None, monthly=None):
    limits = get_or_create_deposit_limit(user)

    if daily is not None:
        limits.daily_limit = daily
    if weekly is not None:
        limits.weekly_limit = weekly
    if monthly is not None:
        limits.monthly_limit = monthly

    limits.pending_daily_limit = None
    limits.pending_weekly_limit = None
    limits.pending_monthly_limit = None
    limits.limit_change_available_at = None
    limits.save()
    return limits


def request_limit_increase(user, daily=None, weekly=None, monthly=None):
    limits = get_or_create_deposit_limit(user)
    available_at = timezone.now() + timedelta(hours=24)

    if daily is not None:
        limits.pending_daily_limit = daily
    if weekly is not None:
        limits.pending_weekly_limit = weekly
    if monthly is not None:
        limits.pending_monthly_limit = monthly

    limits.limit_change_available_at = available_at
    limits.save()
    return limits


def activate_pending_limits(user):
    limits = get_or_create_deposit_limit(user)

    if not limits.limit_change_available_at:
        return limits

    if timezone.now() < limits.limit_change_available_at:
        raise ValidationError("El cambio de límite aún está en espera.")

    if limits.pending_daily_limit is not None:
        limits.daily_limit = limits.pending_daily_limit
    if limits.pending_weekly_limit is not None:
        limits.weekly_limit = limits.pending_weekly_limit
    if limits.pending_monthly_limit is not None:
        limits.monthly_limit = limits.pending_monthly_limit

    limits.pending_daily_limit = None
    limits.pending_weekly_limit = None
    limits.pending_monthly_limit = None
    limits.limit_change_available_at = None
    limits.save()
    return limits


def self_exclude(user, duration: str):
    obj, _ = SelfExclusion.objects.get_or_create(user=user, defaults={"duration": duration})

    obj.duration = duration
    obj.active = True

    if duration == SelfExclusion.Duration.SEVEN:
        obj.ends_at = timezone.now() + timedelta(days=7)
    elif duration == SelfExclusion.Duration.THIRTY:
        obj.ends_at = timezone.now() + timedelta(days=30)
    elif duration == SelfExclusion.Duration.NINETY:
        obj.ends_at = timezone.now() + timedelta(days=90)
    else:
        obj.ends_at = None

    obj.save()
    return obj


def is_self_excluded(user) -> bool:
    exclusion = SelfExclusion.objects.filter(user=user, active=True).first()
    if not exclusion:
        return False

    if exclusion.ends_at and timezone.now() > exclusion.ends_at:
        exclusion.active = False
        exclusion.save(update_fields=["active"])
        return False

    return True