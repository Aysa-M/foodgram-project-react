from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import filters, status, viewsets
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.permissions import (SAFE_METHODS,
                                        AllowAny,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from djoser.views import UserViewSet
from django_filters.rest_framework import DjangoFilterBackend

from users.models import Subscription, User
from recipes.models import (Favorite, Ingredient, Addamount, Recipe,
                            ShoppingCart, Tag)
from .filters import (IngredientSearchFilter,
                      RecipeFilter)
from .mixins import (ListViewSet, ListRetrieveViewSet)
from .pagination import FoodGramPagination
from .permissions import (IsAdminOrReadOnly,
                          IsAuthorOnly,)
from .serializers import (CustomUserSerializer,
                          AccountSerializer,
                          FavoriteSerializer, IngredientSerializer,
                          RecipeListRetrieveSerializer,
                          RecipeManipulationSerializer,
                          ShoppingCartSerializer, SubscriptionSerializer,
                          TagSerializer)


class CustomUserViewSet(UserViewSet):
    """
    Handler function for the processing GET requests: List of users,
    user's profile, current user.
    """
    serializer_class = CustomUserSerializer
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    lookup_field = 'id'
    pagination_class = FoodGramPagination
    http_method_names = ['get', 'head', 'post']

    @action(
        methods=('GET', 'PATCH',),
        detail=False,
        url_path='me',
        serializer_class=AccountSerializer,
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_200_OK)


class SubscriptionViewSet(ListViewSet):
    """
    Handler function for the processing GET requests for
    subscriptions.
    """
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = (IsAuthorOnly,)
    pagination_class = FoodGramPagination
    http_method_names = ('get', )

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)


class SubscriptionCreateDeleteAPIView(APIView):
    """
    Handler function for the processing POST, DEL requests for
    subscriptions.
    """
    serializer_class = SubscriptionSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ('post', 'delete', )

    def post(self, request, id) -> Subscription:
        """
        Create new subscription for the request user.
        """
        data = {'user': request.user.id, 'author': id}
        serializer = SubscriptionSerializer(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED)

    def delete(self, request, id) -> None:
        """
        Delete a chosen subscription from the request user subscriptions list.
        """
        user = request.user
        author = get_object_or_404(User, id=id)
        subscription = get_object_or_404(
            Subscription, user=user, author=author)
        if subscription:
            subscription.delete()
            return Response('Вы отписались от автора.',
                            status=status.HTTP_204_NO_CONTENT)
        return Response('Вы не подписаны на пользователя',
                        status=status.HTTP_400_BAD_REQUEST)


class IngredientViewSet(ListRetrieveViewSet):
    """
    Handler function for the processing GET requests for ingredients /
    ingredient.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filterset_class = IngredientSearchFilter
    search_fields = ('^name')


class TagViewSet(ListRetrieveViewSet):
    """
    Handler function for the processing GET requests for tags / tag.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Handler function for the whole processing of the Recipe objects through
    the further requests: GET, POST, PATCH, DEL.
    """
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = FoodGramPagination
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    filterset_class = RecipeFilter
    filterset_fields = ('tags', 'author',
                        'is_favorited', 'is_in_shopping_cart',)
    search_fields = ('$name', )
    http_method_names = ('get', 'post', 'patch', 'delete',)

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method in SAFE_METHODS:
            return RecipeListRetrieveSerializer
        return RecipeManipulationSerializer

    def perform_create(self, serializer) -> Recipe:
        serializer.save(author=self.request.user)

    def favorite_adding(self, request, recipe) -> Favorite:
        """Put the current recipe into a favorites"""
        data = {'user': request.user.id, 'recipe': recipe}
        serializer = FavoriteSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED)

    def delete_from_favorit(self, request, recipe) -> None:
        """
        Delete a chosen recipe from the request user favorite list.
        """
        favorite = Favorite.objects.filter(user=request.user,
                                           recipe=recipe)
        if favorite.exists():
            favorite.delete()
            return Response(
                'Рецепт удален из Избранного.',
                status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'В Избранном такого рецепта нет.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        methods=('post', 'delete',),
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return self.favorite_adding(request, recipe.id)
        return self.delete_from_favorit(request, recipe.id)

    @action(methods=('GET',),
            detail=False,
            url_path='download_shopping_cart',
            serializer_class=ShoppingCartSerializer,
            permission_classes=(IsAuthorOnly,))
    def download_shopping_cart(self, request):
        ingredients = Addamount.objects.filter(
            recipe__cart__user=request.user).values(
                'ingredients__name', 'ingredients__measurement_unit'
        ).annotate(total=Sum('amount'))
        shopping_cart = '\n'.join([
            f'{ingredient["ingredients__name"]} - {ingredient["total"]} '
            f'{ingredient["ingredients__measurement_unit"]}'
            for ingredient in ingredients
        ])
        filename = 'shopping_cart.txt'
        response = HttpResponse(shopping_cart, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    def add_to_shopping_cart(self, request, recipe) -> ShoppingCart:
        """Put the current recipe into a cart"""
        data = {'user': request.user.id, 'recipe': recipe}
        serializer = ShoppingCartSerializer(
            data=data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED)

    def delete_from_shopping_cart(self, request, recipe) -> None:
        """
        Delete a chosen recipe from the request user favorite list.
        """
        cart = ShoppingCart.objects.filter(user=request.user,
                                           recipe=recipe)
        if cart.exists():
            cart.delete()
            return Response(
                'Рецепт удален из Списка покупок.',
                status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'В корзине такого рецепта нет.'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=('post', 'delete',),
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            return self.add_to_shopping_cart(request, recipe.id)
        return self.delete_from_shopping_cart(request, recipe.id)
