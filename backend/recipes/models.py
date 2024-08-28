from colorfield.fields import ColorField
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.template.defaultfilters import truncatechars
from django.urls import reverse

User = get_user_model()


class BaseNameModel(models.Model):
    name = models.CharField(
        'Имя(название)',
        max_length=settings.RECIPE_DEFAULT_FIELD_LENGTH,
    )

    class Meta:
        abstract = True
        default_related_name = '%(class)ss'
        ordering = ('name',)

    def __str__(self):
        return truncatechars(self.name, settings.DEFAULT_TRUNCATE)


class BaseRecipeModel(models.Model):
    recipe = models.ForeignKey(
        'Recipe', on_delete=models.CASCADE, verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        default_related_name = '%(class)ss'


class ShoppingAndFavoriteBaseModel(BaseRecipeModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Пользователь'
    )

    class Meta(BaseRecipeModel.Meta):
        abstract = True
        ordering = ('-recipe__pub_date',)
        constraints = (
            UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_%(class)s_constraint',
            ),
        )

    def __str__(self):
        return f'{self.user} добавил: {self.recipe}'


class Tag(BaseNameModel):
    color = ColorField(
        format='hex',
        null=True,
        unique=True,
    )
    slug = models.SlugField(
        'Слаг тэга',
        max_length=settings.RECIPE_DEFAULT_FIELD_LENGTH,
        blank=True,
        null=True,
        unique=True,
    )

    class Meta(BaseNameModel.Meta):
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'


class Ingredient(BaseNameModel):
    measurement_unit = models.CharField(
        'Ед. измерения',
        max_length=settings.RECIPE_DEFAULT_FIELD_LENGTH,
    )

    class Meta(BaseNameModel.Meta):
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_%(class)s_constraint',
            ),
        )


class RecipeIngredient(BaseRecipeModel):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=(
            MinValueValidator(
                settings.MIN_VALUE,
                settings.CANT_BE_LESS_THAN_MIN_VALUE
            ),
        )
    )

    class Meta(BaseRecipeModel.Meta):
        ordering = ('ingredient__name',)
        constraints = (
            UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_%(class)s'
            ),
        )

    def __str__(self):
        return (
            f'{self.ingredient.name} ({self.ingredient.measurement_unit}) -'
            f' {self.amount}'
        )


class RecipeTag(BaseRecipeModel):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, verbose_name='Тэг')

    class Meta(BaseRecipeModel.Meta):
        ordering = ('recipe',)

    def __str__(self):
        return f'Тег {self.tag.name} для рецепта {self.recipe.name}'


class Recipe(BaseNameModel):
    ingredients = models.ManyToManyField(
        Ingredient, through=RecipeIngredient, verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag, through=RecipeTag, verbose_name='Тэги'
    )
    image = models.ImageField(
        'Изображение блюда',
        upload_to='recipes/recipe_images/'
    )
    text = models.TextField('Описание рецепта',)
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления в мин.',
        validators=(
            MinValueValidator(
                settings.MIN_VALUE,
                settings.CANT_BE_LESS_THAN_MIN_VALUE
            ),
        )
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Автор',
    )
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta(BaseNameModel.Meta):
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def get_short_url(self):
        return reverse('short_url', args=str(self.id))


class ShoppingCart(ShoppingAndFavoriteBaseModel):
    class Meta(ShoppingAndFavoriteBaseModel.Meta):
        verbose_name = 'Корзина покупок'
        verbose_name_plural = verbose_name


class FavoriteRecipe(ShoppingAndFavoriteBaseModel):
    class Meta(ShoppingAndFavoriteBaseModel.Meta):
        verbose_name = 'Избранные рецепты'
        verbose_name_plural = verbose_name
