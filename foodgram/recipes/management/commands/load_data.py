import csv
from typing import Any, Optional

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Loads deafault ingredient data from csv file.'

    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        with open('ingredients.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(
                file,
                delimiter=",",
                fieldnames=['name', 'measurement_unit']
            )
            to_db = (Ingredient(
                name=_['name'],
                measurement_unit=_['measurement_unit']
            ) for _ in reader)
            Ingredient.objects.bulk_create(to_db)
            self.stdout.write(
                self.style.SUCCESS(
                    'Data is successfully loaded'))
