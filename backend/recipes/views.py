from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.exceptions import ValidationError
from .models import Recipe, Ingredient, FavRecipe, Basket
from .serializers import (GetRecipeSerializer, UpdateRecipeSerializer,
                          NewRecipeSerializer, IngredientSerializer,
                          FavoriteSerializer, BasketSerializer)


class IsAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.author == request.user


class RecipesList:

    queryset = Recipe.objects.all()


class RecipeListView(RecipesList, generics.ListCreateAPIView):

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        rows = super().get_queryset()
        user = self.request.user
        f = self.request.query_params.get('author')
        if f:
            rows = rows.filter(author_id=f)
        f = self.request.query_params.get('is_favorited')
        if f and user.is_authenticated:
            f_us = Q(fav_r__user=user)
            rows = rows.filter(f_us if f == '1' else ~f_us)
        f = self.request.query_params.get('is_in_shopping_cart')
        if f and user.is_authenticated:
            f_us = Q(basket_r__user=user)
            rows = rows.filter(f_us if f == '1' else ~f_us)
        return rows

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return NewRecipeSerializer
        else:
            return GetRecipeSerializer


class RecipeView(RecipesList, generics.RetrieveUpdateDestroyAPIView):

    permission_classes = [IsAuthorOrReadOnly]
    lookup_field = 'id'
    lookup_url_kwarg = 'recipe_id'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UpdateRecipeSerializer
        else:
            return GetRecipeSerializer


class IngredientListView(generics.ListAPIView):

    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        rows = self.request.query_params.get('name', None)
        if not rows:
            return Ingredient.objects.all()
        rows = Ingredient.objects.filter(
            Q(name__istartswith=rows),
        )
        return rows


class IngredientView(generics.RetrieveAPIView):

    lookup_field = 'id'
    lookup_url_kwarg = 'ingredient_id'
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()


class ShortLinkView(RecipesList, generics.RetrieveAPIView):

    lookup_field = 'id'
    lookup_url_kwarg = 'recipe_id'

    def retrieve(self, request, recipe_id='', **kwargs):
        get_object_or_404(Recipe, id=recipe_id)
        link = request.build_absolute_uri(f'/s/{recipe_id}/')
        return Response({"short-link": link}, status=status.HTTP_200_OK)


class FavView(generics.CreateAPIView, generics.DestroyAPIView):

    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'recipe_id'
    serializer_class = FavoriteSerializer

    def create(self, request, *args, **kwargs):
        r_id = kwargs['recipe_id']
        r = get_object_or_404(Recipe, id=r_id)
        if request.user.fav_u.filter(
                recipe=r,
        ).exists():
            return Response(
                {"detail": "Рецепт уже в избранном."},
                status=status.HTTP_400_BAD_REQUEST
            )
        f = FavRecipe.objects.create(user=request.user, recipe=r)
        serializer = self.get_serializer(f)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_object(self):
        r_id = self.kwargs['recipe_id']
        r = get_object_or_404(Recipe, id=r_id)
        try:
            return FavRecipe.objects.get(
                user=self.request.user, recipe=r,
            )
        except FavRecipe.DoesNotExist:
            raise ValidationError(
                {"detail": "Рецепт не найден в вашем избранном."},
                code=status.HTTP_400_BAD_REQUEST
            )

class BasketView(generics.CreateAPIView, generics.DestroyAPIView):

    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'recipe_id'
    serializer_class = BasketSerializer

    def create(self, request, *args, **kwargs):
        r_id = kwargs['recipe_id']
        r = get_object_or_404(Recipe, id=r_id)
        if Basket.objects.filter(user=request.user, recipe=r).exists():
            return Response(
                {"detail": "Рецепт уже в списке покупок."},
                status=status.HTTP_400_BAD_REQUEST
            )
        f = Basket.objects.create(user=request.user, recipe=r)
        s = self.get_serializer(f)
        return Response(s.data, status=status.HTTP_201_CREATED)

    def get_object(self):
        r_id = self.kwargs['recipe_id']
        r = get_object_or_404(Recipe, id=r_id)
        try:
            return Basket.objects.get(user=self.request.user, recipe=r)
        except Basket.DoesNotExist:
            raise ValidationError(
                {"detail": "Нет такого рецепта в списке покупок."},
                code=status.HTTP_400_BAD_REQUEST
            )


class BasketDownload(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        rtext = ["Выбранные рецепты:\n"]
        shopping_cart = self._get_user_basket(request.user)
        if not shopping_cart.exists():
            raise ValidationError({'detail': 'Ваш список покупок пуст.'})
        ingredients = {}
        measurement = {}
        for i in shopping_cart:
            rtext.append(i.recipe.name)
            for j in i.recipe.r_link_i.all():
                if j.ingredient.name in ingredients:
                    ingredients[j.ingredient.name] += j.amount
                else:
                    ingredients[j.ingredient.name] = j.amount
                    measurement[j.ingredient.name] = j.ingredient.measurement_unit
        rtext.append("-" * 50)
        rtext.append("\nНеобходимые продукты:\n")
        for key, value in ingredients.items():
            rtext.append(f"{key}: {value} {measurement[key]}")
        response = HttpResponse("\n".join(rtext), content_type="text/plain")
        response["Content-Disposition"] = 'attachment; filename="shopping-list.txt"'
        return response

    def _get_user_basket(self, user):
        return user.basket_u.select_related(
            "recipe"
        ).prefetch_related("recipe__r_link_i__ingredient").all()
