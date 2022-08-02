from typing import Dict

from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import exceptions, serializers, status, validators
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField

from foodgram.settings import FALSE_RESULT, MINIMUM
from users.models import Subscription, User
from recipes.models import (Favorite, Ingredient, Addamount, Recipe,
                            ShoppingCart, Tag)
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
        url = reverse('api:users_list-me', args=[user.pk])
        if self.context.get('request').path_info == url:
            return False
        if user.is_authenticated:
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
        if username.lower() == 'me':
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

    def create(self, validated_data) -> User:
        """
        Registration new accounts for users.
        """
        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'])
        user.set_password(validated_data['password'])
        user.save()
        return user


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


class SubscriptionListSerializer(CustomUserSerializer):
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
        if not request or request.user.is_anonymous:
            return False
        context = {'request': request}
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit is not None:
            recipes = obj.recipes.all()[:int(recipes_limit)]
        else:
            recipes = obj.recipes.all()
        return PartialRecipeSerializer(
            recipes, many=True, context=context).data

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


class SubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ('user', 'author')
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message=('Подписка уже есть')
            )
        ]

    def validate(self, data) -> bool:
        """
        Checks user's subscription.
        """
        user = self.context.get('request').user
        subscription_id = data.get('id')
        user_id = data.get('user_id')
        author_id = data.get('author_id')
        subscription = Subscription.objects.filter(id=subscription_id,
                                                   user=user_id,
                                                   author=author_id).exists()
        if subscription:
            raise serializers.ValidationError(
                detail=(f'Вы уже подписаны на {author_id}.'),
                code=status.HTTP_400_BAD_REQUEST
            )
        if author_id == user.id:
            raise serializers.ValidationError(
                detail='Вы не можете подписаться на самого себя.',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return SubscriptionListSerializer(
            instance.author, context=context).data


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer / deserializer for model Ingredients."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class AddamountSerializer(serializers.ModelSerializer):
    """
    Serializer / deserializer for counting amount of ingredient in a
    current recipe. The class links class Ingredient with class Recipe.
    """
    id = serializers.ReadOnlyField(source='ingredients.id')
    name = serializers.ReadOnlyField(source='ingredients.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredients.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = Addamount
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class AddamountCUDSerializer(serializers.ModelSerializer):
    """
    Serializer / deserializer for CUD (create, update and delete) operations
    with recipes.
    """
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = Addamount
        fields = ('id', 'amount',)


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
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField(
        method_name='get_ingredients',
        read_only=True)
    is_favorited = serializers.SerializerMethodField(
        method_name='get_is_favorited',
        read_only=True
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        method_name='get_is_in_shopping_cart',
        read_only=True
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

    def get_ingredients(self, obj: Recipe) -> AddamountSerializer:
        """The method is for displaying information"""
        ingredients = Addamount.objects.filter(recipe=obj)
        return AddamountSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj: Recipe) -> bool:
        """
        Method for serializer field checking if the recipe is
        in personal favorite list of a request user.
        """
        if self.context.get('request').method == 'POST':
            return False
        user = self.context.get('request').user
        recipe = self.context.get('recipe_id')
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=recipe).exists()
        return False

    def get_is_in_shopping_cart(self, obj: Recipe) -> bool:
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
                user=user,
                recipe=recipe
            ).exists()
        return False


class RecipeManipulationSerializer(serializers.ModelSerializer):
    """
    Serializer / deserializer for model Recipe.
    POST, PATCH, DELETE requests: creation, update and deletion.
    """
    ingredients = AddamountCUDSerializer(many=True, read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id',
                  'ingredients',
                  'tags',
                  'image',
                  'name',
                  'text',
                  'cooking_time',)

    def validate(self, data: DICT_TYPES) -> None:
        """Validation data for recipe fields."""
        user = self.context.get('request').user
        tags = data.get('tags')
        image = data.get('image')
        name = data.get('name')
        text = data.get('text')
        cooking_time = data.get('cooking_time')
        if user.is_anonymous:
            raise serializers.ValidationError(
                detail='Необходимо пройти аутентификацию',
                code=status.HTTP_403_FORBIDDEN
            )
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
        ingredients = self.initial_data['ingredients']
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

    def create_ingredients(self, recipe, ingredients) -> Addamount:
        """
        Creates a model linking a current ingredient with recipe.
        """
        bulk_list = []
        for ingredient in ingredients:
            bulk_list.append(Addamount(
                recipe=recipe,
                ingredients=ingredient.get('id'),
                amount=ingredient.get('amount'),
            ))
        return Addamount.objects.bulk_create(bulk_list)

    def create(self, validated_data) -> Recipe:
        """Creates new recipes."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data) -> Recipe:
        """
        Updates recipes.
        """
        user = self.context.get('request').user
        author = validated_data.get('author', instance.author)
        if user == author:
            if 'ingredients' in validated_data:
                ingredients = validated_data.pop('ingredients')
                instance.ingredients.clear()
                self.create_ingredients(ingredients, instance)
            if 'tags' in validated_data:
                instance.tags.set(
                    validated_data.pop('tags'))
            instance.name = validated_data.get('name', instance.name)
            instance.text = validated_data.get('text', instance.text)
            instance.cooking_time = validated_data.get(
                'cooking_time',
                instance.cooking_time
            )
            instance.image = validated_data.get('image', instance.image)
            instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeListRetrieveSerializer(
            instance,
            context={'request': self.context.get('request')}).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Serializer / deserializer for model Favorite."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message=('Рецепт уже в избранном')
            )
        ]

    def validate(self, data) -> bool:
        """
        Checks if a recipe already in user's list of favorites.
        """
        user = data.get('user_id')
        recipe_req = data['recipe']
        if Favorite.objects.filter(user=user,
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

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            validators.UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message=('Рецепт уже есть в списке покупок')
            )
        ]

    def validate(self, data) -> bool:
        """
        Checks if a recipe already in user's list of shopping list.
        """
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        user = data.get('user_id')
        recipe_req = data.get('recipe')
        if ShoppingCart.objects.filter(user=user,
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
