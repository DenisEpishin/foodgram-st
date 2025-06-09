from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.exceptions import ValidationError
from .models import Recipe, Ingredient, FavRecipe, Basket, IRLinkModel
from .serializers import (GetRecipeSerializer, NewRecipeSerializer,
                          IngredientSerializer, FavoriteSerializer,
                          BasketSerializer)


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
        author_id = self.request.query_params.get('author')
        if author_id:
            rows = rows.filter(author_id=author_id)
        favorited = self.request.query_params.get('is_favorited')
        if favorited and user.is_authenticated:
            filter_for_user = Q(fav_r__user=user)
            rows = rows.filter(filter_for_user
                               if favorited == '1' else ~filter_for_user)
        in_basket = self.request.query_params.get('is_in_shopping_cart')
        if in_basket and user.is_authenticated:
            filter_for_user = Q(basket_r__user=user)
            rows = rows.filter(filter_for_user
                               if in_basket == '1' else ~filter_for_user)
        return rows

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return NewRecipeSerializer
        return GetRecipeSerializer


class RecipeView(RecipesList, generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthorOrReadOnly]
    lookup_field = 'id'
    lookup_url_kwarg = 'recipe_id'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return NewRecipeSerializer
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
        recipe_id = kwargs['recipe_id']
        recipe_in_fav = get_object_or_404(Recipe, id=recipe_id)
        if request.user.fav_u.filter(
                recipe=recipe_in_fav,
        ).exists():
            return Response(
                {"detail": "Рецепт уже в избранном."},
                status=status.HTTP_400_BAD_REQUEST
            )
        favorite = FavRecipe.objects.create(user=request.user,
                                            recipe=recipe_in_fav)
        serializer = self.get_serializer(favorite)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_object(self):
        recipe_id = self.kwargs['recipe_id']
        recipe_in_fav = get_object_or_404(Recipe, id=recipe_id)
        try:
            return FavRecipe.objects.get(
                user=self.request.user, recipe=recipe_in_fav,
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
        recipe_id = kwargs['recipe_id']
        recipe_in_basket = get_object_or_404(Recipe, id=recipe_id)
        if request.user.basket_u.filter(recipe=recipe_in_basket).exists():
            return Response(
                {"detail": "Рецепт уже в списке покупок."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user_basket = Basket.objects.create(user=request.user,
                                            recipe=recipe_in_basket)
        user_basket = self.get_serializer(user_basket)
        return Response(user_basket.data, status=status.HTTP_201_CREATED)

    def get_object(self):
        recipe_id = self.kwargs['recipe_id']
        recipe_in_basket = get_object_or_404(Recipe, id=recipe_id)
        try:
            return Basket.objects.get(user=self.request.user,
                                      recipe=recipe_in_basket)
        except Basket.DoesNotExist:
            raise ValidationError(
                {"detail": "Нет такого рецепта в списке покупок."},
                code=status.HTTP_400_BAD_REQUEST
            )


class BasketDownload(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rtext = ["Выбранные рецепты:\n"]
        basket_recipes, basket_ingredients = (
            self.get_basket_data(request.user))
        for i in basket_recipes:
            rtext.append(i.name)
        rtext.append("-" * 50)
        rtext.append("\nНеобходимые продукты:\n")
        for i in basket_ingredients:
            rtext.append(f"{i['ingredient__name']}: {i['amount']} "
                         f"{i['ingredient__measurement_unit']}"
                         )
        response = HttpResponse("\n".join(rtext), content_type="text/plain")
        response["Content-Disposition"] = 'attachment; filename="shopping-list.txt"'
        return response

    def get_basket_data(self, user):
        recipes_query = user.basket_u.all().order_by('recipe__name')
        basket_recipes = [i.recipe for i in recipes_query]
        basket_ingredients = (
            IRLinkModel.objects.filter(recipe__in=basket_recipes)
            .values("ingredient__name", "ingredient__measurement_unit")
            .annotate(amount=Sum("amount"))
        )
        return basket_recipes, basket_ingredients

