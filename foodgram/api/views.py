from django.db.models import Sum
from django.http import FileResponse
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
from reportlab.pdfgen import canvas

from users.models import Subscription, User
from recipes.models import (Favorite, Ingredient, Addamount, Recipe,
                            ShoppingCart, Tag)
from .filters import (IsOwnerFilterBackend,
                      RecipeFilter)
from .mixins import (ListViewSet, ListRetrieveViewSet)
from .pagination import FoodGramPagination
from .permissions import (IsAdminOrReadOnly,
                          IsAuthorOnly,
                          IsAuthorOrAdminOrReadOnly,)
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
    filter_backends = (DjangoFilterBackend,)
    filter_class = IsOwnerFilterBackend
    permission_classes = (IsAuthorOnly,)
    pagination_class = FoodGramPagination
    http_method_names = ('get', )


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
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ('$name')


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
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    pagination_class = FoodGramPagination
    filter_backends = (DjangoFilterBackend, filters.SearchFilter,)
    filterset_class = RecipeFilter
    filterset_fields = ('tags', 'author',
                        'is_favorited', 'is_in_shopping_cart',)
    search_fields = ('$name', )
    http_method_names = ('get', 'post', 'put', 'patch', 'delete',)

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method in SAFE_METHODS:
            return RecipeListRetrieveSerializer
        return RecipeManipulationSerializer

    def perform_create(self, serializer) -> Recipe:
        serializer.save(author=self.request.user)

    @action(
        methods=('GET', 'DELETE',),
        detail=True,
        permission_classes=(IsAuthenticated,),
        url_path='favorite'
    )
    def favorite(self, request, id) -> Favorite:
        recipe = get_object_or_404(Recipe, id=id)
        if request.method == 'GET':
            favorited, created = Favorite.objects.get_or_create(
                user=request.user, recipe=recipe
            )
            if created:
                serializer = FavoriteSerializer()
                return Response(
                    serializer.to_representation(instance=favorited),
                    status=status.HTTP_201_CREATED
                )
        elif request.method == 'DELETE':
            favorited = Favorite.objects.get(user=request.user, recipe=recipe)
            favorited.delete()
            return Response('Рецепт удален из Избранного.',
                            status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=('GET', 'DELETE',),
        detail=True,
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart'
    )
    def shopping_cart(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        if request.method == 'GET':
            incart, created = ShoppingCart.objects.get_or_create(
                user=request.user, recipe=recipe
            )
            if created:
                serializer = ShoppingCartSerializer()
                return Response(
                    serializer.to_representation(instance=incart),
                    status=status.HTTP_201_CREATED
                )
        elif request.method == 'DELETE':
            cart = ShoppingCart.objects.get(
                user=request.user, recipe=recipe)
            cart.delete()
            return Response('Рецепт удален из списка покупок.',
                            status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=('GET',),
            detail=False,
            url_path='download_shopping_cart',
            serializer_class=ShoppingCartSerializer,
            permission_classes=(IsAuthorOnly,))
    def download_shopping_cart(self, request) -> None:
        """
        Authorised request user who's an owner of shopping cart
        download shopping list provided by recipes.
        """
        buffer = {}
        ingredients = Addamount.objects.filter(
            recipe__cart__user=request.user).values(
                'ingredients__name', 'ingredients__measurement_unit'
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
