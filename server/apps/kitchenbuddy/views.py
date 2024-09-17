import httpx
import json
import os

from django.conf import settings
from django.template import Template, Context
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from .serializers import RecipeSerializer, GroceryListSerializer
from .models import User, Recipe, GroceryList


OPENAI_URL = 'https://api.openai.com/v1/chat/completions'

client = httpx.Client(http2=True)

with open(str(settings.APPS_DIR / 'kitchenbuddy/ai-templates/system_prompt.txt'), 'r') as f:
    system_prompt = f.read()

with open(str(settings.APPS_DIR / 'kitchenbuddy/ai-templates/user_prompt.tpl'), 'r') as f:
    user_prompt_template = Template(f.read())

with open(str(settings.APPS_DIR / 'kitchenbuddy/ai-templates/recipe_function_call_schema.json'), 'r') as f:
    recipe_function_call_schema = json.load(f)


@api_view(['GET', 'POST'])
def recipe_view(request):
    if request.method == 'POST':
        return create_recipe(request)
    elif request.method == 'GET':
        return get_recipes(request)

@api_view(['GET', 'POST'])
def grocery_list_view(request):
    if request.method == 'POST':
        return add_to_grocery_list(request)
    elif request.method == 'GET':
        return get_grocery_list(request)

def create_recipe(request):
    serializer = RecipeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    url = serializer.validated_data['url']
    user, _ = User.objects.get_or_create(username=request.data['username'])

    # Check if the recipe is already in the database
    recipe = Recipe.objects.filter(url=url, user=user).first()
    if recipe:
        return Response({
            "recipe": RecipeSerializer(recipe).data,
        }, status=status.HTTP_200_OK)

    response = client.get(url)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        return Response({
            "error": f"Failed to fetch recipe: {e.response.status_code} {e.response.text}",
        }, status=status.HTTP_400_BAD_REQUEST)

    recipe_content = response.text
    user_prompt = user_prompt_template.render(Context({
        'html': recipe_content,
    }))

    data = {
        "model": "gpt-4o",
        "temperature": 1,
        "messages": [{
            "role": "system",
            "content": system_prompt,
        }, {
            "role": "user",
            "content": user_prompt,
        }],
        "tool_choice": {
            "type": "function",
            "function": {
                "name": "provide_recipe"
            }
        },
        "tools": [{
            "type": "function",
            "function": recipe_function_call_schema,
        }],
    }

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "Content-Type": "application/json",
    }

    try:
        completion_response = client.post(OPENAI_URL, json=data, headers=headers, timeout=30)
        completion_response.raise_for_status()
    except httpx.HTTPStatusError as e:
        return Response({
            "error": f"Failed to parse recipe with OpenAI: {e.response.status_code} {e.response.text}",
        }, status=status.HTTP_400_BAD_REQUEST)

    completion = completion_response.json()

    try:
        tool_calls = completion['choices'][0]['message']['tool_calls']
        for tool_call in tool_calls:
            if tool_call['function']['name'] == "provide_recipe":
                arguments = json.loads(tool_call['function']['arguments'])

                serializer.save(
                    title=arguments['title'],
                    url=url,
                    content=recipe_content,
                    user=user,
                    parsed_recipe=arguments,
                )

                return Response({
                    "recipe": serializer.data,
                }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({
            "error": str(e),
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        "error": "Failed to parse recipe",
    }, status=status.HTTP_400_BAD_REQUEST)

def get_recipes(request):
    recipes = Recipe.objects.filter(user__username=request.GET.get('username')).order_by('-created_at')
    serializer = RecipeSerializer(recipes, many=True)
    return Response({
        "recipes": serializer.data,
    }, status=status.HTTP_200_OK)

def get_grocery_list(request):
    grocery_list = GroceryList.objects.filter(user__username=request.GET.get('username')).order_by('-created_at')
    serializer = GroceryListSerializer(grocery_list, many=True)
    return Response({
        "items": serializer.data.items,
    }, status=status.HTTP_200_OK)

def add_to_grocery_list(request):
    serializer = GroceryListSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()
    return Response({}, status=status.HTTP_201_CREATED)
