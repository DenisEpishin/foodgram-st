from backend.constants import MIN_INT, MAX_INT
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from users.models import User


class Recipe(models.Model):
    class Meta:
        ordering = ['-id', ]
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes_of_author',
        verbose_name='Автор'
    )

    name = models.CharField(
        unique=False,
        max_length=256,
        blank=False,
        verbose_name='Наименование блюда'
    )

    image = models.ImageField(
        unique=False,
        blank=False,
        verbose_name="Изображение"
    )

    text = models.TextField(
        unique=False,
        blank=False,
        verbose_name='Текстовое описание'
    )

    cooking_time = models.PositiveSmallIntegerField(
        unique=False,
        blank=False,
        verbose_name="Время приготовления в минутах",
        validators=[
            MinValueValidator(
                MIN_INT,
                f"Минимальное время приготовления {MIN_INT} минута"),
            MaxValueValidator(
                MAX_INT,
                f"Максимальное время приготовления {MAX_INT} минута")
        ]
    )


class Ingredient(models.Model):
    class Meta:
        ordering = ['id', ]
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name

    name = models.CharField(
        max_length=255,
        unique=True,
        blank=False,
        verbose_name='Название'
    )

    measurement_unit = models.CharField(
        max_length=255,
        unique=False,
        blank=False,
        verbose_name='Единица измерения'
    )


class IRLinkModel(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='i_link_r'
            )
        ]
        ordering = ['id', ]
        verbose_name = 'Ингредиент блюда'
        verbose_name_plural = 'Ингредиенты блюд'

    def __str__(self):
        a = self.ingredient.measurement_unit
        return (
            f"{self.amount}{a} {self.ingredient.name}"
            f" для {self.recipe.name}"
        )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='r_link_i',
        verbose_name='Рецепт'
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='i_link_r',
        verbose_name='Ингредиент'
    )

    amount = models.PositiveSmallIntegerField(
        blank=False,

        validators=[
            MinValueValidator(
                MIN_INT,
                f"Минимум {MIN_INT}"),
            MaxValueValidator(
                MAX_INT,
                f"Максимум {MAX_INT}")
        ],
        verbose_name='Количество'
    )


class FavRecipe(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe', ],
                name='fav_r'
            )
        ]
        ordering = ['id', ]
        verbose_name = 'Рецепт в избранном'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self):
        a = self.user.username
        b = self.recipe.name
        return f"Рецепт {b} в избранном у {a}"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='fav_u',
        verbose_name='Пользователь'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='fav_r',
        verbose_name='Рецепт'
    )


class Basket(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='basket'
            )
        ]
        ordering = ['id', ]
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        a = self.user.username
        b = self.recipe.name
        return f"Рецепт {b} в корзине у {a}"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='basket_u',
        verbose_name='Пользователь'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='basket_r',
        verbose_name='Рецепт'
    )
