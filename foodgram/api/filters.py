from django_filters.rest_framework import (FilterSet,
                                           filters,)
from rest_framework.filters import BaseFilterBackend

from recipes.models import Ingredient, Recipe


class IngredientSearchFilter(FilterSet):
    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class IsOwnerFilterBackend(BaseFilterBackend):
    """
    Filter allows get objects if you are their author.
    """
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(author=request.user)


class RecipeFilter(FilterSet):
    """
    Filters shown recipes by tags, author, is_favorited and
    is_in_shopping_cart.
    """
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(cart__user=self.request.user)
        return queryset
