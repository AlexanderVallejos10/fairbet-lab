from django.contrib import admin

from apps.betting.models import Event, Market, Selection, Bet, AccumulatedBet, AccumulatedBetLeg


class SelectionInline(admin.TabularInline):
    model = Selection
    extra = 3


class MarketInline(admin.TabularInline):
    model = Market
    extra = 1


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "sport", "status", "starts_at", "created_at")
    list_filter = ("status", "sport")
    search_fields = ("name", "sport")
    inlines = [MarketInline]


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ("name", "event", "market_type", "status", "created_at")
    list_filter = ("status", "market_type")
    search_fields = ("name", "event__name")
    inlines = [SelectionInline]


@admin.register(Selection)
class SelectionAdmin(admin.ModelAdmin):
    list_display = ("name", "market", "odds", "created_at")
    search_fields = ("name", "market__name")


@admin.register(Bet)
class BetAdmin(admin.ModelAdmin):
    list_display = ("user", "market", "selection", "stake", "odds", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__email", "selection__name", "market__name")


@admin.register(AccumulatedBet)
class AccumulatedBetAdmin(admin.ModelAdmin):
    list_display = ("user", "stake", "combined_odds", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__email",)


@admin.register(AccumulatedBetLeg)
class AccumulatedBetLegAdmin(admin.ModelAdmin):
    list_display = ("accumulated_bet", "selection", "market", "odds_at_bet", "settled", "won")
    list_filter = ("settled", "won")
    search_fields = ("selection__name", "market__name")