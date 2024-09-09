import os

from django.urls import path
from django.conf import settings
from django.http import HttpResponse
from django.views.static import serve


def home_view(request):
    index_file_path = os.path.join(settings.BASE_DIR, 'static/kitchenbuddy/index.html')
    with open(index_file_path, 'r') as f:
        return HttpResponse(f.read(), content_type='text/html')

urlpatterns = [
    path('', home_view, name='home'),
    # path('api/stories/', create_story, name='create_story'),

    path('<path:path>', serve, {
        'document_root': os.path.join(settings.BASE_DIR, 'static/kitchenbuddy'),
    }),
]
