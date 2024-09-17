<script>
  import { createEventDispatcher, onMount, onDestroy } from "svelte";


  const dispatch = createEventDispatcher();

  export let recipe;

  let wakeLock;

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
    {#each recipe.ingredients as ingredientSublist}
      <div class="section">
        <h4>Ingredients, {ingredientSublist.location}</h4>
        <ul>
          {#each ingredientSublist.items as ingredient}
            <li>{ingredient}</li>
          {/each}
        </ul>
      </div>
    {/each}
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
</style>
