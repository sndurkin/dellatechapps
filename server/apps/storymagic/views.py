from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Story
from .serializers import StorySerializer

@api_view(['GET'])
def story_list(request):
    stories = Story.objects.all()
    serializer = StorySerializer(stories, many=True)
    return Response(serializer.data)
