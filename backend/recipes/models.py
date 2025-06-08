from django.core.validators import MinValueValidator
from django.db import models
from users.models import User


class Recipe(models.Model):
    class Meta:
        ordering = ['-id', ]
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

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

    cooking_time = models.PositiveIntegerField(
        unique=False,
        blank=False,
        verbose_name="Время приготовления в минутах",
        validators=[
            MinValueValidator(1,
                              "Минимальное время приготовления 1 минута")
        ]
    )

    def __str__(self):
        return self.name


class Ingredient(models.Model):

    class Meta:
        ordering = ['id', ]
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

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

    def __str__(self):
        return self.name


class IRLinkModel(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='i_link_r'
            )
        ]
        verbose_name = 'Ингредиент блюда'
        verbose_name_plural = 'Ингредиенты блюд'

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
        validators=[MinValueValidator(1, "Минимум 1")],
        verbose_name='Количество'
    )

    def __str__(self):
        a = self.ingredient.measurement_unit
        return (
            f"{self.amount}{a} {self.ingredient.name}"
            f" для {self.recipe.name}"
        )


class FavRecipe(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe', ],
                name='fav_r'
            )
        ]
        verbose_name = 'Рецепт в избранном'
        verbose_name_plural = 'Избранные рецепты'

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

    def __str__(self):
        a = self.user.username
        b = self.recipe.name
        return f"Рецепт {b} в избранном у {a}"


class Basket(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='basket'
            )
        ]
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

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

    def __str__(self):
        a = self.user.username
        b = self.recipe.name
        return f"Рецепт {b} в корзине у {a}"
