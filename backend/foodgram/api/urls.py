from django.urls import include, path
from rest_framework import routers

from api.views import (CustomUserViewSet, FavoriteViewSet, IngredientViewSet,
                       RecipeViewSet, ShoppingCartViewSet,
                       SubscriptionsViewSet, TagViewSet, sign_up)

router = routers.DefaultRouter()
router.register(r'users/me', CustomUserViewSet, basename='current_user')
router.register(r'users/(?P<user_id>\d+)/subscribe/',
                SubscriptionsViewSet,
                basename='user_subscriptions'),
router.register(r'users/subscriptions/', SubscriptionsViewSet,
                basename='subscriptions'),
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

urlpatterns = [
    path('users/', sign_up, name='signup'),
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
