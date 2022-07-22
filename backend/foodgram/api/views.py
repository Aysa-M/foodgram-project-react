from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.contrib.auth.hashers import make_password

from reportlab.pdfgen import canvas

from djoser.views import UserViewSet

from rest_framework import status, viewsets, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import (IsAuthenticated,
                                        AllowAny)
from django_filters.rest_framework import DjangoFilterBackend

from recipes.models import (Ingredient,
                            Tag,
                            Recipe,
                            IngredientRecipe,
                            Favorite,
                            ShoppingCart)
from users.models import User, Subscriptions

from .serializers import (CustomUserSerializer,
                          SignUpSerializer,
                          AccountSerializer,
                          SubscriptionsSerializer,
                          IngredientSerializer,
                          TagSerializer,
                          RecipeListRetrieveSerializer,
                          RecipeManipulationSerializer,
                          FavoriteSerializer,
                          ShoppingCartSerializer)
from .mixins import (ListRetrieveViewSet,
                     ListCreateDestroyViewSet,
                     CreateDestroyViewSet,)
from .permissions import (IsAdmin,
                          IsAuthorOnly,
                          IsAuthorOrReadOnly,)
from .pagination import FoodGramPagination

from .filters import RecipeFilter


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
    http_method_names = ['get']

    @action(
        methods=('GET', 'PATCH',),
        detail=False,
        url_path='me/',
        serializer_class=AccountSerializer,
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        user = get_object_or_404(User, pk=request.user.id)
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny,))
def sign_up(request) -> User:
    """
    Handler function for registration new accounts for users.
    """
    serializer = SignUpSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email']
    username = serializer.validated_data['username']
    first_name = serializer.validated_data['first_name']
    last_name = serializer.validated_data['last_name']
    password = make_password(serializer.validated_data['password'])
    user, created = User.objects.get_or_create(
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email,
        password=password,
    )
    return Response(user, status=status.HTTP_201_CREATED)


class SubscriptionsViewSet(ListCreateDestroyViewSet):
    """
    Handler function for the processing GET, POST, DEL requests for
    subscriptions.
    """
    queryset = Subscriptions.objects.all()
    serializer_class = SubscriptionsSerializer
    permission_classes = (IsAdmin, IsAuthorOnly,)
    pagination_class = FoodGramPagination

    def get_queryset(self) -> Subscriptions:
        """
        Get a list of request user subscriptions.
        """
        return get_object_or_404(Subscriptions, user=self.request.user)

    def perform_create(self, serializer) -> Subscriptions:
        """
        Create new subscription for the request user.
        """
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs) -> Subscriptions:
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        self.perform_create(serializer)
        serializer = SubscriptionsSerializer(
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
        subscription = Subscriptions.objects.filter(user=request.user,
                                                    author=author_id)
        if subscription:
            subscription.delete()
            return Response('Вы отписались от автора.',
                            status=status.HTTP_204_NO_CONTENT)
        return Response('Вы не подписаны на пользователя',
                        status=status.HTTP_400_BAD_REQUEST)

    def perform_destroy(self, instance) -> None:
        """
        Delete a chosen subscription from the request user subscriptions list.
        """
        return instance.delete()


class IngredientViewSet(ListRetrieveViewSet):
    """
    Handler function for the processing GET requests for ingredients /
    ingredient.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, )
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

    def create(self, request, *args, **kwargs) -> Recipe:
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        self.perform_create(serializer)
        serializer = RecipeManipulationSerializer(
            instance=serializer.instance,
            context={'request': self.request}
        )
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED,
                        headers=headers)

    def perform_update(self, serializer) -> Recipe:
        return super().perform_update(serializer)

    def update(self, request, *args, **kwargs) -> Recipe:
        serializer = self.get_serializer(data=request.data)
        partial = kwargs.pop('partial')
        instance = self.get_object()
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        self.perform_update(instance, data=request.data, partial=partial)
        serializer = RecipeManipulationSerializer(
            instance=serializer.instance,
            context={'request': self.request}
        )
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data,
                        status=status.HTTP_200_OK,
                        headers=headers)

    def perform_destroy(self, instance) -> None:
        return super().perform_destroy(instance)


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

    def create(self, request, *args, **kwargs) -> Favorite:
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        self.perform_create(serializer)
        serializer = FavoriteSerializer(
            instance=serializer.instance,
            context={'request': self.request}
        )
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED,
                        headers=headers)

    def delete(self, request, *args, **kwargs) -> None:
        """
        Delete a chosen recipe from the request user favorite list.
        """
        recipe_id = get_object_or_404(Recipe, id=self.kwargs.get('recipe_id'))
        favorite = Favorite.objects.filter(user=request.user,
                                           recipe=recipe_id)
        if favorite:
            favorite.delete()
            return Response(
                'Рецепт удален из Избранного.',
                status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'В Избранном такого рецепта нет.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    def perform_destroy(self, instance) -> None:
        """
        Delete a chosen recipe from the request user favorite list.
        """
        return instance.delete()


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
            recipe__user_cart__user=request.user).prefetch_related(Ingredient)
        for field in ingredients:
            name = field[0]
            if name not in buffer:
                buffer[name] = {
                    'measurement_unit': field[1],
                    'amount': field[2]
                }
            else:
                buffer[name]['amount'] += field[2]
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
                                                    recipe=recipe_id)
        if shopping_cart:
            shopping_cart.delete()
            return Response(
                'Рецепт успешно удален из списка покупок.',
                status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'В списке покупок такого рецепта нет.'},
            status=status.HTTP_400_BAD_REQUEST
        )
