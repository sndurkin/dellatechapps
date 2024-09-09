import json
import os
from openai import OpenAI

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from .serializers import StorySerializer

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY')
)


@api_view(['POST'])
def create_story(request):
    serializer = StorySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    grade = serializer.validated_data['grade']
    topic = serializer.validated_data['topic']
    sentence_count = serializer.validated_data['sentence_count']

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "system",
            "content": "You are an expert author that can write short stories for children to use to learn to read. Your task is to write the perfect, age-appropriate short story given the topic, sentence count and any other details. Return the title and sentences of the story. Ensure that the sentences are organized into an array of strings."
        },
        {
            "role": "user",
            "content": f"""Create a story for a child in grade "{grade}" with the topic:

<topic>{topic}</topic>

The story should not include words that are too difficult for a child in this grade. The story should include some sight words appropriate for this grade.

The story should be no more than {sentence_count} sentences long.""",
        }],
        tool_choice={
            "type": "function",
            "function": {
                "name": "provide_story"
            }
        },
        tools=[{
            "type": "function",
            "function": {
                "name": "provide_story",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The title of the story.",
                        },
                        "sentences": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "description": "An individual sentence in the story.",
                            },
                            "description": "The sentences of the story.",
                        },
                    },
                    "required": ["title", "sentences"],
                },
            },
        }]
    )

    tool_calls = completion.choices[0].message.tool_calls;
    for tool_call in tool_calls:
        if tool_call.function.name == "provide_story":
            arguments = json.loads(tool_call.function.arguments)

            serializer.save(
                title=arguments['title'],
                sentences=arguments['sentences'],
            )

            return Response({
                'story': serializer.data,
                'word_mappings': {},
            }, status=status.HTTP_201_CREATED)
