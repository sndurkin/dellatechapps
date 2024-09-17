from django.contrib import admin

from .models import User, Recipe, GroceryList


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user__username', 'title', 'url', 'created_at', 'updated_at')
    search_fields = ('title', 'url', 'user__username')
    list_filter = ('created_at', 'updated_at')
    ordering = ('-created_at',)

admin.site.register(Recipe, RecipeAdmin)

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'created_at', 'updated_at')
    search_fields = ('username',)
    ordering = ('-created_at',)

admin.site.register(User, UserAdmin)

class GroceryListAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at', 'items')
    search_fields = ('user__username',)
    ordering = ('-created_at',)

admin.site.register(GroceryList, GroceryListAdmin)
