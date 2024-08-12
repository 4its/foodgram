from django.conf import settings
from django.contrib import admin

from .models import (
    FavoriteRecipe, Ingredient, Recipe, RecipeIngredient,
    RecipeTag, ShoppingCart, Tag
)


class BaseRecipeTabularInLine(admin.TabularInline):
    min_num = settings.MIN_VALUE


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')


class RecipeIngredientInLine(BaseRecipeTabularInLine):
    model = RecipeIngredient


class RecipeTagInLine(BaseRecipeTabularInLine):
    model = RecipeTag


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    readonly_fields = ('count_in_favorite',)
    inlines = (RecipeIngredientInLine, RecipeTagInLine)
    list_display = (
        'name', 'author', 'image', 'text',
        'cooking_time', 'count_in_favorite'
    )
    list_filter = ('tags', 'author', 'name')

    @admin.display(description='Счетчик в избранном')
    def count_in_favorite(self, recipe):
        return recipe.favoriterecipes.count()


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = list_display


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = list_display
