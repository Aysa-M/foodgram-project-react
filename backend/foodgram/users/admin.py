from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from foodgram.settings import EMPTY_VALUE_DISPLAY

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import Subscription, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = (
        'id',
        'username',
        'password',
        'email',
        'first_name',
        'last_name',
        'role',
    )
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
        'role',
    )
    list_editable = (
        'username',
        'password',
        'role',
    )
    list_filter = ('username', 'email',)
    empty_value_display = EMPTY_VALUE_DISPLAY


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author',)
    list_editable = ('author',)
    list_filter = ('user', 'author',)
    search_fields = ('user', 'author',)
    empty_value_display = EMPTY_VALUE_DISPLAY
