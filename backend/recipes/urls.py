from django.urls import path
from .views import (RecipeListView, RecipeView, ShortLinkView,
                    FavView, BasketView, BasketDownload)


urlpatterns = [
    path('', RecipeListView.as_view()),
    path('<int:recipe_id>/', RecipeView.as_view()),
    path('<int:recipe_id>/get-link/', ShortLinkView.as_view()),
    path('<int:recipe_id>/favorite/', FavView.as_view()),
    path('<int:recipe_id>/shopping_cart/', BasketView.as_view()),
    path('download_shopping_cart/', BasketDownload.as_view())
]
