import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Загружает ингредиенты из CSV-файла."""

    help = 'Загружает ингредиенты из data/ingredients.csv'

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            '--path',
            type=str,
            default=str(
                Path(settings.BASE_DIR) / 'data' / 'ingredients.csv'
            ),
            help='Путь к CSV-файлу с ингредиентами.',
        )

    def handle(self, *args, **options) -> None:
        path = Path(options['path'])
        if not path.exists():
            self.stderr.write(self.style.ERROR(f'Файл не найден: {path}'))
            return

        rows: list[list[str]] = []
        with path.open(encoding='utf-8') as f:
            reader = csv.reader(f)
            first = next(reader, None)
            if first and first[0].strip().lower() not in (
                    'name', 'название', 'ингредиент',
            ):
                rows.append(first)
            rows.extend(reader)

        unique: dict[tuple[str, str], Ingredient] = {}
        for row in rows:
            if len(row) < 2:
                continue
            name = row[0].strip()
            unit = row[1].strip()
            if not name or not unit:
                continue
            unique.setdefault(
                (name, unit),
                Ingredient(name=name, measurement_unit=unit),
            )

        existing = set(
            Ingredient.objects.values_list('name', 'measurement_unit')
        )
        to_create = [
            obj for key, obj in unique.items()
            if key not in existing
        ]

        Ingredient.objects.bulk_create(to_create, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(
            f'Всего строк: {len(rows)}, '
            f'уникальных: {len(unique)}, '
            f'создано: {len(to_create)}, '
            f'пропущено (уже были): {len(unique) - len(to_create)}'
        ))
