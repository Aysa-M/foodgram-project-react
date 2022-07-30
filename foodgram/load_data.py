import os
import csv

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodgram.settings')
django.setup()
from recipes.models import Ingredient


path = '.'
os.chdir(path)


with open('ingredients.csv', 'r', encoding='utf-8') as file:
    reader = csv.DictReader(file, fieldnames=['name', 'measurement_unit'])
    to_db = (Ingredient(
        name=['name'],
        measurement_unit=['measurement_unit']
    ) for _ in reader)
    Ingredient.objects.bulk_create(to_db)
