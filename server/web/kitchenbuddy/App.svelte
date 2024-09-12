<script>
  import Frame from '../Frame.svelte';
  import * as utils from '../utils';

  // let recipeUrl = '';
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
      body: JSON.stringify({ url: recipeUrl }),
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

      state = 'initial';
      return;
    }

    const data = await response.json();
    console.log(data);
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
    {#if error}
      <div class="alert alert-danger mt-3" role="alert">
        {error}
      </div>
    {/if}
  </div>
</Frame>

<style>
.fetch-btn {
  display: flex;
  align-items: center;
  gap: 0.75em;
}
</style>
