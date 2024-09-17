import os

from django.urls import path
from django.conf import settings
from django.http import HttpResponse
from django.views.static import serve

from .views import recipe_view, grocery_list_view


def home_view(request, unique_id):
    index_file_path = os.path.join(settings.BASE_DIR, 'static/kitchenbuddy/index.html')
    with open(index_file_path, 'r') as f:
        return HttpResponse(f.read(), content_type='text/html')

urlpatterns = [
    path('', home_view, name='home'),

    path('api/recipes/', recipe_view, name='recipe_view'),
    path('api/list/', grocery_list_view, name='grocery_list_view'),

    path('<str:unique_id>/', home_view),  # Serves the same page as /
    path('<str:unique_id>/list/', home_view),  # Serves the same page as /
]
