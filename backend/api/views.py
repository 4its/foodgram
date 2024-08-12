from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response

from recipes.models import (
    Tag, Ingredient, Recipe, RecipeIngredient, FavoriteRecipe, ShoppingCart
)
from users.models import User

from . import filters, utils, paginations, permissions, serializers


class RecipesUserViewSet(UserViewSet):
    def get_permissions(self):
        if self.action == 'me':
            return (IsAuthenticated(),)
        elif self.action == 'retrieve':
            return (AllowAny(),)
        return super().get_permissions()

    @action(
        detail=True, methods=('POST', 'DELETE'), pagination_class=None,
    )
    def subscribe(self, request, id):
        author = get_object_or_404(User, pk=id)
        if request.method == 'POST':
            serializer = serializers.WriteFollowSerializer(
                data=dict(user=request.user.pk, author=author.pk),
                context=dict(request=request)
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        connection = request.user.follower.filter(author=author)
        if connection.exists():
            connection.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            dict(error='Вы не подписаны на этого пользователя'),
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False, methods=('GET',),
        pagination_class=paginations.LimitPageNumberPagination,
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=self.request.user)
        serializer = serializers.FollowSerializer(
            self.paginate_queryset(queryset),
            context=dict(request=request),
            many=True,
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer
    pagination_class = None
    permission_classes = (AllowAny,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = serializers.IngredientSerializer
    filter_backends = (filters.IngredientFilter,)
    search_fields = ('^name',)
    pagination_class = None
    permission_classes = (AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthorOrReadOnly,)
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = filters.RecipeFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return serializers.ReadRecipeSerializer
        return serializers.WriteRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @staticmethod
    def delete_connection(model, user, pk):
        if not Recipe.objects.filter(id=pk).exists():
            return Response(
                dict(errors='Рецепт не существует'),
                status=status.HTTP_404_NOT_FOUND
            )
        del_count, _ = model.objects.filter(user=user, recipe__id=pk).delete()
        if del_count:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            dict(errors='Рецепт был удален ранее'),
            status=status.HTTP_400_BAD_REQUEST
        )

    @classmethod
    def base_favorite_shoppingcart_logic(cls, request, pk, serial, model):
        if request.method == 'POST':
            serializer = serial(
                data=dict(recipe=pk, user=request.user.pk),
                context=dict(request=request)
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return cls.delete_connection(
            model, request.user, pk
        )

    @action(detail=True, methods=('POST', 'DELETE'),)
    def favorite(self, request, pk=None):
        return self.base_favorite_shoppingcart_logic(
            request, pk,
            serializers.WriteFavoriteRecipeSerializer, FavoriteRecipe
        )

    @action(detail=True, methods=('POST', 'DELETE'),)
    def shopping_cart(self, request, pk=None):
        return self.base_favorite_shoppingcart_logic(
            request, pk,
            serializers.WriteShoppingCartRecipeSerializer, ShoppingCart
        )

    @action(detail=False)
    def download_shopping_cart(self, request):
        shopping_list = RecipeIngredient.objects.filter(
            recipe__shoppingcarts__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount')).order_by('ingredient__name')
        return utils.make_file(request, shopping_list)
