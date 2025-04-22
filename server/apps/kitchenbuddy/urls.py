import os

from django.urls import path
from django.conf import settings
from django.http import HttpResponse
from django.views.static import serve

from .views import recipe_view, get_grocery_list, manage_all_items_sorted, remove_from_grocery_list, update_item_count, add_to_grocery_list


def home_view(request, unique_id = None):
    # Simply serve the index.html file - nginx will handle the hot reloading
    index_file_path = os.path.join(settings.BASE_DIR, 'static/kitchenbuddy/index.html')
    with open(index_file_path, 'r') as f:
        return HttpResponse(f.read(), content_type='text/html')

urlpatterns = [
    path('', home_view, name='home'),

    path('api/recipes/', recipe_view, name='recipe_view'),
    path('api/list/', get_grocery_list, name='grocery_list_view'),
    path('api/list/add/', add_to_grocery_list, name='add_to_grocery_list'),
    path('api/list/remove/', remove_from_grocery_list, name='remove_from_grocery_list'),
    path('api/list/update-count/', update_item_count, name='update_item_count'),
    path('api/manage-all/', manage_all_items_sorted, name='manage_all_items_sorted'),

    path('u/<str:unique_id>/', home_view),  # Serves the same page as /
    path('u/<str:unique_id>/list/', home_view),  # Serves the same page as /
    path('u/<str:unique_id>/list-all/', home_view),  # Serves the same page as /
    path('u/<str:unique_id>/new/', home_view),  # Serves the same page as /
    path('u/<str:unique_id>/recipe/', home_view),  # Serves the same page as /
]
