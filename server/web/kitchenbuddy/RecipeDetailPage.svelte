<script>
  import { onMount, onDestroy } from "svelte";

  import * as recipeUtils from './recipeUtils';
  import * as utils from '../shared/utils';


  export let recipe;

  let wakeLock;
  let addedItems = new Set();
  let addingItems = new Set();

  function formatIngredientLine(ingredient) {
    if (typeof ingredient === 'string') {
      return ingredient;
    }
    if (ingredient?.name == null) {
      return null;
    }
    const parts = [ingredient.name];
    if (ingredient.modifier) {
      parts.push(ingredient.modifier);
    }
    if (ingredient.amount != null && ingredient.amount !== '') {
      parts.push(ingredient.amount);
    }
    return parts.join(', ');
  }

  function getIngredientEntries(ingredients) {
    const entries = [];
    for (const ingredient of ingredients || []) {
      if (ingredient?.items) {
        for (const item of ingredient.items) {
          entries.push({ line: item });
        }
        continue;
      }
      const line = formatIngredientLine(ingredient);
      if (line) {
        entries.push({
          line,
          amount: typeof ingredient === 'object' ? ingredient.amount : undefined,
        });
      }
    }
    return entries;
  }

  $: ingredientEntries = getIngredientEntries(recipe?.ingredients);

  async function addToGroceryList(item, amount) {
    if (addedItems.has(item) || addingItems.has(item)) {
      return;
    }

    addingItems.add(item);
    addingItems = addingItems;

    const body = {
      item,
      username: recipeUtils.getUsername(),
    };
    if (typeof amount === 'number') {
      body.amount = amount;
    }

    try {
      const response = await fetch('/kitchenbuddy/api/list/add/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': utils.getCsrfToken(),
        },
        body: JSON.stringify(body),
      });

      if (response.ok) {
        addedItems.add(item);
        addedItems = addedItems;
      }
    } finally {
      addingItems.delete(item);
      addingItems = addingItems;
    }
  }

  onMount(async () => {
    wakeLock = await navigator?.wakeLock?.request('screen');
  });

  onDestroy(async () => {
    wakeLock?.release();
  });
</script>

{#if recipe}
  <div class="recipe">
    <h2>{recipe.title}</h2>
    <p>{recipe.summary}</p>
    <div class="section">
      <h4>Ingredients</h4>
      <ul>
        {#each ingredientEntries as { line, amount }}
          <li>
            {line}
            {#if addedItems.has(line)}
              <span class="add-link added">✓ added</span>
            {:else}
              <a
                class="add-link"
                class:adding={addingItems.has(line)}
                href="javascript:;"
                on:click={() => addToGroceryList(line, amount)}
              >add</a>
            {/if}
          </li>
        {/each}
      </ul>
    </div>
    <div class="section">
      <h4>Steps</h4>
      {#each recipe.steps as step, index}
        <p class="mt-4 mb-4">{index + 1}. {step}</p>
      {/each}
    </div>
  </div>
{/if}

<style>
.section {
  padding: 1em;
}
.add-link {
  margin-left: 0.5em;
  color: #bbb;
  text-decoration: none;
  font-size: 0.9em;
}
.add-link:hover {
  color: #888;
  text-decoration: underline;
}
.add-link.adding {
  pointer-events: none;
  opacity: 0.6;
}
.add-link.added {
  color: #bbb;
}
</style>
