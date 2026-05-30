from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from apps.betting.models import ( AccumulatedBet,AccumulatedBetLeg,Bet,Event, Market,Selection,)
from apps.betting.services import settle_event
from apps.betting.sport_rules import allowed_markets_for_sport

class SelectionInline(admin.TabularInline):
    model = Selection
    extra = 3
    fields = ("name", "odds", "created_at")
    readonly_fields = ("created_at",)

class MarketInline(admin.TabularInline):
    model = Market
    extra = 1
    fields = ("name", "market_type", "status", "created_at")
    readonly_fields = ("created_at",)

class EventAdminForm(forms.ModelForm):
    winning_selection_name = forms.ChoiceField(
        required=False,
        label="Resultado ganador",
        help_text="Selecciona la selección que ganó el evento.",
    )
    class Meta:
        model = Event
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["winning_selection_name"].choices = [("", "---------")]

        if self.instance and self.instance.pk:
            selection_names = (
                Selection.objects.filter(market__event=self.instance)
                .order_by("name")
                .values_list("name", flat=True)
                .distinct()
            )
            self.fields["winning_selection_name"].choices += [
                (name, name) for name in selection_names
            ]

class MarketAdminForm(forms.ModelForm):
    class Meta:
        model = Market
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        event = cleaned.get("event") or getattr(self.instance, "event", None)
        market_type = cleaned.get("market_type") or getattr(self.instance, "market_type", None)
        if event and market_type:
            allowed_types = allowed_markets_for_sport(event.sport)
            if market_type not in allowed_types:
                raise ValidationError(
                    {
                        "market_type": (
                            f'El mercado "{market_type}" no está permitido para '
                            f'el deporte "{event.get_sport_display()}".'
                        )
                    }
                )
        return cleaned

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    form = EventAdminForm
    change_form_template = "admin/betting/event/change_form.html"
    list_display = ("name", "sport", "status", "starts_at", "created_at", "markets_count")
    list_filter = ("status", "sport")
    search_fields = ("name", "sport")
    ordering = ("starts_at",)
    inlines = [MarketInline]
    readonly_fields = ("created_at",)

    @admin.display(description="Mercados")
    def markets_count(self, obj):
        return obj.markets.count()

    def response_change(self, request, obj):
        if "_liquidate" in request.POST:
            winning_selection_name = request.POST.get("winning_selection_name", "").strip()

            if not winning_selection_name:
                self.message_user(
                    request,
                    "Selecciona un resultado ganador antes de liquidar.",
                    level=messages.ERROR,
                )
                return HttpResponseRedirect(".")

            try:
                settle_event(obj, winning_selection_name)
                self.message_user(
                    request,
                    f'Evento liquidado correctamente con resultado "{winning_selection_name}".',
                    level=messages.SUCCESS,
                )
            except Exception as exc:
                self.message_user(
                    request,
                    f"No se pudo liquidar el evento: {exc}",
                    level=messages.ERROR,
                )

            return HttpResponseRedirect(".")

        return super().response_change(request, obj)

@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    form = MarketAdminForm
    list_display = ("name", "event", "market_type", "status", "created_at", "selections_count")
    list_filter = ("status", "market_type", "event__sport")
    search_fields = ("name", "event__name")
    ordering = ("-created_at",)
    inlines = [SelectionInline]
    readonly_fields = ("created_at",)

    @admin.display(description="Selecciones")
    def selections_count(self, obj):
        return obj.selections.count()

@admin.register(Selection)
class SelectionAdmin(admin.ModelAdmin):
    list_display = ("name", "market", "odds", "created_at")
    search_fields = ("name", "market__name")
    list_filter = ("market__event__sport",)
    readonly_fields = ("created_at",)

@admin.register(Bet)
class BetAdmin(admin.ModelAdmin):
    list_display = ("user", "market", "selection", "stake", "odds", "status", "created_at")
    list_filter = ("status", "market__event__sport")
    search_fields = ("user__email", "selection__name", "market__name")
    readonly_fields = ("created_at", "transaction_id")

@admin.register(AccumulatedBet)
class AccumulatedBetAdmin(admin.ModelAdmin):
    list_display = ("user", "stake", "combined_odds", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__email",)
    readonly_fields = ("created_at", "transaction_id")

@admin.register(AccumulatedBetLeg)
class AccumulatedBetLegAdmin(admin.ModelAdmin):
    list_display = ("accumulated_bet", "selection", "market", "odds_at_bet", "settled", "won")
    list_filter = ("settled", "won", "market__event__sport")
    search_fields = ("selection__name", "market__name")