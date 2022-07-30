from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CustomUserViewSet, FavoriteViewSet, IngredientViewSet,
                    RecipeViewSet, ShoppingCartViewSet, SubscriptionCDViewSet,
                    SubscriptionViewSet, TagViewSet)

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='users_list')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'recipes/(?P<recipe_id>\d+)/shopping_cart',
                ShoppingCartViewSet,
                basename='shopping_cart')
router.register(r'recipes/download_shopping_cart', ShoppingCartViewSet,
                basename='shopping_list_pdf')
router.register(r'recipes/(?P<recipe_id>\d+)/favorite',
                FavoriteViewSet,
                basename='shopping_cart')

app_name = 'api'
urlpatterns = [
    path('', include(router.urls)),
    path('users/<int:id>/subscribe/', SubscriptionCDViewSet, name='subscribe'),
    path('users/subscriptions/', SubscriptionViewSet, name='subscriptions'),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
