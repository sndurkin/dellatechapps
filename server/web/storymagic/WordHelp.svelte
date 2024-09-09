<script>
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';


  export let word;
  export let wordMapping;

  const dispatch = createEventDispatcher();

  onMount(() => {
    document.addEventListener('keydown', handleKeyDown);
  });

  onDestroy(() => {
    document.removeEventListener('keydown', handleKeyDown);
  });

  function handleKeyDown(event) {
    if (event.key === 'Escape' || event.key === 'Enter' || event.key === ' ') {
      close();
    }
  }

  function close() {
    dispatch('close');
  }
</script>

<div class="modal-wrapper" on:click={close}>
  <div class="modal-box" on:click|stopPropagation>
    <div class="close-button" on:click={close}>&times;</div>
    <h3 class="text-center word">
      {word}
    </h3>
    <h4 class="mt-4 text-center pronunciation">
      {wordMapping.map(mapping => mapping.grapheme).join(' • ')}
    </h4>
  </div>
</div>

<style>
.modal-wrapper {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(255, 255, 255, 0.5); /* Half opaque white background */
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000; /* Ensure it appears on top */
}

.modal-box {
  font-family: 'Georgia', 'Times New Roman', 'Palatino', 'Serif';
  background-color: white;
  padding: 2em;
  border-radius: 8px;
  box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1); /* Box-shadow */
  max-width: 90%;
  max-height: 90%;
  overflow-y: auto;
}

.close-button {
  position: absolute;
  top: 15px;
  right: 20px;
  font-size: 1.5rem;
  cursor: pointer;
}
</style>
