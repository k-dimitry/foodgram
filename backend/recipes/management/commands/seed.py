"""Seed-команда: наполняет БД тегами, пользователями и рецептами.
Идемпотентна.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from recipes.models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Tag,
)
from recipes.serializers import _decode_image

User = get_user_model()

USERS: list[dict[str, str | bool]] = [
    {
        'email': 'bestpythondev@gmail.com',
        'username': 'admin',
        'first_name': 'Admin',
        'last_name': 'Foodgram',
        'password': 'admin12345',
        'is_staff': True,
        'is_superuser': True,
    },
    {
        'email': 'dimitry@foodgram.dev',
        'username': 'dimitry',
        'first_name': 'Dimitry',
        'last_name': 'Developer',
        'password': 'Ashgabat@5',
    },
    {
        'email': 'user2@foodgram.dev',
        'username': 'user2',
        'first_name': 'User',
        'last_name': 'Two',
        'password': 'user2pass123',
    },
    {
        'email': 'user3@foodgram.dev',
        'username': 'user3',
        'first_name': 'User',
        'last_name': 'Three',
        'password': 'user3pass123',
    },
]

TAGS = [
    ('Завтрак', 'breakfast'),
    ('Обед', 'lunch'),
    ('Ужин', 'dinner'),
    ('Десерт', 'dessert'),
]

RECIPES = [
    {
        'name': 'Оливье',
        'author': 'dimitry',
        'text': 'Классический салат Оливье с говядиной и солёными огурцами.',
        'cooking_time': 60,
        'tags': ['lunch', 'dinner'],
        'ingredients': [
            ('Картофель', 'г', 300),
            ('Морковь', 'г', 150),
            ('яйца куриные', 'г', 240),
            ('огурцы консервированные', 'г', 150),
            ('Майонез', 'г', 200),
        ],
    },
    {
        'name': 'Борщ',
        'author': 'dimitry',
        'text': 'Наваристый украинский борщ со сметаной.',
        'cooking_time': 120,
        'tags': ['lunch'],
        'ingredients': [
            ('Свекла', 'г', 300),
            ('Капуста белокочанная', 'г', 200),
            ('Картофель', 'г', 300),
            ('Морковь', 'г', 100),
            ('Лук репчатый', 'г', 100),
        ],
    },
    {
        'name': 'Пицца Маргарита',
        'author': 'user2',
        'text': 'Тонкая пицца с томатами и моцареллой.',
        'cooking_time': 45,
        'tags': ['lunch', 'dinner'],
        'ingredients': [
            ('мука', 'г', 300),
            ('дрожжи сухие', 'г', 5),
            ('моцарелла', 'г', 200),
            ('Томатная паста', 'г', 100),
            ('Соль', 'г', 5),
        ],
    },
    {
        'name': 'Салат Цезарь',
        'author': 'user2',
        'text': 'Хрустящий салат Цезарь с курицей и пармезаном.',
        'cooking_time': 30,
        'tags': ['lunch'],
        'ingredients': [
            ('Куриное филе', 'г', 300),
            ('пармезан', 'г', 100),
            ('Хлеб', 'г', 100),
            ('Майонез', 'г', 100),
        ],
    },
    {
        'name': 'Блины',
        'author': 'user3',
        'text': 'Тонкие домашние блинчики к завтраку.',
        'cooking_time': 30,
        'tags': ['breakfast', 'dessert'],
        'ingredients': [
            ('мука', 'г', 250),
            ('Молоко', 'мл', 500),
            ('яйца куриные', 'г', 120),
            ('Сахар', 'г', 30),
            ('Соль', 'г', 3),
        ],
    },
    {
        'name': 'Тирамису',
        'author': 'user3',
        'text': 'Нежный итальянский десерт с маскарпоне и кофе.',
        'cooking_time': 60,
        'tags': ['dessert'],
        'ingredients': [
            ('Сыр маскарпоне', 'г', 500),
            ('печенье Савоярди', 'г', 150),
            ('Сливки', 'мл', 200),
            ('Сахар', 'г', 100),
            ('Какао-порошок', 'г', 20),
        ],
    },
]


class Command(BaseCommand):
    """Наполняет БД тегами, пользователями и рецептами."""

    help = 'Seed database with tags, users, and recipes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Удалить сид-пользователей (CASCADE их рецепты) и сид-теги перед созданием',
        )

    def handle(self, *args, **options):
        if options['flush']:
            self._flush()

        with transaction.atomic():
            tags_created = self._seed_tags()
            users_created = self._seed_users()
            recipes_created = self._seed_recipes()

        self.stdout.write(self.style.SUCCESS(
            f'\nSeed complete: '
            f'tags +{tags_created}, '
            f'users +{users_created}, '
            f'recipes +{recipes_created}'
        ))

    def _flush(self):
        """Удаляет сид-данные. Ингредиенты не трогает."""
        deleted_users = User.objects.filter(
            email__in=[u['email'] for u in USERS],
        ).delete()
        deleted_tags = Tag.objects.filter(
            slug__in=[t[1] for t in TAGS],
        ).delete()
        self.stdout.write(self.style.WARNING(
            f'Flush: users → {deleted_users[0]}, tags → {deleted_tags[0]}'
        ))

    def _seed_tags(self) -> int:
        created = 0
        for name, slug in TAGS:
            _, is_new = Tag.objects.get_or_create(
                slug=slug,
                defaults={'name': name},
            )
            if is_new:
                created += 1
        self.stdout.write(f'Tags: {created} created, {len(TAGS) - created} existing')
        return created

    def _seed_users(self) -> int:
        created = 0
        for data in USERS:
            data = data.copy()
            password = data.pop('password')
            user, is_new = User.objects.get_or_create(
                email=data['email'],
                defaults=data,
            )
            if is_new:
                user.set_password(password)
                user.save()
                created += 1
        self.stdout.write(f'Users: {created} created, {len(USERS) - created} existing')
        return created

    def _seed_recipes(self) -> int:
        created = 0
        skipped_ingredients = 0

        for data in RECIPES:
            author = User.objects.get(email=self._email_of(data['author']))
            if Recipe.objects.filter(name=data['name'], author=author).exists():
                continue

            recipe = Recipe.objects.create(
                author=author,
                name=data['name'],
                text=data['text'],
                cooking_time=data['cooking_time'],
                image=_decode_image(
                    'data:image/png;base64,'
                    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8'
                    'z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=='
                ),
            )

            tag_objs = Tag.objects.filter(slug__in=data['tags'])
            recipe.tags.set(tag_objs)

            for ing_name, ing_unit, amount in data['ingredients']:
                ingredient = Ingredient.objects.filter(
                    name__iexact=ing_name,
                    measurement_unit=ing_unit,
                ).first()
                if ingredient is None:
                    skipped_ingredients += 1
                    self.stdout.write(self.style.WARNING(
                        f'  ! Ingredient not found: {ing_name} ({ing_unit}) — skipped'
                    ))
                    continue
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=amount,
                )

            created += 1

        self.stdout.write(
            f'Recipes: {created} created, {len(RECIPES) - created} existing'
        )
        if skipped_ingredients:
            self.stdout.write(self.style.WARNING(
                f'  Skipped ingredients (not in DB): {skipped_ingredients}'
            ))
        return created

    @staticmethod
    def _email_of(username: str) -> str:
        for u in USERS:
            if u['username'] == username:
                return u['email']
        raise ValueError(f'Unknown seed username: {username}')
