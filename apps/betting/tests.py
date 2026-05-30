from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.betting.models import Bet
from apps.betting.services import place_simple_bet, settle_event
from apps.wallet.services import get_user_wallet_account, ensure_user_accounts


pytestmark = pytest.mark.django_db


def test_place_bet_creates_bet_and_moves_money(verified_user, event_with_odds):
    event, odds = event_with_odds

    bet = place_simple_bet(
        user=verified_user,
        odd=odds["gana_local"],
        stake="20.0000",
        idempotency_key="bet-001",
    )

    wallet = get_user_wallet_account(verified_user)
    accounts = ensure_user_accounts(verified_user)
    pending = accounts["apuestas_pendientes"]

    assert bet.status == Bet.Status.ACCEPTED
    assert bet.stake == Decimal("20.0000")
    assert wallet.balance == Decimal("80.0000")
    assert pending.balance == Decimal("20.0000")


def test_place_bet_with_insufficient_balance_fails(verified_user, event_with_odds):
    event, odds = event_with_odds

    with pytest.raises(ValidationError):
        place_simple_bet(
            user=verified_user,
            odd=odds["gana_local"],
            stake="9999.0000",
            idempotency_key="bet-002",
        )


def test_autoexcluded_user_cannot_bet(autoexcluded_user, event_with_odds):
    event, odds = event_with_odds

    with pytest.raises(ValidationError):
        place_simple_bet(
            user=autoexcluded_user,
            odd=odds["gana_local"],
            stake="10.0000",
            idempotency_key="bet-003",
        )


def test_duplicate_idempotency_key_does_not_create_two_bets(verified_user, event_with_odds):
    event, odds = event_with_odds

    bet1 = place_simple_bet(
        user=verified_user,
        odd=odds["empate"],
        stake="10.0000",
        idempotency_key="bet-004",
    )
    bet2 = place_simple_bet(
        user=verified_user,
        odd=odds["empate"],
        stake="10.0000",
        idempotency_key="bet-004",
    )

    wallet = get_user_wallet_account(verified_user)

    assert bet1.pk == bet2.pk
    assert Bet.objects.filter(idempotency_key="bet-004").count() == 1
    assert wallet.balance == Decimal("90.0000")


def test_winning_bet_pays_correct_amount(verified_user, event_with_odds):
    event, odds = event_with_odds

    bet = place_simple_bet(
        user=verified_user,
        odd=odds["gana_local"],
        stake="20.0000",
        idempotency_key="bet-005",
    )

    settle_event(event, "gana_local")
    bet.refresh_from_db()

    wallet = get_user_wallet_account(verified_user)

    assert bet.status == Bet.Status.WON
    assert bet.payout == Decimal("50.0000")
    assert wallet.balance == Decimal("130.0000")


def test_event_blocks_when_user_reaches_bet_limit(verified_user, event_with_odds):
    event, odds = event_with_odds
    event.max_bets_per_user = 1
    event.save(update_fields=["max_bets_per_user"])

    place_simple_bet(
        user=verified_user,
        odd=odds["gana_local"],
        stake="5.0000",
        idempotency_key="limit-user-001",
    )

    with pytest.raises(ValidationError, match="maximo de apuestas"):
        place_simple_bet(
            user=verified_user,
            odd=odds["empate"],
            stake="5.0000",
            idempotency_key="limit-user-002",
        )


def test_event_blocks_when_house_exposure_is_exceeded(verified_user, event_with_odds):
    event, odds = event_with_odds
    event.max_event_exposure = Decimal("10.0000")
    event.save(update_fields=["max_event_exposure"])

    with pytest.raises(ValidationError, match="limite de exposicion"):
        place_simple_bet(
            user=verified_user,
            odd=odds["gana_local"],
            stake="5.0000",
            idempotency_key="limit-exposure-001",
        )


def test_event_blocks_after_start_time(verified_user, event_with_odds):
    event, odds = event_with_odds
    event.start_at = timezone.now()
    event.save(update_fields=["start_at"])

    with pytest.raises(ValidationError, match="ya inicio"):
        place_simple_bet(
            user=verified_user,
            odd=odds["gana_local"],
            stake="5.0000",
            idempotency_key="started-event-001",
        )
