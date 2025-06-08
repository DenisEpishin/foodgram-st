from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *


class CustomUser(UserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff'
    )
    search_fields = ('email', 'username')


admin.site.register(User, CustomUser)
admin.site.register(Follow)


