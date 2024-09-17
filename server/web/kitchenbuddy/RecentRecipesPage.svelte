<script>
  import { onMount, createEventDispatcher } from 'svelte';

  import * as recipeUtils from './recipeUtils';


  const dispatch = createEventDispatcher();

  let recipes = [];

  function handleRecipeClick(recipe) {
    dispatch('recipe-selected', { recipe });
  }

  function handleAddRecipe() {
    dispatch('new-recipe');
  }

  onMount(async () => {
    const response = await fetch(`/api/recipes/?username=${encodeURIComponent(recipeUtils.getUsername())}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    const data = await response.json();
    recipes = data.recipes?.map(r => r.parsed_recipe) || [];
  });
</script>

<div class="mt-4">
  <h5>Recent recipes</h5>
  <ul class="list-group list-group-flush mt-4">
    {#each recipes as recipe}
      <a href="javascript:;" class="list-group-item list-group-item-action" on:click={() => handleRecipeClick(recipe)}>
        {recipe.title}
      </a>
    {/each}
  </ul>
</div>
<button class="btn btn-primary add-recipe-btn" type="button" title="Add recipe" on:click={handleAddRecipe}>
  <i class="bi bi-plus"></i>
</button>

<style>
.add-recipe-btn {
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
  font-family: 'Consolas', 'Roboto Mono', 'SF Mono', 'Menlo', 'Monaco', 'Courier New', 'Courier', 'monospace';
  font-size: 1.5em;
}
</style>
