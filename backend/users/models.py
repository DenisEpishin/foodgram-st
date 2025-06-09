from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models


class RValidator(UnicodeUsernameValidator):
    regex = r'^[\w.@+-]+\Z'


class User(AbstractUser):
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["username",]

    def __str__(self):
        return self.username

    username_validator = RValidator()
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'password']
    USERNAME_FIELD = "email"

    email = models.EmailField(
        unique=True,
        max_length=254,
        blank=False,
        verbose_name='Электронная почта'
    )

    username = models.CharField(
        unique=True,
        max_length=150,
        blank=False,
        validators=[username_validator],
        verbose_name='Логин'
    )

    first_name = models.CharField(
        unique=False,
        max_length=150,
        blank=False,
        verbose_name='Имя',
    )

    last_name = models.CharField(
        unique=False,
        max_length=150,
        blank=False,
        verbose_name='Фамилия',
    )

    avatar = models.ImageField(
        blank=True,
        verbose_name="Аватар"
    )


class Follow(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['follower', 'following'],
                name='follow'
            )
        ]
        ordering = ["follower",]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        a = self.follower.username
        b = self.following.username
        return f'"{a}" подписан на "{b}"'

    follower = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
    )

    following = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE,
        verbose_name='Подписан на',
    )
