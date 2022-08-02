from django.db.models import IntegerField, Value
from django_filters.rest_framework import (FilterSet,
                                           filters,
                                           CharFilter,)
from rest_framework.filters import SearchFilter, BaseFilterBackend

from recipes.models import Ingredient, Recipe


class IngredientSearchFilter(SearchFilter):
    name = CharFilter(method='search_name_ingredient')

    class Meta:
        model = Ingredient
        fields = ('name',)

    def search_name_ingredient(self, queryset, name, value):
        if not value:
            return queryset
        start_with_queryset = (
            queryset.filter(name__istartswith=value).annotate(
                order=Value(0, IntegerField())
            )
        )
        contain_queryset = (
            queryset.filter(name__icontains=value).exclude(
                id__in=(ingredient.id for ingredient in start_with_queryset)
            ).annotate(
                order=Value(1, IntegerField())
            )
        )
        return start_with_queryset.union(contain_queryset).order_by('order')


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
