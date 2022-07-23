from typing import Dict

from django.shortcuts import get_object_or_404
from django.urls import reverse
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from foodgram.settings import FALSE_RESULT, MINIMUM

from rest_framework import exceptions, serializers, status, validators

from users.models import Subscription, User

from recipes.models import (Favorite, Ingredient, IngredientRecipe,
                            Recipe, ShoppingCart, Tag)

from .validators import password_verification

DICT_TYPES = Dict[int, str]


class CustomUserSerializer(UserSerializer):
    """
    Serializer / deserializer from djoser for model User: GET - List of users,
    user's profile, current user.
    """
    is_subscribed = serializers.SerializerMethodField(
        method_name='get_is_subscribed')

    class Meta:
        model = User
        fields = ('email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed',)
        read_only_fields = ('email',
                            'id',
                            'username',
                            'first_name',
                            'last_name',
                            'is_subscribed',)
        validators = [
            validators.UniqueTogetherValidator(
                queryset=User.objects.all(),
                fields=('username', 'email',),
                message=(
                    'Комбинация логин-email не совпадают.'
                )
            )
        ]

    def get_is_subscribed(self, obj: User) -> bool:
        """Checks if a current user had subscrubed to the author's account"""
        user = self.context.get('request').user
        url = reverse('api:current_user-me', args=[user.pk])
        if self.context.get('request').path_info == url:
            return False
        if user.role == (user.is_user or user.is_admin):
            return Subscription.objects.filter(user=user, author=obj).exists()
        return False

    def validate_user(self, value: DICT_TYPES) -> None:
        """Uniqueness' validation for username and email fields."""
        user = self.context.get('request').user
        if not user.id:
            raise exceptions.NotFound(
                detail='Страница не найдена.',
                code=status.HTTP_404_NOT_FOUND
            )
        return value


class SignUpSerializer(UserCreateSerializer):
    """Serializer / deserializer of data while signing user up in system."""
    email = serializers.EmailField(
        max_length=254,
        validators=[validators.UniqueValidator(
            queryset=User.objects.all(),
            message='email уже зарегистрирован в системе. Попробуйте снова',
        )]
    )
    username = serializers.CharField(
        max_length=150,
        validators=[validators.UniqueValidator(
            queryset=User.objects.all(),
            message='Такой логин уже занят. Попробуйте снова.',
        )]
    )

    class Meta:
        model = User
        fields = ('id', 'email', 'username',
                  'first_name', 'last_name', 'password',)
        extra_kwargs = {'password': {'write_only': True}}

    def validate_username(self, username: str) -> bool:
        """Validation of user's username"""
        if username in ('me', 'Me', 'ME', 'mE', 'mE'):
            raise serializers.ValidationError('Недопустимое имя')
        return username

    def validate(self, data: DICT_TYPES) -> None:
        """Uniqueness' validation for username and email fields."""
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        password_verification(password)
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                detail='Пофантазируйте ещё.',
                code=status.HTTP_400_BAD_REQUEST
            )
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                detail=('Кажется, вы пытаетесь использовать этот '
                        'email повторно.'),
                code=status.HTTP_400_BAD_REQUEST)
        return data


class AccountSerializer(CustomUserSerializer):
    """Checks the role of the request user."""
    role = serializers.CharField(read_only=True)


