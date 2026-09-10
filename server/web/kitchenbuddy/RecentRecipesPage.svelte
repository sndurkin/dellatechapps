<script>
  import { onMount, createEventDispatcher } from 'svelte';

  import * as recipeUtils from './recipeUtils';
  import * as utils from '../shared/utils';
  import DeleteButton from '../shared/DeleteButton.svelte';


  const dispatch = createEventDispatcher();

  let recipes = [];

  function handleRecipeClick(recipe) {
    dispatch('recipe-selected', { recipe: recipe.parsed_recipe, recipeId: recipe.id });
  }

  function handleAddRecipe() {
    dispatch('new-recipe');
  }

  async function handleDeleteRecipe(recipe) {
    const response = await fetch('/kitchenbuddy/api/recipes/', {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': utils.getCsrfToken(),
      },
      body: JSON.stringify({
        username: recipeUtils.getUsername(),
        id: recipe.id,
      }),
    });

    if (response.ok) {
      const data = await response.json();
      recipes = mapRecipes(data.recipes);
    }
  }

  function mapRecipes(apiRecipes) {
    return (apiRecipes || []).map(r => ({
      id: r.id,
      title: r.title || r.parsed_recipe?.title,
      parsed_recipe: r.parsed_recipe,
    }));
  }

  onMount(async () => {
    const response = await fetch(`/kitchenbuddy/api/recipes/?username=${encodeURIComponent(recipeUtils.getUsername())}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    const data = await response.json();
    recipes = mapRecipes(data.recipes);
  });
</script>

<div class="mt-4">
  <h5>Recent recipes</h5>
  <ul class="list-group mt-4">
    {#each recipes as recipe}
      <li class="list-group-item d-flex align-items-center gap-2">
        <a href="javascript:;" class="recipe-title flex-grow-1" on:click={() => handleRecipeClick(recipe)}>
          {recipe.title}
        </a>
        <DeleteButton
          iconOnly={true}
          on:delete={() => handleDeleteRecipe(recipe)} />
      </li>
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
.recipe-title {
  color: inherit;
  text-decoration: none;
}
</style>
