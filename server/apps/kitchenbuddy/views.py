import httpx
import json
import os
from difflib import SequenceMatcher

from django.conf import settings
from django.template import Template, Context
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from constance import config

from .serializers import RecipeSerializer, GroceryListSerializer
from .models import User, Recipe, GroceryList


OPENAI_URL = 'https://api.openai.com/v1/chat/completions'

client = httpx.Client(http2=True)

def extract_item_name(item_text):
    """
    Extract the main item name from text that may contain additional info after a comma.
    Example: "tomato sauce, 32oz" -> "tomato sauce"
    """
    return item_text.split(',')[0].strip().lower()

with open(str(settings.APPS_DIR / 'kitchenbuddy/ai-templates/system_prompt.txt'), 'r') as f:
    system_prompt = f.read()

with open(str(settings.APPS_DIR / 'kitchenbuddy/ai-templates/user_prompt.tpl'), 'r') as f:
    user_prompt_template = Template(f.read())

with open(str(settings.APPS_DIR / 'kitchenbuddy/ai-templates/recipe_function_call_schema.json'), 'r') as f:
    recipe_function_call_schema = json.load(f)


@api_view(['GET', 'POST', 'DELETE'])
def recipe_view(request):
    if request.method == 'POST':
        return create_recipe(request)
    elif request.method == 'GET':
        return get_recipes(request)
    elif request.method == 'DELETE':
        return delete_recipe(request)

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
        **json.loads(config.KITCHENBUDDY_OPENAI),
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
    username = request.GET.get('username') or request.data.get('username')
    recipes = Recipe.objects.filter(user__username=username).order_by('-created_at')
    serializer = RecipeSerializer(recipes, many=True)
    return Response({
        "recipes": serializer.data,
    }, status=status.HTTP_200_OK)

def delete_recipe(request):
    username = request.data.get('username')
    if not username:
        return Response({
            "error": "username is a required field",
        }, status=status.HTTP_400_BAD_REQUEST)

    recipe_id = request.data.get('id')
    if recipe_id is None:
        return Response({
            "error": "id is a required field",
        }, status=status.HTTP_400_BAD_REQUEST)

    recipe = Recipe.objects.filter(id=recipe_id, user__username=username).first()
    if not recipe:
        return Response({
            "error": "Recipe not found",
        }, status=status.HTTP_404_NOT_FOUND)

    recipe.delete()
    return get_recipes(request)

@api_view(['GET'])
def get_grocery_list(request):
    grocery_list = GroceryList.objects.filter(user__username=request.GET.get('username')).order_by('-created_at')
    if not grocery_list.exists():
        return Response({
            "items": [],
            "item_counts": {},
        }, status=status.HTTP_200_OK)

    grocery_list = grocery_list.first()
    serializer = GroceryListSerializer(grocery_list, many=False)
    items = serializer.data['items']
    item_counts = serializer.data['item_counts']

    # Sort the items using the reference list
    sorted_items = sort_grocery_items(items, grocery_list.all_items_sorted)

    return Response({
        "items": sorted_items,
        "item_counts": item_counts,
    }, status=status.HTTP_200_OK)

def sort_grocery_items(items, all_items_sorted):
    # Create a map of item to its position
    item_positions = {}

    # Try exact matches first (both full item and clean name)
    for item in items:
        clean_item = extract_item_name(item)

        # Try exact match with full item first
        try:
            item_positions[item] = all_items_sorted.index(item)
            continue
        except ValueError:
            pass

        # Try exact match with clean item name
        try:
            item_positions[item] = all_items_sorted.index(clean_item)
            continue
        except ValueError:
            item_positions[item] = -1

    # Sort items based on their positions
    return sorted(items, key=lambda x: item_positions[x])

