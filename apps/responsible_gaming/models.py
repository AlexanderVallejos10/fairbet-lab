from django.conf import settings
from django.db import models


class DepositLimit(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="deposit_limit",
    )
    daily_limit = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    weekly_limit = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    monthly_limit = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    pending_daily_limit = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    pending_weekly_limit = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    pending_monthly_limit = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    limit_change_available_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Deposit limits for {self.user.username}"


class SelfExclusion(models.Model):
    class Duration(models.TextChoices):
        SEVEN = "7_days", "7 days"
        THIRTY = "30_days", "30 days"
        NINETY = "90_days", "90 days"
        INDEFINITE = "indefinite", "Indefinite"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="self_exclusion",
    )
    duration = models.CharField(max_length=20, choices=Duration.choices)
    starts_at = models.DateTimeField(auto_now_add=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"Self exclusion for {self.user.username}"