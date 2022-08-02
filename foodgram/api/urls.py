from django.urls import include, path
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter

from .views import (CustomUserViewSet, FavoriteViewSet, IngredientViewSet,
                    RecipeViewSet, ShoppingCartViewSet,
                    SubscriptionCreateDeleteAPIView,
                    SubscriptionViewSet, TagViewSet)

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='users_list')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'recipes/(?P<recipe_id>\d+)/favorite',
                FavoriteViewSet,
                basename='shopping_cart')
router.register(r'recipes/(?P<recipe_id>\d+)/shopping_cart',
                ShoppingCartViewSet,
                basename='shopping_cart')

app_name = 'api'

urlpatterns = [
    path(
        'docs/',
        TemplateView.as_view(template_name='redoc.html'),
        name='docs'
    ),
    path(
        'users/<int:id>/subscribe/',
        SubscriptionCreateDeleteAPIView.as_view(),
        name='subscribe'),
    path(
        'users/subscriptions/',
        SubscriptionViewSet.as_view({'get': 'list'}),
        name='subscriptions'
    ),
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
