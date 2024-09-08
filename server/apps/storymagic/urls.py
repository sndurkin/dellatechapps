import os
from django.urls import path
from django.conf import settings
from django.http import HttpResponse
from django.views.static import serve


def storymagic_home(request):
    index_file_path = os.path.join(settings.BASE_DIR, 'static/storymagic/index.html')
    with open(index_file_path, 'r') as f:
        return HttpResponse(f.read(), content_type='text/html')

urlpatterns = [
    path('', storymagic_home, name='storymagic_home'),

    path('<path:path>', serve, {
        'document_root': os.path.join(settings.BASE_DIR, 'static/storymagic'),
    }),
]
