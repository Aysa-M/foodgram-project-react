from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from .validators import validate_not_empty

USER = settings.AUTH_USER_MODEL


class Ingredient(models.Model):
    """
    Class's used for creation of ingredients for recipes.
    """
    name = models.CharField(
        verbose_name='Название ингридиента',
        max_length=200,
        blank=False
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=200,
        blank=False
    )

    class Meta:
        """
        Service class for metadata of the Ingredients model.
        """
        ordering = ['name']
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'

    def __str__(self) -> str:
        """
        Output the information about the ingredient's measurement.
        """
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    """
    Class's used for creation of tags for recipes. One recipe
    can include many tags.
    """
    name = models.CharField(
        verbose_name='Название тега',
        max_length=200,
        unique=True,
        blank=False
    )
    color = models.CharField(
        verbose_name='Цветовой HEX-код',
        default='#337f37',
        max_length=7,
        unique=True,
        blank=False
    )
    slug = models.SlugField(
        verbose_name='slug тега',
        blank=False,
        unique=True,
        max_length=200,
        db_index=True,
        error_messages={
            'unique': 'Выбранный slug уже существует.',
        }
    )

    class Meta:
        """
        Service class for metadata of the Tags model.
        """
        ordering = ['id', ]
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        db_table = 'slug'
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'slug',),
                name='unique_slug'),
            models.CheckConstraint(
                name='not_double_slug',
                check=~models.Q(name=models.F('slug')),
            )
        ]

    def __str__(self) -> str:
        """
        Output the information about the tag.
        """
        return f'{self.name}'


class Recipe(models.Model):
    """
    Class's used for creation objects of model Recipe - recipes.
    """
    author = models.ForeignKey(
        USER,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта',
        blank=True,
        null=True,
        db_index=True
    )
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=200,
        blank=False,
        validators=[validate_not_empty]
    )
    image = models.ImageField(
        'Изображение',
        upload_to='recipes/',
        blank=False
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
        help_text='Добавьте сюда ваш рецепт',
        max_length=10000,
        validators=[validate_not_empty],
        blank=False
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        related_name='recipes',
        verbose_name='Список ингредиентов',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
        blank=False
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления в минутах.',
        blank=False,
        null=False,
        validators=[MinValueValidator(
            1, message='Минимальное время приготовления = 1 минута.')]
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        """
        Service class for metadata of the Recipe model.
        """
        ordering = ['-pub_date', ]
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self) -> str:
        """
        Output the full description of the recipe.
        """
        return self.text

    def get_absoulute_url(self):
        return reverse('recipe', args=[self.pk])


class IngredientRecipe(models.Model):
    """
    Class's used for the link between recipe and its ingredient.
    """
    ingredients = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_for_recipe',
        verbose_name='Ингредиент',
        null=True,
    )
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               null=True,
                               related_name='igredients_recipes')
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество ингридиента для рецепта',
        blank=False,
        null=False,
        validators=[MinValueValidator(
            1, message='Минимальное количество должно быть не меньше 1.')]
    )

    class Meta:
        """
        Service class for metadata of IngredientRecipe model.
        """
        verbose_name = 'Количество ингридиента для рецепта'
        verbose_name_plural = 'Количество ингридиента для рецептов'
        db_table = 'ingredient_recipe'
        constraints = [
            models.UniqueConstraint(
                fields=('ingredients', 'amount',),
                name='unique_ingredient_amount'),
            models.CheckConstraint(
                name='not_double_ingredient_amount',
                check=~models.Q(ingredients=models.F('amount')),
            )
        ]

    def __str__(self) -> str:
        """
        Output the full description of the ingredient for recipe.
        """
        return (f'{self.ingredients} - {self.amount}')


class Favorite(models.Model):
    """
    Class's used for adding favourite recipe into the user's special list.
    """
    user = models.ForeignKey(
        USER,
        on_delete=models.CASCADE,
        related_name='user_favorite',
        verbose_name='Пользователь',
        blank=False
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт',
        blank=False
    )

    class Meta:
        """
        Service class for metadata of Favorite model.
        """
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        db_table = 'favorites'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe',),
                name='unique_user_favorites'),
            models.CheckConstraint(
                name='not_double_favorites',
                check=~models.Q(user=models.F('recipe')),
            )
        ]


class ShoppingCart(models.Model):
    """
    Class's used for adding favourite recipe into the user's shopping list.
    """
    user = models.ForeignKey(
        USER,
        on_delete=models.CASCADE,
        related_name='user_cart',
        verbose_name='Пользователь',
        blank=False
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name='Рецепт',
        blank=False
    )

    class Meta:
        """
        Service class for metadata of ShoppingCart model.
        """
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        db_table = 'cart'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe',),
                name='unique_shopping_cart'),
            models.CheckConstraint(
                name='not_double_cart',
                check=~models.Q(user=models.F('recipe')),
            )
        ]
