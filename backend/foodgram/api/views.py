from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from djoser.views import UserViewSet
from django_filters.rest_framework import DjangoFilterBackend
from reportlab.pdfgen import canvas

from users.models import Subscription, User
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from .filters import RecipeFilter
from .mixins import (CreateDestroyViewSet, ListCreateDestroyViewSet,
                     ListRetrieveViewSet)
from .pagination import FoodGramPagination
from .permissions import IsAdmin, IsAuthorOnly, IsAuthorOrReadOnly
from .serializers import (CustomUserSerializer, AccountSerializer, FavoriteSerializer,
                          IngredientSerializer, RecipeListRetrieveSerializer,
                          RecipeManipulationSerializer, ShoppingCartSerializer,
                          SubscriptionSerializer, TagSerializer)


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


class SubscriptionViewSet(ListCreateDestroyViewSet):
    """
    Handler function for the processing GET, POST, DEL requests for
    subscriptions.
    """
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = (IsAdmin, IsAuthorOnly,)
    pagination_class = FoodGramPagination

    def get_queryset(self) -> Subscription:
        """
        Get a list of request user subscriptions.
        """
        return Subscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer) -> Subscription:
        """
        Create new subscription for the request user.
        """
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs) -> Subscription:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.perform_create(serializer)
        serializer = SubscriptionSerializer(
            instance=serializer.instance,
            context={'request': self.request}
        )
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED,
                        headers=headers)

    def delete(self, request, *args, **kwargs) -> None:
        """
        Delete a chosen subscription from the request user subscriptions list.
        """
        author_id = get_object_or_404(User, id=self.kwargs.get('author_id'))
        subscription = Subscription.objects.filter(user=request.user,
                                                   author=author_id).exists()
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
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    search_fields = ('$name', )


class TagViewSet(ListRetrieveViewSet):
    """
    Handler function for the processing GET requests for tags / tag.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Handler function for the whole processing of the Recipe objects through
    the further requests: GET, POST, PATCH, DEL.
    """
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticated, IsAuthorOrReadOnly,)
    pagination_class = FoodGramPagination
    http_method_names = ['get', 'post', 'patch', 'delete', ]
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    filterset_class = RecipeFilter
    filterset_fields = ('tags', 'author',
                        'is_favorited', 'is_in_shopping_cart',)
    search_fields = ('$name', )

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == 'get':
            return RecipeListRetrieveSerializer
        return RecipeManipulationSerializer

    def perform_create(self, serializer) -> Recipe:
        serializer.save(author=self.request.user)


class FavoriteViewSet(CreateDestroyViewSet):
    """
    Handler function for the processing POST and DEL requests for
    favorits of the request user.
    """
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = (IsAuthenticated, IsAuthorOnly, IsAdmin,)

    def perform_create(self, serializer) -> Favorite:
        """
        Create new subscription for the request user.
        """
        serializer.save(user=self.request.user)

    def delete(self, request, *args, **kwargs) -> None:
        """
        Delete a chosen recipe from the request user favorite list.
        """
        recipe_id = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        favorite = Favorite.objects.filter(user=request.user,
                                           recipe=recipe_id).exists()
        if favorite:
            favorite.delete()
            return Response(
                'Рецепт удален из Избранного.',
                status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'В Избранном такого рецепта нет.'},
            status=status.HTTP_400_BAD_REQUEST
        )


class ShoppingCartViewSet(ListRetrieveViewSet, ListCreateDestroyViewSet):
    """
    Handler function for the processing GET, POST, DEL requests for
    shopping cart list.
    """
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    permission_classes = (IsAuthenticated, IsAuthorOnly, IsAdmin,)

    @action(methods=['GET'],
            permission_classes=[IsAuthenticated, IsAuthorOnly, ],
            detail=False)
    def download_shopping_cart(self, request) -> None:
        """
        Authorised request user who's an owner of shopping cart
        download shopping list provided by recipes.
        """
        buffer = {}
        ingredients = IngredientRecipe.objects.filter(
            recipe__user_cart__user=request.user).values(
                'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(total=Sum('amount'))
        for field in ingredients:
            name = field[0]
            if name not in buffer:
                buffer[name] = {
                    'name': field[1],
                    'measurement_unit': field[2],
                    'total': field[3]
                }
            else:
                buffer[name]['total'] += field[3]
        shopping_list = canvas.Canvas(buffer)
        shopping_list.drawString(100, 100, 'Список покупок')
        shopping_list.showPage()
        shopping_list.save()
        shopping_list.seek(0)
        return FileResponse(shopping_list,
                            as_attachment=True,
                            filename='shopping_list.pdf')

    @action(methods=['POST'],
            permission_classes=[IsAuthenticated, IsAuthorOnly, ],
            detail=False)
    def perform_create(self, serializer) -> ShoppingCart:
        """
        Create new shopping cart for the request user.
        """
        serializer.save(user=self.request.user)

    @action(methods=['DELETE'],
            permission_classes=[IsAuthenticated, IsAuthorOnly, ],
            detail=False)
    def delete(self, request, *args, **kwargs) -> None:
        """
        Delete a chosen recipe from the request user favorite list.
        """
        recipe_id = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        shopping_cart = ShoppingCart.objects.filter(user=request.user,
                                                    recipe=recipe_id).exists()
        if shopping_cart:
            shopping_cart.delete()
            return Response(
                'Рецепт успешно удален из списка покупок.',
                status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'В списке покупок такого рецепта нет.'},
            status=status.HTTP_400_BAD_REQUEST
        )
