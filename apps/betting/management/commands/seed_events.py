from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.betting.models import Event, Market, Selection


class Command(BaseCommand):
    help = 'Crea eventos semilla multideporte con mercados permitidos.'

    def handle(self, *args, **options):
        now = timezone.now()
        fixtures = [
            # FUTBOL - EN_VIVO
            {
                'name': 'Manchester United vs Liverpool',
                'sport': Event.Sport.FUTBOL,
                'status': Event.Status.EN_VIVO,
                'starts_at': now - timezone.timedelta(minutes=30),
                'markets': [
                    {
                        'name': 'Resultado final',
                        'market_type': Market.Type.UNO_X_DOS,
                        'selections': [
                            ('Manchester United', '2.1000'),
                            ('Empate', '3.4000'),
                            ('Liverpool', '3.8000'),
                        ],
                    },
                    {
                        'name': 'Más/Menos goles',
                        'market_type': Market.Type.OVER_UNDER,
                        'selections': [
                            ('Más de 2.5', '1.9500'),
                            ('Menos de 2.5', '1.7500'),
                        ],
                    },
                    {
                        'name': 'Ambos anotan',
                        'market_type': Market.Type.BTTS,
                        'selections': [
                            ('Sí', '1.9000'),
                            ('No', '1.8000'),
                        ],
                    },
                ],
            },
            # FUTBOL - PROGRAMADO
            {
                'name': 'Alianza Lima vs Sporting Cristal',
                'sport': Event.Sport.FUTBOL,
                'status': Event.Status.PROGRAMADO,
                'starts_at': now + timezone.timedelta(days=1),
                'markets': [
                    {
                        'name': 'Resultado final',
                        'market_type': Market.Type.UNO_X_DOS,
                        'selections': [
                            ('Alianza Lima', '2.0500'),
                            ('Empate', '3.2000'),
                            ('Sporting Cristal', '3.8500'),
                        ],
                    },
                    {
                        'name': 'Más/Menos goles',
                        'market_type': Market.Type.OVER_UNDER,
                        'selections': [
                            ('Más de 2.5', '1.9200'),
                            ('Menos de 2.5', '1.7800'),
                        ],
                    },
                    {
                        'name': 'Ambos anotan',
                        'market_type': Market.Type.BTTS,
                        'selections': [
                            ('Sí', '1.8700'),
                            ('No', '1.8500'),
                        ],
                    },
                ],
            },
            # BASQUET - EN_VIVO
            {
                'name': 'Lakers vs Celtics',
                'sport': Event.Sport.BASQUET,
                'status': Event.Status.EN_VIVO,
                'starts_at': now - timezone.timedelta(minutes=15),
                'markets': [
                    {
                        'name': 'Ganador del partido',
                        'market_type': Market.Type.WINNER,
                        'selections': [
                            ('Lakers', '1.7000'),
                            ('Celtics', '2.0500'),
                        ],
                    },
                    {
                        'name': 'Hándicap',
                        'market_type': Market.Type.HANDICAP,
                        'selections': [
                            ('Lakers -3.5', '1.9100'),
                            ('Celtics +3.5', '1.9100'),
                        ],
                    },
                    {
                        'name': 'Totales',
                        'market_type': Market.Type.TOTALS,
                        'selections': [
                            ('Más de 220.5', '1.8800'),
                            ('Menos de 220.5', '1.8800'),
                        ],
                    },
                ],
            },
            # BASQUET - PROGRAMADO
            {
                'name': 'Bulls vs Warriors',
                'sport': Event.Sport.BASQUET,
                'status': Event.Status.PROGRAMADO,
                'starts_at': now + timezone.timedelta(days=2),
                'markets': [
                    {
                        'name': 'Ganador del partido',
                        'market_type': Market.Type.WINNER,
                        'selections': [
                            ('Bulls', '2.1000'),
                            ('Warriors', '1.7800'),
                        ],
                    },
                    {
                        'name': 'Hándicap',
                        'market_type': Market.Type.HANDICAP,
                        'selections': [
                            ('Bulls +4.5', '1.9100'),
                            ('Warriors -4.5', '1.9100'),
                        ],
                    },
                    {
                        'name': 'Totales',
                        'market_type': Market.Type.TOTALS,
                        'selections': [
                            ('Más de 228.5', '1.9000'),
                            ('Menos de 228.5', '1.9000'),
                        ],
                    },
                ],
            },
            # VOLEY - EN_VIVO
            {
                'name': 'Regatas vs Géminis',
                'sport': Event.Sport.VOLEY,
                'status': Event.Status.EN_VIVO,
                'starts_at': now - timezone.timedelta(minutes=8),
                'markets': [
                    {
                        'name': 'Ganador del partido',
                        'market_type': Market.Type.WINNER,
                        'selections': [
                            ('Regatas', '1.8200'),
                            ('Géminis', '1.9800'),
                        ],
                    },
                    {
                        'name': 'Sets',
                        'market_type': Market.Type.SETS,
                        'selections': [
                            ('3 sets', '2.3000'),
                            ('4 sets', '2.1000'),
                            ('5 sets', '3.0000'),
                        ],
                    },
                    {
                        'name': 'Totales',
                        'market_type': Market.Type.TOTALS,
                        'selections': [
                            ('Más de 3.5 sets', '1.9500'),
                            ('Menos de 3.5 sets', '1.7500'),
                        ],
                    },
                ],
            },
            # VOLEY - PROGRAMADO
            {
                'name': 'Perú vs Argentina',
                'sport': Event.Sport.VOLEY,
                'status': Event.Status.PROGRAMADO,
                'starts_at': now + timezone.timedelta(days=3),
                'markets': [
                    {
                        'name': 'Ganador del partido',
                        'market_type': Market.Type.WINNER,
                        'selections': [
                            ('Perú', '2.2500'),
                            ('Argentina', '1.6500'),
                        ],
                    },
                    {
                        'name': 'Sets',
                        'market_type': Market.Type.SETS,
                        'selections': [
                            ('3 sets', '2.2500'),
                            ('4 sets', '2.0500'),
                            ('5 sets', '3.1000'),
                        ],
                    },
                    {
                        'name': 'Totales',
                        'market_type': Market.Type.TOTALS,
                        'selections': [
                            ('Más de 3.5 sets', '1.9000'),
                            ('Menos de 3.5 sets', '1.8000'),
                        ],
                    },
                ],
            },
        ]

        created_events = 0
        updated_events = 0

        with transaction.atomic():
            for fixture in fixtures:
                event, created = Event.objects.update_or_create(
                    name=fixture['name'],
                    defaults={
                        'sport': fixture['sport'],
                        'status': fixture['status'],
                        'starts_at': fixture['starts_at'],
                        'live_betting_enabled': True,
                        'max_bets': 5000,
                        'max_event_exposure': Decimal('100000.0000'),
                    },
                )
                if created:
                    created_events += 1
                else:
                    updated_events += 1

                for market_data in fixture['markets']:
                    market, _ = Market.objects.update_or_create(
                        event=event,
                        name=market_data['name'],
                        defaults={
                            'market_type': market_data['market_type'],
                            'status': Market.Status.ABIERTO,
                            'suspended_until': None,
                            'max_bets': 1500,
                            'max_exposure': Decimal('25000.0000'),
                        },
                    )

                    for selection_name, selection_odds in market_data['selections']:
                        Selection.objects.update_or_create(
                            market=market,
                            name=selection_name,
                            defaults={
                                'odds': Decimal(selection_odds),
                            },
                        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Seed multideporte completado. Nuevos: {created_events} | Actualizados: {updated_events}'
            )
        )