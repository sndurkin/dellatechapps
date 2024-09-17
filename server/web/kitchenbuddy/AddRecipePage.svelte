<script>
  import { onMount, createEventDispatcher } from 'svelte';

  import * as recipeUtils from './recipeUtils';
  import * as utils from '../utils';


  const dispatch = createEventDispatcher();

  let recipeUrl = 'https://www.preciouscore.com/wprm_print/garlic-butter-chicken-pasta';
  let error = '';
  let state = 'initial';

  async function handleFetchRecipe() {
    state = 'fetching';
    error = '';

    const response = await fetch('/api/recipes/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': utils.getCsrfToken(),
      },
      body: JSON.stringify({
        username: recipeUtils.getUsername(),
        url: recipeUrl,
      }),
    });

    if (!response.ok) {
      try {
        const data = await response.json();
        if (data.error) {
          error = `Failed to fetch recipe: ${data.error}`;
        }
      } catch (e) { /* ignore */ }

      if (!error) {
        error = `Failed to fetch recipe: ${response.status} ${response.statusText} ${await response.text()}`;
      }

      return;
    }

    const data = await response.json();
    dispatch('recipe-fetched', {
      recipe: data.recipe.parsed_recipe,
    });
  }

  onMount(() => {
    if (state === 'create-recipe') {
      document.title = `${username} - Kitchen Buddy`;
    }
  });
</script>

<div class="form-floating mb-3">
  <input
    type="text"
    class="form-control"
    placeholder="e.g. https://www.preciouscore.com/wprm_print/garlic-butter-chicken-pasta"
    id="recipe-url"
    on:keyup={utils.onEnter(handleFetchRecipe)}
    bind:value={recipeUrl}
  />
  <label for="recipe-url" class="form-label">Enter a recipe URL</label>
</div>
<button class="btn btn-primary fetch-btn" type="button" title="Fetch recipe" on:click={handleFetchRecipe}>
  Fetch recipe
  {#if state !== 'fetching'}
    <i class="bi bi-arrow-right"></i>
  {:else}
    <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
  {/if}
</button>
{#if error}
  <div class="alert alert-danger mt-3" role="alert">
    {error}
  </div>
{/if}

<style>
.fetch-btn {
  display: flex;
  align-items: center;
  gap: 1em;
}
</style>
