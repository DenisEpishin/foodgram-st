from drf_extra_fields.fields import Base64ImageField
from users.serializers import GetUserSerializer
from rest_framework import serializers
from .models import Recipe, IRLinkModel, Ingredient, FavRecipe, Basket


class MealSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)

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
        else:
            return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.basket_r.filter(user=user).exists()
        else:
            return False


class NewRecipeSerializer(serializers.ModelSerializer):

    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(min_value=1)
    ingredients = serializers.ListField(
        child=MealSerializer(write_only=True),
        write_only=True
    )

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
        i = data.pop('ingredients')
        r = Recipe.objects.create(author=self.context['request'].user, **data)
        self.addI(r, i)
        return r

    def validate(self, data):
        try:
            image = data['image']
        except Exception:
            raise serializers.ValidationError(
                {"detail": "Выберите картинку правильного формата"}
            )
        if image:
            if image.size > 5 * 1024 * 1024:
               raise serializers.ValidationError(
                    "Максимальный размер изображения 5Мб."
                )
        else:
            raise serializers.ValidationError(
                {"detail": "Выберите картинку правильного формата"}
            )
        try:
            ingredients = data['ingredients']
        except Exception:
            raise serializers.ValidationError(
                {"detail": "Ингредиенты не найдены."}
            )
        if not isinstance(ingredients, list):
            raise serializers.ValidationError(
                {"detail": "В качестве ингредиентов ожидается список."}
            )
        i = [j["id"] for j in ingredients]
        if len(i) != len(set(i)):
            raise serializers.ValidationError({
                "detail": "Ингредиенты не должны повторяться."
            })
        iid = []
        for i in ingredients:
            try:
                iid.append({"id": i["id"], "amount": int(i["amount"])})
            except (KeyError, ValueError):
                raise serializers.ValidationError(
                    {
                        "detail":
                            "Ошибка формата ингредиента."
                    }
                )
        if not iid:
            raise serializers.ValidationError(
                {"detail": "В блюде отсутствуют ингредиенты."}
            )
        ids = [j["id"] for j in iid]
        good_ids = set(Ingredient.objects.filter(
            id__in=ids
        ).values_list('id', flat=True))
        bad_ids = set(ids) - good_ids
        if bad_ids:
            raise serializers.ValidationError(
                {"detail":f"Некоторые ингредиенты не найдены."}
            )
        data['ingredients'] = iid
        return data

    def addI(self, recipe, i_list):
        i = [IRLinkModel(
            recipe=recipe,
            ingredient_id=j['id'],
            amount=j['amount']) for j in i_list
        ]
        IRLinkModel.objects.bulk_create(i)

    def to_representation(self, instance):
        return GetRecipeSerializer(
            instance,
            context=self.context,
        ).data


class UpdateRecipeSerializer(serializers.ModelSerializer):

    image = Base64ImageField(required=False, )
    cooking_time = serializers.IntegerField(min_value=1)
    ingredients = serializers.ListField(
        child=MealSerializer(write_only=True),
        write_only=True
    )

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

    def update(self, instance, data):
        i = data.pop('ingredients', None)
        if i is None:
            raise serializers.ValidationError("")
        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.save()
        instance.r_link_i.all().delete()
        self.addI(instance, i)
        return instance

    def validate(self, data):
        try:
            image = data['image']
        except Exception:
            raise serializers.ValidationError(
                {"detail": "Выберите картинку правильного формата"}
            )
        if image:
            if image.size > 5 * 1024 * 1024:
               raise serializers.ValidationError(
                    "Максимальный размер изображения 5Мб."
                )
        else:
            raise serializers.ValidationError(
                {"detail": "Выберите картинку правильного формата"}
            )
        try:
            ingredients = data['ingredients']
        except Exception:
            raise serializers.ValidationError(
                {"detail": "Ингредиенты не найдены."}
            )
        if not isinstance(ingredients, list):
            raise serializers.ValidationError(
                {"detail": "В качестве ингредиентов ожидается список."}
            )
        i = [j["id"] for j in ingredients]
        if len(i) != len(set(i)):
            raise serializers.ValidationError({
                "detail": "Ингредиенты не должны повторяться."
            })
        iid = []
        for i in ingredients:
            try:
                iid.append({"id": i["id"], "amount": int(i["amount"])})
            except (KeyError, ValueError):
                raise serializers.ValidationError(
                    {"detail": "Ошибка формата ингредиента."}
                )
        if not iid:
            raise serializers.ValidationError(
                {"detail": "В блюде отсутствуют ингредиенты."}
            )
        ids = [j["id"] for j in iid]
        good_ids = set(Ingredient.objects.filter(
            id__in=ids
        ).values_list('id', flat=True))
        bad_ids = set(ids) - good_ids
        if bad_ids:
            raise serializers.ValidationError(
                {"detail": f"Некоторые ингредиенты не найдены."}
            )
        data['ingredients'] = iid
        return data

    def addI(self, recipe, i_list):
        i = [IRLinkModel(
            recipe=recipe,
            ingredient_id=j['id'],
            amount=j['amount']) for j in i_list
        ]
        IRLinkModel.objects.bulk_create(i)

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
        source='recipe.cooking_time', read_only=True,
    )

    class Meta:
        model = Basket
        fields = [
            'id',
            'name',
            'image',
            'cooking_time'
        ]
