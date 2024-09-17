<script>
  import { onMount, afterUpdate } from 'svelte';

  import * as recipeUtils from './recipeUtils';

  import DeleteButton from '../DeleteButton.svelte';
  import * as utils from '../utils';


  let items = [];
  let state = 'initial';
  let newItemInput;
  let newItem = '';

  export async function deleteList() {
    await updateList([]);
  }

  onMount(async () => {
    const response = await fetch(`/api/list/?username=${encodeURIComponent(recipeUtils.getUsername())}`);
    const data = await response.json();
    items = data.items;

    if (newItemInput) {
      newItemInput.focus();
    }
  });

  afterUpdate(() => {
    if (newItemInput) {
      newItemInput.focus();
    }
  });

  async function handleAddItem() {
    if (newItem) {
      state = 'adding';
      let newItems = [...items, newItem];
      await updateList(newItems);
      state = 'initial';
      newItem = '';
    }
  }

  async function handleDeleteItem(item) {
    const newItems = items.filter(i => i !== item);
    await updateList(newItems);
  }

  async function updateList(newItems) {
    const response = await fetch(`/api/list/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': utils.getCsrfToken(),
      },
      body: JSON.stringify({
        items: newItems,
        username: recipeUtils.getUsername(),
      }),
    });

    if (response.ok) {
      items = newItems;
    }
  }
</script>

<ul class="list-group">
  {#each items as item}
    <li class="list-group-item d-flex align-items-center gap-2">
      {item}
      <span class="ms-auto">
        <DeleteButton
          iconOnly={true}
          on:delete={() => handleDeleteItem(item)} />
      </span>
    </li>
  {/each}
  <li class="list-group-item d-flex align-items-center gap-2">
    {#if state === 'initial'}
      <input
        bind:this={newItemInput}
        type="text"
        class="form-control"
        placeholder="Enter an item"
        bind:value={newItem}
        on:keyup={utils.onEnter(handleAddItem)}
      />
      <button class="btn btn-primary" on:click={handleAddItem}>Add</button>
    {:else if state === 'adding'}
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    {/if}
  </li>
</ul>

<style>
.spinner-border {
  width: 1em;
  height: 1em;
}
</style>
