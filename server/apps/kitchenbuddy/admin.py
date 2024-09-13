from django.contrib import admin

from .models import Recipe


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'created_at', 'updated_at')
    search_fields = ('title', 'url')
    list_filter = ('created_at', 'updated_at')
    ordering = ('-created_at',)

admin.site.register(Recipe, RecipeAdmin)
