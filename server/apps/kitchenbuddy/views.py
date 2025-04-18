import httpx
import json
import os
from difflib import SequenceMatcher

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
    username = request.data.pop('username', None)
    if not username:
        return Response({
            "error": "username is a required field",
        }, status=status.HTTP_400_BAD_REQUEST)

    serializer = RecipeSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    url = serializer.validated_data['url']
    user, _ = User.objects.get_or_create(username=username)

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
    if not grocery_list.exists():
        return Response({
            "items": [],
        }, status=status.HTTP_200_OK)

    serializer = GroceryListSerializer(grocery_list.first(), many=False)
    return Response({
        "items": serializer.data['items'],
    }, status=status.HTTP_200_OK)

def sort_grocery_items(items, all_items_sorted):
    # Create a map of item to its position
    item_positions = {}

    # Try exact matches first
    for item in items:
        try:
            item_positions[item] = all_items_sorted.index(item)
        except ValueError:
            item_positions[item] = -1

    # For items without exact matches, find best matches using SequenceMatcher
    for item in [i for i, pos in item_positions.items() if pos == -1]:
        best_ratio = 0
        best_position = -1

        for idx, reference in enumerate(all_items_sorted):
            # Compare strings case-insensitively
            matcher = SequenceMatcher(None, item.lower(), reference.lower())
            ratio = matcher.ratio()

            # Only consider matches with ratio > 0.8 (very similar strings)
            if ratio > 0.8 and ratio > best_ratio:
                best_ratio = ratio
                best_position = idx

        item_positions[item] = best_position

    # Sort items based on their positions
    return sorted(items, key=lambda x: item_positions[x])

def add_to_grocery_list(request):
    username = request.data.pop('username', None)
    if not username:
        return Response({
            "error": "username is a required field",
        }, status=status.HTTP_400_BAD_REQUEST)

    serializer = GroceryListSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user, _ = User.objects.get_or_create(username=username)

    # Get or create grocery list
    grocery_list = GroceryList.objects.filter(user=user).first()
    if grocery_list:
        # Update existing list
        new_items = serializer.validated_data['items']

        # Add new items to the beginning of all_items_sorted if they don't exist
        all_items_sorted = grocery_list.all_items_sorted
        for item in new_items:
            if item not in all_items_sorted:
                all_items_sorted.insert(0, item)

        # Sort the new items based on all_items_sorted
        sorted_items = sort_grocery_items(new_items, all_items_sorted)

        # Update both items and all_items_sorted
        grocery_list.items = sorted_items
        grocery_list.all_items_sorted = all_items_sorted
        grocery_list.save()
    else:
        # Create new list - for new lists, items and all_items_sorted are the same
        grocery_list = serializer.save(
            user=user,
            all_items_sorted=serializer.validated_data['items'],
            items=serializer.validated_data['items']
        )

    return Response({
        "items": grocery_list.items,
        "all_items_sorted": grocery_list.all_items_sorted
    }, status=status.HTTP_201_CREATED)

@api_view(['GET', 'POST'])
def manage_all_items_sorted(request):
    username = request.GET.get('username') if request.method == 'GET' else request.data.get('username')
    if not username:
        return Response({
            "error": "username is a required field",
        }, status=status.HTTP_400_BAD_REQUEST)

    grocery_list = GroceryList.objects.filter(user__username=username).first()
    if not grocery_list:
        return Response({
            "all_items_sorted": [],
        }, status=status.HTTP_200_OK)

    if request.method == 'GET':
        return Response({
            "all_items_sorted": grocery_list.all_items_sorted,
        }, status=status.HTTP_200_OK)

    action = request.data.get('action')
    if action not in ['remove', 'move', 'replace']:
        return Response({
            "error": "Invalid action. Must be one of: remove, move, replace",
        }, status=status.HTTP_400_BAD_REQUEST)

    all_items_sorted = grocery_list.all_items_sorted

    if action == 'remove':
        items = request.data.get('items', [])
        if not isinstance(items, list):
            items = [items]
        all_items_sorted = [item for item in all_items_sorted if item not in items]

    elif action == 'move':
        item = request.data.get('item')
        new_position = request.data.get('new_position')
        if item is None or new_position is None:
            return Response({
                "error": "Both item and new_position are required for move action",
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            current_position = all_items_sorted.index(item)
            all_items_sorted.pop(current_position)
            all_items_sorted.insert(new_position, item)
        except ValueError:
            return Response({
                "error": f"Item '{item}' not found in all_items_sorted",
            }, status=status.HTTP_400_BAD_REQUEST)
        except IndexError:
            return Response({
                "error": f"Invalid new_position: {new_position}",
            }, status=status.HTTP_400_BAD_REQUEST)

    elif action == 'replace':
        new_items = request.data.get('items', [])
        if not isinstance(new_items, list):
            return Response({
                "error": "items must be a list for replace action",
            }, status=status.HTTP_400_BAD_REQUEST)
        all_items_sorted = new_items

    grocery_list.all_items_sorted = all_items_sorted
    grocery_list.save()

    return Response({
        "all_items_sorted": all_items_sorted,
    }, status=status.HTTP_200_OK)

