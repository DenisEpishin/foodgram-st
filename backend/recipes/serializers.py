from backend.constants import MIN_INT, MAX_INT, MAX_IMAGE_SIZE, MB_SIZE
from drf_extra_fields.fields import Base64ImageField
from users.serializers import GetUserSerializer
from rest_framework import serializers
from .models import Recipe, IRLinkModel, Ingredient, FavRecipe, Basket


class MealSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=MIN_INT, max_value=MAX_INT)

    class Meta:
        model = IRLinkModel
        fields = ['id', 'amount']


class IRLinkSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IRLinkModel
        fields = [
            'id',
            'name',
            'measurement_unit',
            'amount'
        ]


class GetRecipeSerializer(serializers.ModelSerializer):
    author = GetUserSerializer(read_only=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    ingredients = IRLinkSerializer(
        many=True,
        source='r_link_i',
        read_only=True
    )

    class Meta:
        model = Recipe
        fields = [
            'id',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        ]

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.fav_r.filter(user=user).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.basket_r.filter(user=user).exists()
        return False


class NewRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(min_value=MIN_INT, max_value=MAX_INT)
    ingredients = MealSerializer(many=True, write_only=True)

    class Meta:
        model = Recipe
        fields = [
            'id',
            'ingredients',
            'image',
            'name',
            'text',
            'cooking_time'
        ]

    def create(self, data):
        ingredients = data.pop('ingredients')
        recipe = Recipe.objects.create(author=self.context['request'].user, **data)
        self.add_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, data):
        ingredients = data.pop('ingredients', None)
        if ingredients is None:
            raise serializers.ValidationError("Добавьте ингредиенты")
        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.save()
        instance.r_link_i.all().delete()
        self.add_ingredients(instance, ingredients)
        return instance

    def validate(self, data):
        image = data.get('image')
        if image:
            if image.size > MAX_IMAGE_SIZE * MB_SIZE:
                raise serializers.ValidationError(
                    f"Максимальный размер изображения {MAX_IMAGE_SIZE}Мб."
                )
        else:
            raise serializers.ValidationError(
                {"detail": "Выберите картинку правильного формата"}
            )
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {"detail": "Ингредиенты не найдены."}
            )
        i = [j["id"] for j in ingredients]
        if len(i) != len(set(i)):
            raise serializers.ValidationError({
                "detail": "Ингредиенты не должны повторяться."
            })
        ingredients_exist = Ingredient.objects.filter(id__in=i).count()
        if ingredients_exist != len(i):
            raise serializers.ValidationError(
                {"detail": "Некоторые ингредиенты не найдены."}
            )
        return data

    def add_ingredients(self, recipe, i_list):
        ingredients_to_add = [IRLinkModel(
            recipe=recipe,
            ingredient_id=j['id'],
            amount=j['amount']) for j in i_list
        ]
        IRLinkModel.objects.bulk_create(ingredients_to_add)

    def to_representation(self, instance):
        return GetRecipeSerializer(
            instance,
            context=self.context,
        ).data


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = [
            'id',
            'name',
            'measurement_unit'
        ]


class FavoriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='recipe.id', read_only=True)
    name = serializers.CharField(source='recipe.name', read_only=True)
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time', read_only=True
    )

    class Meta:
        model = FavRecipe
        fields = [
            'id',
            'name',
            'image',
            'cooking_time'
        ]


class BasketSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='recipe.id', read_only=True)
    name = serializers.CharField(source='recipe.name', read_only=True)
    image = serializers.ImageField(source='recipe.image', read_only=True)
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time', read_only=True
    )

    class Meta:
        model = Basket
        fields = [
            'id',
            'name',
            'image',
            'cooking_time'
        ]
