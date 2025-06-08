from django.contrib import admin
from django.db.models import Count
from .models import *


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'f_count')
    search_fields = ('name', 'author__username', 'author__email')

    def get_queryset(self, request):
        rows = super().get_queryset(request)
        return rows.annotate(
            _f_count=Count('fav_r', distinct=True)
        )

    def f_count(self, obj):
        return obj._f_count


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(IRLinkModel)
admin.site.register(FavRecipe)
admin.site.register(Basket)

