from django.core.validators import MinValueValidator
from django.db import models
from users.models import User

from constants import (
    RECIPE_MAX_LENGTH,
    RECIPE_MIN_TIME,
    RECIPE_MIN_AMOUNT,
    INGREDIENT_NAME_MAX_LENGTH,
    INGREDIENT_MEASUREMENT_UNIT_MAX_LENGTH
)


class Ingredient(models.Model):
    """Модель ингредиентов."""

    name = models.CharField(
        verbose_name="Наименование",
        max_length=INGREDIENT_NAME_MAX_LENGTH
    )

    measurement_unit = models.CharField(
        verbose_name="Ед. измерения",
        max_length=INGREDIENT_MEASUREMENT_UNIT_MAX_LENGTH
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"],
                name="unique_name_measurement_unit"
            )
        ]
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Recipe(models.Model):
    """Модель рецептов."""

    name = models.CharField(
        verbose_name="Наименование",
        max_length=RECIPE_MAX_LENGTH
    )

    text = models.TextField(
        verbose_name="Описание"
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        through="RecipeIngredient",
    )

    image = models.ImageField(
        verbose_name="Изображение",
        upload_to="recipes/images/"
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор"
    )

    cooking_time = models.PositiveIntegerField(
        verbose_name="Время приготовления в минутах",
        validators=[
            MinValueValidator(
                RECIPE_MIN_TIME,
                f"Минимальное время приготовления "
                f"{RECIPE_MIN_TIME} минут(-ы)."
            )
        ]
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("-created_at",)
        default_related_name = "recipes"

    def __str__(self):
        return f"ID рецепта: {self.id} | {self.name}"


class RecipeIngredient(models.Model):
    """Модель для связи ингредиентов с рецептами"""

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name="Ингредиент"
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт"
    )

    amount = models.PositiveIntegerField(
        verbose_name="Количество",
        validators=[
            MinValueValidator(
                RECIPE_MIN_AMOUNT,
                "Минимальное количество ингредиентов "
                f"{RECIPE_MIN_AMOUNT}."
            )
        ]
    )


    class Meta:
        verbose_name = "Игредиент-рецепт"
        verbose_name_plural = "Ингредиенты рецептов"
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "ingredient"],
                name="unique_recipe_ingredient"
            )
        ]
        default_related_name = "recipe_ingredients"

    def __str__(self):
        return (
            f"{self.ingredient.name} - {self.amount}"
            f"{self.ingredient.measurement_unit} для {self.recipe.name}"
        )


class BaseUserRecipe(models.Model):
    """Базовый класс для избранного и списка покупок"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="%(class)ss"
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
        related_name="%(class)ss"
    )

    class Meta:
        abstract = True
        ordering = ['user', 'recipe']
        constraints = [
            models.UniqueConstraint(
                fields=["user", "recipe"],
                name="%(app_label)s_%(class)s_unique_user_recipe"
            )
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.recipe.name}"


class Favorite(BaseUserRecipe):
    """Модель для избранного."""

    class Meta(BaseUserRecipe.Meta):
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные"


class ShoppingCart(BaseUserRecipe):
    """Модель для списка покупок."""

    class Meta(BaseUserRecipe.Meta):
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
