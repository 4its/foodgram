from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from rest_framework.authtoken.models import TokenProxy

from .models import Follow, User

admin.site.unregister(Group)
admin.site.unregister(TokenProxy)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    readonly_fields = ('followers_count', 'recipes_count')
    list_display = (
        'id', 'username', 'email', 'first_name', 'last_name'
    ) + readonly_fields
    list_filter = ('email', 'username')

    @admin.display(description='Кол-во подписчиков')
    def followers_count(self, user):
        return user.following.count()

    @admin.display(description='Кол-во рецептов')
    def recipes_count(self, user):
        return user.recipes.count()


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
