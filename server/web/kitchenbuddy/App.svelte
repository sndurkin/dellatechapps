<script>
  import Frame from '../Frame.svelte';
  import * as utils from '../utils';

  // let recipeUrl = '';
  let recipeUrl = 'https://www.preciouscore.com/wprm_print/garlic-butter-chicken-pasta';
  let state = 'initial';

  function handleFetchRecipe() {
    state = 'fetching';
    console.log('fetching recipe');
  }
</script>

<Frame>
  <div class="col-md-6">
    <label for="recipe-url" class="form-label">Recipe URL</label>
    <div class="input-group mb-3">
      <input
        id="recipe-url"
        type="text"
        bind:value={recipeUrl}
        class="form-control"
        placeholder="e.g. https://www.preciouscore.com/wprm_print/garlic-butter-chicken-pasta"
        on:keyup={utils.onEnter(handleFetchRecipe)}
      >
    </div>
    <button class="btn btn-primary fetch-btn" type="button" title="Fetch recipe" on:click={handleFetchRecipe}>
      Fetch recipe
      {#if state !== 'fetching'}
        <i class="bi bi-arrow-right"></i>
      {:else}
        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
      {/if}
    </button>
  </div>
</Frame>

<style>
.fetch-btn {
  display: flex;
  align-items: center;
  gap: 0.75em;
}
</style>
