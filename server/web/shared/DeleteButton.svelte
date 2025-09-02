<script>
  import { createEventDispatcher } from 'svelte';
  import { fade } from 'svelte/transition';

  export let iconOnly = false;
  export let text = 'Delete';

  const dispatch = createEventDispatcher();

  let showConfirmation = false;
  let timer;

  function handleClick() {
    showConfirmation = true;
    clearTimeout(timer);
    timer = setTimeout(() => {
      showConfirmation = false;
    }, 3000);
  }

  function handleConfirm() {
    dispatch('delete');
    showConfirmation = false;
  }

  function handleCancel() {
    showConfirmation = false;
  }
</script>

{#if showConfirmation}
  <div transition:fade="{{ duration: 200 }}" class="d-inline-block">
    <span class="me-2">Really delete?</span>
    <button on:click={handleConfirm} class="btn btn-danger btn-sm me-1">Yes</button>
    <button on:click={handleCancel} class="btn btn-secondary btn-sm">No</button>
  </div>
{:else}
  <button on:click={handleClick} class="btn btn-outline-danger btn-sm">
    {#if iconOnly}
      <i class="bi bi-trash"></i>
    {:else}
      <i class="bi bi-trash"></i> {text}
    {/if}
  </button>
{/if}
