<script>
  import { onMount, afterUpdate } from 'svelte';

  import * as recipeUtils from './recipeUtils';

  import DeleteButton from '../DeleteButton.svelte';
  import SpeechRecognitionButton from '../SpeechRecognitionButton.svelte';
  import * as utils from '../utils';

  export let active;

  let items = [];
  let state = 'initial';
  let newItemInput;
  let isShoppingMode = false;
  let checkedItems = {};

  $: if (active) {
    loadItems();
  }

  onMount(async () => {
    await loadItems();

    if (newItemInput) {
      newItemInput.focus();
    }
  });

  afterUpdate(async () => {
    if (newItemInput) {
      newItemInput.focus();
    }
  });

  async function loadItems() {
    const response = await fetch(`/api/list/?username=${encodeURIComponent(recipeUtils.getUsername())}`);
    const data = await response.json();
    items = data.items;
  }

  async function addItemFromInput() {
    if (!newItemInput.value.trim()) {
      newItemInput.value = '';
      return;
    }

    state = 'adding';
    let newItems = [...items, newItemInput.value];
    await updateList(newItems);
    state = 'initial';
    newItemInput.value = '';
  }

  async function addItems(itemsToAdd) {
    state = 'adding';
    let newItems = [...items, ...itemsToAdd];
    await updateList(newItems);
    state = 'initial';
    newItemInput.value = '';
  }

  async function handleDeleteList() {
    await updateList([]);
  }

  async function handleDeleteItem(item) {
    const newItems = items.filter(i => i !== item);
    await updateList(newItems);
  }

  function toggleShoppingMode() {
    isShoppingMode = !isShoppingMode;
    if (!isShoppingMode) {
      // When exiting shopping mode, delete all checked items
      const uncheckedItems = items.filter(item => !(item in checkedItems));
      updateList(uncheckedItems);
      checkedItems = {};
    }
  }

  function toggleItemChecked(item) {
    if (checkedItems[item]) {
      delete checkedItems[item];
    } else {
      checkedItems[item] = true;
    }
    checkedItems = { ...checkedItems };
  }

  async function handleSpeech(event) {
    const SEPARATOR_STR = 'enter';
    const { transcript } = event.detail;
    console.log(`Speech: "${transcript}"`);

    let parts = transcript.split(' ').filter(part => part.trim());
    if (parts.length === 1 && parts[0].toLowerCase() === SEPARATOR_STR) {
      await addItemFromInput();
      return;
    }

    const itemsToAdd = [];
    while (parts.length > 0) {
      console.log(`Parts: ${parts}`);
      const separatorIdx = parts.findIndex(part => part.toLowerCase() === SEPARATOR_STR);
      if (separatorIdx >= 0) {
        itemsToAdd.push(parts.slice(0, separatorIdx).join(' '));
        parts = parts.slice(separatorIdx + 1);
      }
      else {
        newItemInput.value = newItemInput.value.trim() + ' ' + parts.join(' ');
        parts = [];
      }
    }

    if (itemsToAdd.length > 0) {
      await addItems(itemsToAdd);
    }
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
      const data = await response.json();
      items = data.items;
    }
  }
</script>

<ul class="list-group">
  <li class="list-group-item d-flex align-items-center justify-content-between">
    <button class="btn btn-primary btn-sm" on:click={toggleShoppingMode}>
      {isShoppingMode ? 'Done shopping' : 'Go shopping'}
    </button>
    {#if !isShoppingMode}
      <DeleteButton
        text="Delete all"
        on:delete={handleDeleteList}
      />
    {/if}
  </li>
  {#each items as item}
    <li class="list-group-item d-flex align-items-center gap-2">
      <span class:checked={isShoppingMode && checkedItems[item]}>
        {item}
      </span>
      {#if !isShoppingMode}
        <span class="ms-auto">
          <DeleteButton
            iconOnly={true}
            on:delete={() => handleDeleteItem(item)} />
        </span>
      {:else}
        <span class="ms-auto">
          <input
            type="checkbox"
            class="form-check-input"
            checked={checkedItems[item]}
            on:change={() => toggleItemChecked(item)}
          />
        </span>
      {/if}
    </li>
  {/each}
  {#if state === 'adding'}
    <li class="list-group-item d-flex align-items-center gap-2">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </li>
  {/if}
  {#if !isShoppingMode}
    <li class="list-group-item d-flex align-items-center gap-2">
      <input
        bind:this={newItemInput}
        type="text"
        class="form-control"
        placeholder="Enter an item"
        on:keyup={utils.onEnter(addItemFromInput)}
      />
      <button class="btn btn-primary" on:click={addItemFromInput}>Add</button>
    </li>
  {/if}
</ul>
<SpeechRecognitionButton on:speech={handleSpeech} />

<style>
.spinner-border {
  width: 1em;
  height: 1em;
}

.list-group-item .checked {
  position: relative;
  color: #999;
  text-decoration: line-through;
}
</style>
