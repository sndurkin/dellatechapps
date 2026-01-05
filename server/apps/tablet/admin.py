from django.contrib import admin

from .models import BusSession, BusData

class BusSessionAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'cookies_data', 'time_of_day_values', 'last_refresh', 'created_at', 'updated_at')
    pass

class BusDataAdmin(admin.ModelAdmin):
    list_display = ('session', 'created_at', 'bus_location', 'error_message')

admin.site.register(BusSession, BusSessionAdmin)
admin.site.register(BusData, BusDataAdmin)
