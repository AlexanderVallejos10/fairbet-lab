from decimal import Decimal
import uuid
from django.conf import settings
from django.db import models

class Event(models.Model):
    class Status(models.TextChoices):
        PROGRAMADO = "programado", "Programado"
        EN_VIVO = "en_vivo", "En vivo"
        FINALIZADO = "finalizado", "Finalizado"
        SUSPENDIDO = "suspendido", "Suspendido"
        ANULADO = "anulado", "Anulado"
    class Result(models.TextChoices):
        LOCAL = "gana_local", "Gana local"
        EMPATE = "empate", "Empate"
        VISITANTE = "gana_visitante", "Gana visitante"

    home_team = models.CharField(max_length=120)
    away_team = models.CharField(max_length=120)
    start_at = models.DateTimeField()
    status = models.CharField( max_length=20, choices=Status.choices, default=Status.PROGRAMADO,)
    result = models.CharField( max_length=20, choices=Result.choices, blank=True, null=True,)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.home_team} vs {self.away_team}"

class Odd(models.Model):
    class Selection(models.TextChoices):
        LOCAL = "gana_local", "Gana local"
        EMPATE = "empate", "Empate"
        VISITANTE = "gana_visitante", "Gana visitante"

    event = models.ForeignKey( Event, on_delete=models.CASCADE, related_name="odds",)
    selection = models.CharField(max_length=20, choices=Selection.choices)
    decimal_odds = models.DecimalField(max_digits=18, decimal_places=4)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint( fields=["event", "selection"], name="uniq_event_selection_odd",)]

    def __str__(self):
        return f"{self.event} - {self.selection} - {self.decimal_odds}"


class Bet(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        WON = "won", "Won"
        LOST = "lost", "Lost"
        CANCELLED = "cancelled", "Cancelled"
        CASHED_OUT = "cashed_out", "Cashed out"

    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    idempotency_key = models.CharField(max_length=120, unique=True)
    user = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bets",)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="bets")
    odd = models.ForeignKey(Odd, on_delete=models.PROTECT, related_name="bets")
    selection = models.CharField(max_length=20, choices=Odd.Selection.choices)
    stake = models.DecimalField(max_digits=18, decimal_places=4)
    odds_snapshot = models.DecimalField(max_digits=18, decimal_places=4)
    status = models.CharField(max_length=20, choices=Status.choices, default="accepted",)
    payout = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0.0000"))
    placed_at = models.DateTimeField(auto_now_add=True)
    settled_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.event} - {self.stake}"

class CombinedBet(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        WON = "won", "Won"
        LOST = "lost", "Lost"
        CANCELLED = "cancelled", "Cancelled"
        CASHED_OUT = "cashed_out", "Cashed out"

    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    idempotency_key = models.CharField(max_length=120, unique=True)
    user = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="combined_bets", )
    stake = models.DecimalField(max_digits=18, decimal_places=4)
    odds_snapshot = models.DecimalField(max_digits=18, decimal_places=4)
    selection_count = models.PositiveSmallIntegerField(default=0)
    status = models.CharField( max_length=20, choices=Status.choices, default="accepted",)
    payout = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0.0000"))
    placed_at = models.DateTimeField(auto_now_add=True)
    settled_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - combinada - {self.stake}"

class CombinedBetSelection(models.Model):
    combined_bet = models.ForeignKey(CombinedBet, on_delete=models.CASCADE, related_name="selections",)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    odd = models.ForeignKey(Odd, on_delete=models.PROTECT)
    selection = models.CharField(max_length=20, choices=Odd.Selection.choices)
    odds_snapshot = models.DecimalField(max_digits=18, decimal_places=4)

    class Meta:
        constraints = [ models.UniqueConstraint( fields=["combined_bet", "event"], name="uniq_combined_bet_event",)]

    def __str__(self):
        return f"{self.combined_bet_id} - {self.event_id} - {self.selection}"