class PartialRecipeSerializer(serializers.ModelSerializer):
    """
    Serializer / deserializer of author's recipes for getting the list
    of subscriptions by GET request from current user.
    """

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class SubscriptionSerializer(CustomUserSerializer):
    """
    Serializer / deserializer to get the list of subscriptions
    of the GET request user.
    """
    recipes = serializers.SerializerMethodField(method_name='get_recipes')
    recipes_count = serializers.SerializerMethodField(
        method_name='get_recipes_count'
    )

    class Meta:
        model = User
        fields = ('email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed',
                  'recipes',
                  'recipes_count',)

    def get_recipes(self, obj: User) -> Recipe:
        """
        Collect the recipes of the author which is following by request user.
        """
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.only('id', 'name', 'image', 'cooking_time')
        if limit:
            recipes = recipes[:int(limit)]
        return PartialRecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, obj: User) -> int:
        """
        Count the recipes of the author which is following by request user.
        """
        user = self.context.get('request').user
        if user.is_authenticated:
            return Recipe.objects.filter(author=obj).count()
        else:
            raise exceptions.NotAuthenticated(
                detail='Учетные данные не были предоставлены.',
                code=status.HTTP_401_UNAUTHORIZED
            )

    def validate(self, data) -> bool:
        """
        Checks user's subscription.
        """
        sub_id = data.get('id')
        user_id = data.get('user_id')
        author_id = data.get('author_id')
        subscription = get_object_or_404(Subscription,
                                         id=sub_id,
                                         user=user_id,
                                         author=author_id)
        if subscription:
            raise serializers.ValidationError(
                detail=(f'Вы уже подписаны на {author_id}.'),
                code=status.HTTP_400_BAD_REQUEST
            )
        if user_id == author_id:
            raise serializers.ValidationError(
                detail='Вы не можете подписаться на самого себя.',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer / deserializer for model Ingredients."""
    id = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """
    Serializer / deserializer for counting amount of ingredient in a
    current recipe. The class links class Ingredient with class Recipe.
    """
    id = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Ingredient.objects.all()
    )
    name = serializers.ReadOnlyField(
        source='ingredient_for_recipe.name'
    )

    measurement_unit = serializers.ReadOnlyField(
        source='ingredient_for_recipe.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class IngredientCUDRecipeSerializer(serializers.ModelSerializer):
    """
    Serializer / deserializer for CUD (create, update and delete) operations
    with recipes.
    """
    id = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Ingredient.objects.all()
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')
        extra_kwargs = {
            'id': {
                'read_only': False,
                'error_messages': {
                    'does_not_exist': 'Такого ингредиента не существует.',
                }
            },
            'amount': {
                'error_messages': {
                    'min_value': ('Количество ингредиента не может быть '
                                  'меньше {min_value}.').format(
                        min_value=MINIMUM
                    ),
                }
            }
        }


class TagSerializer(serializers.ModelSerializer):
    """Serializer / deserializer for model Tags."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug',)


class RecipeListRetrieveSerializer(serializers.ModelSerializer):
    """
    Serializer / deserializer for model Recipe.
    GET request: showing list of recipes.
    """
    tags = TagSerializer(many=True)
    author = CustomUserSerializer()
    ingredients = IngredientRecipeSerializer(many=True,
                                             source='igredients_recipes')
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited'
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('id',
                  'tags',
                  'author',
                  'ingredients',
                  'is_favorited',
                  'is_in_shopping_cart',
                  'name',
                  'image',
                  'text',
                  'cooking_time',)

    def get_is_favorited(self, obj: User) -> bool:
        """
        Method for serializer field checking if the recipe is
        in personal favorite list of a request user.
        """
        if self.context.get('request').method == 'POST':
            return False
        user = self.context.get('request').user
        recipe = self.context.get('recipe_id')
        if user.is_authenticated:
            return Favorite.objects.filter(user=obj, recipe=recipe).exists()
        return False

    def get_is_in_shopping_cart(self, obj: User) -> bool:
        """
        Method for serializer field checking if the recipe is
        in shopping cart of a request user.
        """
        if self.context.get('request').method == 'POST':
            return False
        user = self.context.get('request').user
        recipe = self.context.get('recipe_id')
        if user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=obj,
                recipe=recipe
            ).exists()
        return False


