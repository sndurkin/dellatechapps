import os

from django.urls import path
from django.conf import settings
from django.http import HttpResponse
from django.views.static import serve

from .views import bus_view, invalidate_session_view, session_status_view, weather_view, status_view, dashboard_view, test_bus_view, test_client_view


urlpatterns = [
    path('', test_client_view, name='test_client'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('bus', bus_view, name='bus'),
    path('bus/test/<int:num>/', test_bus_view, name='test_bus'),
    path('bus/invalidate', invalidate_session_view, name='bus_invalidate'),
    path('bus/status', session_status_view, name='bus_status'),
    path('weather/', weather_view, name='weather'),
    path('status/', status_view, name='status'),
]
