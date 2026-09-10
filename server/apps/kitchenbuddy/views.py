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


def parse_item_amount(amount):
    """Return a positive numeric increment for grocery list item_counts."""
    if amount is None or amount == '':
        return 1
    if isinstance(amount, bool):
        return 1
    if isinstance(amount, (int, float)):
        return amount if amount > 0 else 1
    try:
        value = float(amount)
    except (TypeError, ValueError):
        return 1
    if value <= 0:
        return 1
    if value.is_integer():
        return int(value)
    return value

with open(str(settings.APPS_DIR / 'kitchenbuddy/ai-templates/system_prompt.txt'), 'r') as f:
    system_prompt = f.read()

with open(str(settings.APPS_DIR / 'kitchenbuddy/ai-templates/user_prompt.tpl'), 'r') as f:
    user_prompt_template = Template(f.read())

with open(str(settings.APPS_DIR / 'kitchenbuddy/ai-templates/edit_system_prompt.txt'), 'r') as f:
    edit_system_prompt = f.read()

with open(str(settings.APPS_DIR / 'kitchenbuddy/ai-templates/edit_user_prompt.tpl'), 'r') as f:
    edit_user_prompt_template = Template(f.read())

with open(str(settings.APPS_DIR / 'kitchenbuddy/ai-templates/recipe_function_call_schema.json'), 'r') as f:
    recipe_function_call_schema = json.load(f)


def request_recipe_from_openai(messages, timeout=30):
    data = {
        **json.loads(config.KITCHENBUDDY_OPENAI),
        "messages": messages,
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
        completion_response = client.post(OPENAI_URL, json=data, headers=headers, timeout=timeout)
        completion_response.raise_for_status()
    except httpx.HTTPStatusError as e:
        return None, Response({
            "error": f"Failed to parse recipe with OpenAI: {e.response.status_code} {e.response.text}",
        }, status=status.HTTP_400_BAD_REQUEST)
    except httpx.RequestError as e:
        return None, Response({
            "error": f"Failed to parse recipe with OpenAI: {str(e)}",
        }, status=status.HTTP_400_BAD_REQUEST)

    completion = completion_response.json()

    try:
        tool_calls = completion['choices'][0]['message']['tool_calls']
        for tool_call in tool_calls:
            if tool_call['function']['name'] == "provide_recipe":
                return json.loads(tool_call['function']['arguments']), None
    except Exception as e:
        return None, Response({
            "error": str(e),
        }, status=status.HTTP_400_BAD_REQUEST)

    return None, Response({
        "error": "Failed to parse recipe",
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST', 'DELETE', 'PATCH'])
def recipe_view(request):
    if request.method == 'POST':
        return create_recipe(request)
    elif request.method == 'GET':
        return get_recipes(request)
    elif request.method == 'DELETE':
        return delete_recipe(request)
    elif request.method == 'PATCH':
        return edit_recipe(request)

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

    arguments, error_response = request_recipe_from_openai([{
        "role": "system",
        "content": system_prompt,
    }, {
        "role": "user",
        "content": user_prompt,
    }])
    if error_response:
        return error_response

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

def edit_recipe(request):
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

    instructions = (request.data.get('instructions') or '').strip()
    if not instructions:
        return Response({
            "error": "instructions is a required field",
        }, status=status.HTTP_400_BAD_REQUEST)

    recipe = Recipe.objects.filter(id=recipe_id, user__username=username).first()
    if not recipe:
        return Response({
            "error": "Recipe not found",
        }, status=status.HTTP_404_NOT_FOUND)

    recipe_json = request.data.get('recipe') or recipe.parsed_recipe
    user_prompt = edit_user_prompt_template.render(Context({
        'recipe_json': json.dumps(recipe_json, indent=2),
        'instructions': instructions,
    }))

    arguments, error_response = request_recipe_from_openai([{
        "role": "system",
        "content": edit_system_prompt,
    }, {
        "role": "user",
        "content": user_prompt,
    }], timeout=60)
    if error_response:
        return error_response

    try:
        recipe.title = arguments['title']
        recipe.parsed_recipe = arguments
        recipe.save()
    except Exception as e:
        return Response({
            "error": str(e),
        }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        "recipe": RecipeSerializer(recipe).data,
    }, status=status.HTTP_200_OK)

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
    username = request.data.get('username')
    if not username:
        return Response({
            "error": "username is a required field",
        }, status=status.HTTP_400_BAD_REQUEST)

    new_items = parse_items_to_add(request.data)
    if not new_items:
        return Response({
            "error": "item or items is required",
        }, status=status.HTTP_400_BAD_REQUEST)

    increment = parse_item_amount(request.data.get('amount'))
    user, _ = User.objects.get_or_create(username=username)
    grocery_list = GroceryList.objects.filter(user=user).first()

    if grocery_list:
        merge_items_into_grocery_list(grocery_list, new_items, increment)
    else:
        item_counts = {}
        if increment != 1:
            item_counts = {item: increment for item in new_items}
        grocery_list = GroceryList.objects.create(
            user=user,
            items=new_items,
            all_items_sorted=list(dict.fromkeys(extract_item_name(item) for item in new_items)),
            item_counts=item_counts,
        )

    return Response({
        "items": grocery_list.items,
        "all_items_sorted": grocery_list.all_items_sorted,
        "item_counts": grocery_list.item_counts,
    }, status=status.HTTP_201_CREATED)


def parse_items_to_add(data):
    """Collect items to add. Does not replace the existing grocery list."""
    new_items = []
    item = data.get('item')
    if item is not None and str(item).strip():
        new_items.append(str(item).strip().lower())

    items = data.get('items')
    if items:
        if not isinstance(items, list):
            items = [items]
        new_items.extend(str(entry).strip().lower() for entry in items if str(entry).strip())

    return list(dict.fromkeys(new_items))


def merge_items_into_grocery_list(grocery_list, new_items, increment):
    updated_item_counts = dict(grocery_list.item_counts or {})
    existing_items = grocery_list.items or []

    for item in new_items:
        current = updated_item_counts.get(item, 1 if item in existing_items else 0)
        updated_item_counts[item] = current + increment

    combined_items = list(dict.fromkeys(existing_items + new_items))
    all_items_sorted = list(grocery_list.all_items_sorted or [])
    for item in new_items:
        clean_item = extract_item_name(item)
        if clean_item not in all_items_sorted:
            all_items_sorted.insert(get_best_position(clean_item, all_items_sorted), clean_item)

    grocery_list.items = sort_grocery_items(combined_items, all_items_sorted)
    grocery_list.all_items_sorted = all_items_sorted
    grocery_list.item_counts = updated_item_counts
    grocery_list.save()

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