class RecipeManipulationSerializer(serializers.ModelSerializer):
    """
    Serializer / deserializer for model Recipe.
    POST, PATCH, DELETE requests: creation, update and deletion.
    """
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientCUDRecipeSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('author',
                  'ingredients',
                  'tags',
                  'image',
                  'name',
                  'text',
                  'cooking_time',)

    def validate(self, data: DICT_TYPES) -> None:
        """Validation data for recipe fields."""
        tags = data.get('tags')
        image = data.get('image')
        name = data.get('name')
        text = data.get('text')
        cooking_time = data.get('cooking_time')
        if not tags:
            raise serializers.ValidationError(
                detail='Необходимо выбрать теги',
                code=status.HTTP_400_BAD_REQUEST
            )
        if not image:
            raise serializers.ValidationError(
                detail='Загрузите фото рецепта',
                code=status.HTTP_400_BAD_REQUEST
            )
        if not name:
            raise serializers.ValidationError(
                detail='Укажите название рецепта',
                code=status.HTTP_400_BAD_REQUEST
            )
        if not text:
            raise serializers.ValidationError(
                detail='Необходимо описание приготовления блюда',
                code=status.HTTP_400_BAD_REQUEST
            )
        if not cooking_time or cooking_time <= FALSE_RESULT:
            raise serializers.ValidationError(
                detail='Укажите время приготовления',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    def validate_ingredients(self, data: DICT_TYPES) -> None:
        """Validation ingredients data."""
        ingredients = data.get('ingredients')
        if not ingredients or len(ingredients) == FALSE_RESULT:
            raise serializers.ValidationError(
                detail=('Укажите название и количество '
                        'ингредиентов в рецепте.'),
                code=status.HTTP_400_BAD_REQUEST
            )
        ingredients_id = []
        for item in ingredients:
            ingredient = get_object_or_404(
                Ingredient,
                id=item['id']
            )
            if item.get('amount') < MINIMUM:
                raise serializers.ValidationError(
                    detail=('Укажите необходимое количество '
                            f'ингредиента {ingredient}.'),
                    code=status.HTTP_400_BAD_REQUEST
                )
            if ingredient in ingredients_id:
                raise serializers.ValidationError(
                    detail=(f'Ингредиент {ingredient.id} уже '
                            'использован в рецепте.'),
                    code=status.HTTP_400_BAD_REQUEST
                )
            ingredients_id.append(ingredient)
        return data

    def create_ingredients(self, ingredients, recipe) -> IngredientRecipe:
        """
        Creates a model linking a current ingredient with recipe.
        """
        bulk_list = []
        for ingredient in ingredients:
            bulk_list.append(IngredientRecipe(
                recipe=recipe,
                ingredients=ingredient.get('name'),
                amount=ingredient.get('amount')
            ))
        return IngredientRecipe.objects.bulk_create(bulk_list)

    def create(self, validated_data) -> Recipe:
        """
        Creates a whole recipe with provided data.
        """
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data) -> Recipe:
        """
        Updates recipes.
        """
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self.create_ingredients(ingredients, instance)
        if 'tags' in validated_data:
            instance.tags.set(
                validated_data.pop('tags'))
        return super().update(
            instance, validated_data)

    def to_representation(self, instance):
        return RecipeListRetrieveSerializer(
            instance,
            context={'request': self.context.get('request')}).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer / deserializer for model Favorite."""
    user = CustomUserSerializer(read_only=True)
    recipe = PartialRecipeSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ('user', 'recipe',)

    def validate(self, data) -> bool:
        """
        Checks if a recipe already in user's list of favorites.
        """
        request = self.context.get('request')
        recipe_req = data.get('recipe')
        if Favorite.objects.filter(user=request.user,
                                   recipe=recipe_req).exists():
            raise serializers.ValidationError(
                detail=(f'{recipe_req} уже есть в вашем списке.'),
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return PartialRecipeSerializer(
            instance.recipe, context=context).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Serializer / deserializer for model Shopping cart."""
    user = CustomUserSerializer(read_only=True)
    recipe = PartialRecipeSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ('user', 'recipe',)

    def validate(self, data) -> bool:
        """
        Checks if a recipe already in user's list of shopping list.
        """
        request = self.context.get('request')
        recipe_req = data.get('recipe')
        if ShoppingCart.objects.filter(user=request.user,
                                       recipe=recipe_req).exists():
            raise serializers.ValidationError(
                detail=(f'{recipe_req} уже есть в списке покупок.'),
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return PartialRecipeSerializer(
            instance.recipe, context=context).data
