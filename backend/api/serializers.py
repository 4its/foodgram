from django.conf import settings
from django.db import transaction
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .fields import Base64ImageField
from recipes.models import (
    FavoriteRecipe, Ingredient, Recipe,
    RecipeIngredient, ShoppingCart, Tag, User
)
from users.models import Follow


def check_recipe_subscribe(self, recipe, checking_model):
    user = self.context['request'].user
    return (
        user.is_authenticated
        and checking_model.objects.filter(
            user=user, recipe=recipe
        ).exists()
    )


class MyUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', "is_subscribed"
        )

    def get_is_subscribed(self, author):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and user.follower.filter(author=author).exists()
        )


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount',)

    def validate_amount(self, amount):
        if amount < settings.MIN_VALUE:
            raise ValidationError('Не задано количество ингредиента')
        return amount


class ReadRecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = MyUserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipeingredients', many=True
    )
    is_in_shopping_cart = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'name',
            'image', 'text', 'cooking_time', 'is_in_shopping_cart',
            'is_favorited'
        )

    def get_is_in_shopping_cart(self, recipe):
        return check_recipe_subscribe(self, recipe, ShoppingCart)

    def get_is_favorited(self, recipe):
        return check_recipe_subscribe(self, recipe, FavoriteRecipe)


class WriteRecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True, required=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=True
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time'
        )
        required_fields = fields
        extra_kwargs = {i: {'required': True} for i in fields}

    def validate(self, data):
        tags = data.get('tags')
        ingredients = data.get('ingredients')
        if not ingredients:
            raise ValidationError(
                dict(ingredients='Должен быть хотя бы 1 ингредиент.')
            )
        if not tags:
            raise ValidationError(dict(tags='Должен быть хотя бы 1 тег.'))
        if len(tags) != len(set(tags)):
            raise ValidationError('Дублирование в тэгах недопустимо.')
        ingredients_ids = [item['ingredient'].id for item in ingredients]
        if len(ingredients_ids) != len(set(ingredients_ids)):
            raise ValidationError('Ингредиенты не должны повторяться')
        return super().validate(data)

    @transaction.atomic
    def ingredients_create(self, recipe, ingredients):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self.ingredients_create(recipe, ingredients_data)
        return recipe

    @transaction.atomic
    def update(self, recipe, validated_data):
        new_ingredients = validated_data.pop('ingredients')
        recipe.tags.clear()
        recipe.ingredients.clear()
        self.ingredients_create(recipe, new_ingredients)
        return super().update(recipe, validated_data)

    def to_representation(self, recipe):
        return ReadRecipeSerializer(recipe, context=self.context).data


class RecipeMinimalSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(MyUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='recipes.count')

    class Meta(MyUserSerializer.Meta):
        fields = MyUserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, user):
        request = self.context.get('request')
        recipes_limit = request.GET.get('recipes_limit')
        recipes = user.recipes.all()
        if recipes_limit and recipes_limit.isdigit():
            recipes = recipes[:int(recipes_limit)]
        serializer = RecipeMinimalSerializer(
            recipes, context=self.context, many=True
        )
        return serializer.data


class WriteFollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('user', 'author',)

    def validate(self, data):
        user, author = data['user'], data['author']
        if user == author:
            raise ValidationError('Нельзя подписаться на себя')
        if user.follower.filter(author=author).exists():
            raise ValidationError('Уже подписаны на этого пользователя')
        return data

    def to_representation(self, instance):
        return FollowSerializer(
            instance.author,
            context=self.context
        ).data


class BaseWriteFavoriteShoppingCart(serializers.ModelSerializer):

    def validate(self, data):
        if not Recipe.objects.filter(id=data['recipe'].pk).exists():
            raise ValidationError('Рецепта не существует.')
        return data

    def to_representation(self, instance):
        return RecipeMinimalSerializer(
            instance.recipe,
            context=self.context
        ).data


class WriteFavoriteRecipeSerializer(BaseWriteFavoriteShoppingCart):
    class Meta:
        model = FavoriteRecipe
        fields = ('recipe', 'user')

    def validate(self, data):
        data = super().validate(data)
        if data['user'].favoriterecipes.filter(recipe=data['recipe']).exists():
            raise ValidationError('Рецепт уже добавлен в избранное.')
        return data


class WriteShoppingCartRecipeSerializer(BaseWriteFavoriteShoppingCart):
    class Meta:
        model = ShoppingCart
        fields = ('recipe', 'user')

    def validate(self, data):
        data = super().validate(data)
        if data['user'].shoppingcarts.filter(recipe=data['recipe']).exists():
            raise ValidationError('Рецепт уже добавлен в список покупок.')
        return data