@api_view(['POST'])
def add_to_grocery_list(request):
    username = request.data.pop('username', None)
    if not username:
        return Response({
            "error": "username is a required field",
        }, status=status.HTTP_400_BAD_REQUEST)

    # Keep original items with additional info, but convert to lowercase for consistency
    request.data['items'] = [item.lower() for item in request.data.get('items', [])]

    # Initialize item_counts if not provided
    if 'item_counts' not in request.data:
        request.data['item_counts'] = {}

    serializer = GroceryListSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user, _ = User.objects.get_or_create(username=username)

    # Get or create grocery list
    grocery_list = GroceryList.objects.filter(user=user).first()
    if grocery_list:
        # Add to existing list
        new_items = serializer.validated_data['items']

        # Count occurrences of each item (using full item text)
        updated_item_counts = grocery_list.item_counts.copy()
        for item in new_items:
            updated_item_counts[item] = updated_item_counts.get(item, 0) + 1

        # Combine existing items with new items, removing duplicates (preserve full item text)
        combined_items = list(dict.fromkeys(grocery_list.items + new_items))

        # Add new items to all_items_sorted using clean names only
        all_items_sorted = grocery_list.all_items_sorted
        for item in new_items:
            clean_item = extract_item_name(item)
            if clean_item not in all_items_sorted:
                all_items_sorted.insert(get_best_position(clean_item, all_items_sorted), clean_item)

        # Sort the combined items based on all_items_sorted
        sorted_items = sort_grocery_items(combined_items, all_items_sorted)

        # Update both items and all_items_sorted
        grocery_list.items = sorted_items
        grocery_list.all_items_sorted = all_items_sorted
        grocery_list.item_counts = updated_item_counts

        grocery_list.save()
    else:
        # Create new list - items contain full text, all_items_sorted contains clean names
        # Remove duplicates from initial items (preserve full item text)
        unique_items = list(dict.fromkeys(serializer.validated_data['items']))
        # Create all_items_sorted with clean names only
        unique_clean_items = list(dict.fromkeys([extract_item_name(item) for item in unique_items]))
        # Initialize counts for new items
        item_counts = serializer.validated_data.get('item_counts', {})

        grocery_list = serializer.save(
            user=user,
            all_items_sorted=unique_clean_items,
            items=unique_items,
            item_counts=item_counts
        )

    return Response({
        "items": grocery_list.items,
        "all_items_sorted": grocery_list.all_items_sorted,
        "item_counts": grocery_list.item_counts,
    }, status=status.HTTP_201_CREATED)

def get_best_position(item, all_items_sorted):
    best_ratio = 0
    best_position = 0
    for idx, reference in enumerate(all_items_sorted):
        matcher = SequenceMatcher(None, item.lower(), reference.lower())
        ratio = matcher.ratio()
        if ratio > 0.8 and ratio > best_ratio:
            best_ratio = ratio
            best_position = idx
    return best_position

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

@api_view(['POST'])
def remove_from_grocery_list(request):
    username = request.data.pop('username', None)
    if not username:
        return Response({
            "error": "username is a required field",
        }, status=status.HTTP_400_BAD_REQUEST)

    items_to_remove = request.data.get('items', [])
    if not isinstance(items_to_remove, list):
        items_to_remove = [items_to_remove]

    # Convert all items to lowercase
    items_to_remove = [item.lower() for item in items_to_remove]

    user, _ = User.objects.get_or_create(username=username)
    grocery_list = GroceryList.objects.filter(user=user).first()

    if not grocery_list:
        return Response({
            "error": "No grocery list found for this user",
        }, status=status.HTTP_404_NOT_FOUND)

    # Remove items from the main list
    grocery_list.items = [item for item in grocery_list.items if item not in items_to_remove]

    # Remove items from item_counts
    for item in items_to_remove:
        if item in grocery_list.item_counts:
            del grocery_list.item_counts[item]

    grocery_list.save()

    return Response({
        "items": grocery_list.items,
        "all_items_sorted": grocery_list.all_items_sorted,
        "item_counts": grocery_list.item_counts,
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
def update_item_count(request):
    username = request.data.pop('username', None)
    if not username:
        return Response({
            "error": "username is a required field",
        }, status=status.HTTP_400_BAD_REQUEST)

    item = request.data.get('item')
    count = request.data.get('count')

    if item is None or count is None:
        return Response({
            "error": "Both item and count are required fields",
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        count = int(count)
        if count < 1:
            return Response({
                "error": "Count must be a positive integer",
            }, status=status.HTTP_400_BAD_REQUEST)
    except ValueError:
        return Response({
            "error": "Count must be a positive integer",
        }, status=status.HTTP_400_BAD_REQUEST)

    # Convert item to lowercase
    item = item.lower()

    user, _ = User.objects.get_or_create(username=username)
    grocery_list = GroceryList.objects.filter(user=user).first()

    if not grocery_list:
        return Response({
            "error": "No grocery list found for this user",
        }, status=status.HTTP_404_NOT_FOUND)

    if item not in grocery_list.items:
        return Response({
            "error": f"Item '{item}' not found in grocery list",
        }, status=status.HTTP_404_NOT_FOUND)

    # Update the count
    if count == 1:
        del grocery_list.item_counts[item]
    else:
        grocery_list.item_counts[item] = count

    grocery_list.save()

    return Response({
        "items": grocery_list.items,
        "all_items_sorted": grocery_list.all_items_sorted,
        "item_counts": grocery_list.item_counts,
    }, status=status.HTTP_200_OK)

