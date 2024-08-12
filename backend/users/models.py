from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.template.defaultfilters import truncatechars

from .validators import validate_username


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name',)

    email = models.EmailField(
        verbose_name='Эл.почта',
        max_length=settings.EMAIL_FIELD_LENGTH,
        unique=True,
    )
    username = models.CharField(
        verbose_name='Имя пользователя',
        max_length=settings.STANDARD_FIELD_LENGTH,
        unique=True,
        validators=(validate_username,)
    )
    password = models.CharField(
        max_length=settings.STANDARD_FIELD_LENGTH,
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=settings.STANDARD_FIELD_LENGTH,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=settings.STANDARD_FIELD_LENGTH,
    )

    class Meta(AbstractUser.Meta):
        ordering = ('username',)

    def __str__(self):
        return truncatechars(self.username, settings.DEFAULT_TRUNCATE)


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'подписки'
        ordering = ('author',)
        constraints = (
            UniqueConstraint(
                fields=('user', 'author'),
                name='unique_%(class)s'
            ),
        )

    def __str__(self):
        return f'{self.user} подписан на {self.author}'
