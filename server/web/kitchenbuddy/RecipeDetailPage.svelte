<script>
  import { onMount, onDestroy } from "svelte";

  import * as recipeUtils from './recipeUtils';
  import * as utils from '../shared/utils';


  export let recipe;
  export let recipeId = null;

  let wakeLock;
  let addedItems = new Set();
  let addingItems = new Set();
  let showEditDialog = false;
  let editInstructions = '';
  let editError = '';
  let editLoading = false;

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

  function openEditDialog() {
    editInstructions = '';
    editError = '';
    editLoading = false;
    showEditDialog = true;
  }

  function closeEditDialog() {
    if (editLoading) {
      return;
    }
    showEditDialog = false;
    editError = '';
    editInstructions = '';
  }

  async function submitEdit() {
    const instructions = editInstructions.trim();
    if (!instructions || editLoading) {
      return;
    }
    if (!recipeId) {
      editError = 'This recipe cannot be edited because it has no id.';
      return;
    }

    editLoading = true;
    editError = '';

    try {
      const response = await fetch('/kitchenbuddy/api/recipes/', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': utils.getCsrfToken(),
        },
        body: JSON.stringify({
          username: recipeUtils.getUsername(),
          id: recipeId,
          instructions,
          recipe,
        }),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        editError = data.error || `Failed to update recipe: ${response.status} ${response.statusText}`;
        return;
      }

      recipe = data.recipe.parsed_recipe;
      showEditDialog = false;
      editInstructions = '';
      editError = '';
    } catch (e) {
      editError = e.message || 'Failed to update recipe';
    } finally {
      editLoading = false;
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
  <button class="btn btn-primary edit-recipe-btn" type="button" title="Edit" on:click={openEditDialog}>
    <i class="bi bi-pencil"></i>
  </button>
{/if}

{#if showEditDialog}
  <div
    class="modal-backdrop"
    role="button"
    tabindex="0"
    on:click={closeEditDialog}
    on:keydown={(e) => e.key === 'Escape' && closeEditDialog()}
  ></div>
  <div class="edit-dialog">
    <div class="dialog-header">
      <h5>Edit recipe</h5>
      <button class="btn-close" type="button" disabled={editLoading} on:click={closeEditDialog}>&times;</button>
    </div>
    <div class="dialog-body">
      <label for="edit-instructions" class="form-label">Instructions for the recipe update</label>
      <textarea
        id="edit-instructions"
        class="form-control"
        rows="6"
        placeholder="e.g. Cut the servings in half and replace chicken with tofu"
        disabled={editLoading}
        bind:value={editInstructions}
      ></textarea>
      {#if editLoading}
        <p class="mt-3 mb-0">Updating recipe...</p>
      {:else}
        {#if editError}
          <div class="alert alert-danger mt-3 mb-0" role="alert">
            {editError}
          </div>
        {/if}
        <div class="mt-3">
          <button
            type="button"
            class="btn btn-primary"
            disabled={!editInstructions.trim()}
            on:click={submitEdit}
          >
            Update recipe
          </button>
          <button
            type="button"
            class="btn btn-secondary ms-2"
            on:click={closeEditDialog}
          >
            Cancel
          </button>
        </div>
      {/if}
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
.edit-recipe-btn {
  position: fixed;
  bottom: 1em;
  right: 1em;
  width: 2.5em;
  height: 2.5em;
  line-height: 2.5em;
  border-radius: 2.5em;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25em;
}
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1040;
}
.edit-dialog {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  border-radius: 0.375rem;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
  z-index: 1050;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
}
.dialog-header {
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
  display: flex;
  align-items: center;
}
.dialog-header h5 {
  margin: 0;
  flex-grow: 1;
}
.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6c757d;
  margin-left: auto;
}
.btn-close:hover {
  color: #000;
}
.btn-close:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.dialog-body {
  padding: 1rem;
}
</style>
