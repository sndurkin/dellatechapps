<script>
  import { createEventDispatcher, onMount, onDestroy } from "svelte";


  const dispatch = createEventDispatcher();

  export let recipe;

  let startOverBtn;
  let startOverTimer;
  let wakeLock;

  function startPress(event) {
    if (event.target?.classList?.contains('start-over-btn')) {
      event.target.classList.add('active');
      startOverTimer = setTimeout(() => {
        dispatch('start-over');
      }, 1000);
    }
  }

  function cancelPress(event) {
    startOverBtn?.classList?.remove('active');
    clearTimeout(startOverTimer);
  }

  onMount(async () => {
    // Mouse events
    document.addEventListener('mousedown', startPress);
    document.addEventListener('mouseup', cancelPress);
    document.addEventListener('mouseleave', cancelPress);

    // Touch events (for mobile long press)
    document.addEventListener('touchstart', startPress);
    document.addEventListener('touchend', cancelPress);
    document.addEventListener('touchcancel', cancelPress);

    wakeLock = await navigator?.wakeLock?.request('screen');
  });

  onDestroy(async () => {
    wakeLock?.release();

    document.removeEventListener('mousedown', startPress);
    document.removeEventListener('mouseup', cancelPress);
    document.removeEventListener('mouseleave', cancelPress);

    document.removeEventListener('touchstart', startPress);
    document.removeEventListener('touchend', cancelPress);
    document.removeEventListener('touchcancel', cancelPress);
  });
</script>

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
<div class="actions">
  <button class="btn btn-light me-auto action-btn start-over-btn" bind:this={startOverBtn}>⟳</button>
</div>

<style>
.actions {
  position: fixed;
  left: 1em;
  bottom: 1em;
  right: 1em;
  display: flex;
  align-items: center;
  gap: 0.5em;
}
.action-btn {
  width: 3em;
  height: 3em;
  line-height: 3em;
  border-radius: 3em;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Consolas', 'Roboto Mono', 'SF Mono', 'Menlo', 'Monaco', 'Courier New', 'Courier', 'monospace';
  font-size: 1.5em;
  opacity: 0.65;
}
.start-over-btn::before {
  content: "";
  position: absolute;
  left: 1.5em;
  width: 0;
  height: 0;
  border-radius: 0;
  background: #2c2cff;
  transform: translate(-50%, 0);
  z-index: -1;
  opacity: 0.65;
  transition: border-radius 1s ease, width 1s ease, height 1s ease;
}
.start-over-btn:global(.active)::before {
  width: 3em;
  height: 3em;
  border-radius: 3em;
}

.section {
  padding: 1em;
}
</style>
