from django.urls import path, include
from rest_framework.routers import SimpleRouter

from . import views


router_v1 = SimpleRouter()
router_v1.register('tags', views.TagViewSet, basename='tags')
router_v1.register('users', views.RecipesUserViewSet, basename='users')
router_v1.register('recipes', views.RecipeViewSet, basename='recipes')
router_v1.register(
    'ingredients', views.IngredientViewSet, basename='ingredients'
)


urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
