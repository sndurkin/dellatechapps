from django.contrib import admin

from .models import Story

class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'grade', 'sentence_count', 'created_at', 'updated_at')
    search_fields = ('title',)
    list_filter = ('grade', 'created_at', 'updated_at')
    ordering = ('-created_at',)

admin.site.register(Story, StoryAdmin)
