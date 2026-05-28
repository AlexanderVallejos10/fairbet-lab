from django.contrib import admin
from .models import Bet, CombinedBet, CombinedBetSelection, Event, Odd

class OddInline(admin.TabularInline):
    model = Odd
    extra = 3

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("home_team", "away_team", "start_at", "status", "result")
    list_filter = ("status",)
    search_fields = ("home_team", "away_team")
    inlines = [OddInline]

@admin.register(Odd)
class OddAdmin(admin.ModelAdmin):
    list_display = ("event", "selection", "decimal_odds", "is_active", "updated_at")
    list_filter = ("is_active", "selection")
    search_fields = ("event__home_team", "event__away_team")

@admin.register(Bet)
class BetAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "selection", "stake", "status", "payout", "placed_at")
    list_filter = ("status", "selection")
    search_fields = ("user__username", "event__home_team", "event__away_team")

@admin.register(CombinedBet)
class CombinedBetAdmin(admin.ModelAdmin):
    list_display = ("user", "stake", "odds_snapshot", "status", "payout", "placed_at")
    list_filter = ("status",)
    search_fields = ("user__username", "idempotency_key")

@admin.register(CombinedBetSelection)
class CombinedBetSelectionAdmin(admin.ModelAdmin):
    list_display = ("combined_bet", "event", "selection", "odds_snapshot")
    search_fields = ("combined_bet__idempotency_key", "event__home_team", "event__away_team")