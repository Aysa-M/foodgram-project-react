from django_filters.rest_framework import FilterSet, filters
from rest_framework.filters import SearchFilter, BaseFilterBackend

from recipes.models import Recipe


class IngredientSearchFilter(SearchFilter):
    def get_search_fields(self, view, request):
        if request.query_params.get('name'):
            return['name']
        return super(
            IngredientSearchFilter, self
        ).get_search_fields(view, request)


class IsOwnerFilterBackend(BaseFilterBackend):
    """
    Фильтр, позволяющий пользователям видеть только свои собственные объекты.
    """
    def filter_queryset(self, request, queryset, view):
        return queryset.filter(author=request.user)


class RecipeFilter(FilterSet):
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
            return queryset.filter(user_cart__user=self.request.user)
        return queryset
