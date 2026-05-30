from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.betting.models import Event, Odd
from apps.responsible_gaming.models import DepositLimit
from apps.users.choices import EstadoKYC
from apps.users.models import PerfilUsuario
from apps.wallet.services import deposit, ensure_user_accounts, get_balance


class Command(BaseCommand):
    help = "Carga usuarios, eventos, cuotas y saldo demo para FairBet Lab."

    def handle(self, *args, **options):
        User = get_user_model()

        admin = self._user(
            User,
            username="admin",
            email="admin@fairbet.local",
            password="Admin12345",
            is_staff=True,
            is_superuser=True,
            dni="12345678",
        )
        demo = self._user(
            User,
            username="demo",
            email="demo@fairbet.local",
            password="Demo12345",
            dni="87654321",
        )

        DepositLimit.objects.update_or_create(
            user=demo,
            defaults={
                "daily_limit": Decimal("500.0000"),
                "weekly_limit": Decimal("1500.0000"),
                "monthly_limit": Decimal("5000.0000"),
            },
        )

        ensure_user_accounts(demo)
        target_balance = Decimal("250.0000")
        current_balance = get_balance(demo)
        if current_balance < target_balance:
            deposit(
                demo,
                target_balance - current_balance,
                transaction_id=f"seed-demo-wallet-{timezone.now().timestamp()}",
            )

        events = [
            (
                Event.Sport.FUTBOL,
                "Peru",
                "Chile",
                1,
                {
                    Odd.Selection.LOCAL: Decimal("2.4000"),
                    Odd.Selection.EMPATE: Decimal("3.1000"),
                    Odd.Selection.VISITANTE: Decimal("2.9500"),
                },
            ),
            (
                Event.Sport.BASQUET,
                "Lakers",
                "Celtics",
                2,
                {
                    Odd.Selection.LOCAL: Decimal("1.9000"),
                    Odd.Selection.EMPATE: Decimal("12.0000"),
                    Odd.Selection.VISITANTE: Decimal("2.1000"),
                },
            ),
            (
                Event.Sport.TENIS,
                "Alcaraz",
                "Sinner",
                3,
                {
                    Odd.Selection.LOCAL: Decimal("1.8500"),
                    Odd.Selection.EMPATE: Decimal("9.5000"),
                    Odd.Selection.VISITANTE: Decimal("2.0000"),
                },
            ),
            (
                Event.Sport.VOLEY,
                "Peru Voley",
                "Brasil Voley",
                4,
                {
                    Odd.Selection.LOCAL: Decimal("2.0500"),
                    Odd.Selection.EMPATE: Decimal("8.0000"),
                    Odd.Selection.VISITANTE: Decimal("1.8500"),
                },
            ),
        ]

        for sport, home, away, days, odds in events:
            event, _ = Event.objects.update_or_create(
                home_team=home,
                away_team=away,
                defaults={
                    "sport": sport,
                    "start_at": timezone.now() + timedelta(days=days),
                    "status": Event.Status.PROGRAMADO,
                    "result": None,
                    "max_total_bets": 1000,
                    "max_bets_per_user": 3,
                    "max_event_exposure": Decimal("10000.0000"),
                },
            )
            for selection, decimal_odds in odds.items():
                Odd.objects.update_or_create(
                    event=event,
                    selection=selection,
                    defaults={
                        "decimal_odds": decimal_odds,
                        "is_active": True,
                        "max_selection_exposure": Decimal("5000.0000"),
                    },
                )

        self.stdout.write(self.style.SUCCESS("Datos demo cargados correctamente."))
        self.stdout.write("Usuario demo: demo / Demo12345")
        self.stdout.write("Admin: admin / Admin12345")

    def _user(self, User, username, email, password, dni, is_staff=False, is_superuser=False):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
            },
        )
        user.email = email
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.set_password(password)
        user.save()

        PerfilUsuario.objects.update_or_create(
            user=user,
            defaults={
                "dni": dni,
                "fecha_nacimiento": date(1990, 1, 1),
                "estado_kyc": EstadoKYC.VERIFICADO,
            },
        )
        ensure_user_accounts(user)
        return user
