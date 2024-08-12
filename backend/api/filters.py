from django_filters.rest_framework import FilterSet, filters
from rest_framework.filters import SearchFilter

from recipes import models


class IngredientFilter(SearchFilter):
    search_param = 'name'


class RecipeFilter(FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=models.Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(method='favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='in_cart')

    class Meta:
        model = models.Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def favorited(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(favoriterecipes__user=self.request.user)
        return queryset

    def in_cart(self, queryset, name, value):
        if value and not self.request.user.is_anonymous:
            return queryset.filter(shoppingcarts__user=self.request.user)
        return queryset
