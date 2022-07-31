from django.contrib import admin

from foodgram.settings import EMPTY_VALUE_DISPLAY
from .models import (Favorite, Ingredient, Addamount, Recipe,
                     ShoppingCart, Tag)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)
    search_fields = ('name',)
    empty_value_display = EMPTY_VALUE_DISPLAY


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'color', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('name',)
    search_fields = ('name', 'slug',)
    list_editable = ('name',)
    empty_value_display = EMPTY_VALUE_DISPLAY


class IngredientInLine(admin.TabularInline):
    model = Addamount


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'text',)
    inlines = [
        IngredientInLine,
    ]
    list_filter = ('author', 'name', 'tags', 'ingredients')
    search_fields = ('name',)
    readonly_fields = ('in_favorites',)
    empty_value_display = EMPTY_VALUE_DISPLAY

    @staticmethod
    def in_favorites(obj: Recipe) -> int:
        """
        Count and display total of adding the recipe into Favorite on its page.
        """
        return obj.favorites.count()


@admin.register(Addamount)
class IngredientRecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'ingredients', 'amount',)
    list_editable = ('ingredients', 'amount',)
    list_filter = ('ingredients',)
    search_fields = ('ingredient_for_recipe__name',)
    empty_value_display = EMPTY_VALUE_DISPLAY

    @ admin.display(description='Ингредиенты')
    def get_ingredients(self, obj):
        return '\n'.join([
            f'{item["ingredient__name"]} - {item["amount"]}'
            f'{item["ingredient__measurement_unit"]}.'
            for item in obj.recipe.values(
                'ingredient__name',
                'amount', 'ingredient__measurement_unit')])


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe',)
    list_editable = ('user', 'recipe',)
    list_filter = ('user', 'recipe',)
    search_fields = ('user', 'recipe',)
    empty_value_display = EMPTY_VALUE_DISPLAY


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe',)
    list_editable = ('user', 'recipe',)
    list_filter = ('user', 'recipe',)
    search_fields = ('user', 'recipe',)
    empty_value_display = EMPTY_VALUE_DISPLAY
