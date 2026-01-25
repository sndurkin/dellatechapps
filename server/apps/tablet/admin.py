from django.contrib import admin

from .models import BusSession, BusData, BusDashboardSkip

class BusSessionAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'cookies_data', 'time_of_day_values', 'last_refresh', 'created_at', 'updated_at')
    pass

class BusDataAdmin(admin.ModelAdmin):
    list_display = ('session', 'created_at', 'bus_location', 'error_message')

class BusDashboardSkipAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active', 'created_at')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('name',)
    date_hierarchy = 'start_date'

admin.site.register(BusSession, BusSessionAdmin)
admin.site.register(BusData, BusDataAdmin)
admin.site.register(BusDashboardSkip, BusDashboardSkipAdmin)
