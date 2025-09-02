<script>
  import { onMount, afterUpdate } from 'svelte';

  import * as recipeUtils from './recipeUtils';

  import DeleteButton from '../shared/DeleteButton.svelte';
  import SpeechRecognitionButton from '../shared/SpeechRecognitionButton.svelte';
  import * as utils from '../shared/utils';

  export let active;

  let items = [];
  let itemCounts = {};
  let state = 'initial';
  let newItemInput;
  let isShoppingMode = false;
  let checkedItems = {};
  let newlyAddedItems = new Set();
  let itemRefs = {};

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
    const response = await fetch(`/kitchenbuddy/api/list/?username=${encodeURIComponent(recipeUtils.getUsername())}`);
    const data = await response.json();
    items = data.items;
    itemCounts = data.item_counts;
  }

  async function addItemFromInput() {
    if (!newItemInput.value.trim()) {
      newItemInput.value = '';
      return;
    }

    const newItemName = newItemInput.value.trim();

    state = 'adding';
    await addItems([newItemName]);
    state = 'initial';
    newItemInput.value = '';
  }

  async function addItemsFromSpeech(itemsToAdd) {
    state = 'adding';
    await addItems(itemsToAdd);
    state = 'initial';
    newItemInput.value = '';
  }

  async function removeItems(itemsToRemove) {
    const response = await fetch(`/kitchenbuddy/api/list/remove/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': utils.getCsrfToken(),
      },
      body: JSON.stringify({
        items: itemsToRemove,
        username: recipeUtils.getUsername(),
      }),
    });

    if (response.ok) {
      const data = await response.json();
      items = data.items;
      itemCounts = data.item_counts;
    }
  }

  async function handleDeleteList() {
    await removeItems(items);
  }

  async function handleDeleteItem(item) {
    await removeItems([item]);
  }

  async function updateItemCount(item, delta) {
    const newCount = Math.max(1, (itemCounts[item] || 1) + delta);
    const response = await fetch(`/kitchenbuddy/api/list/update-count/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': utils.getCsrfToken(),
      },
      body: JSON.stringify({
        item: item,
        count: newCount,
        username: recipeUtils.getUsername(),
      }),
    });

    if (response.ok) {
      const data = await response.json();
      items = data.items;
      itemCounts = data.item_counts;
    }
  }

  async function toggleShoppingMode() {
    isShoppingMode = !isShoppingMode;
    if (!isShoppingMode) {
      // When exiting shopping mode, delete all checked items
      await removeItems(Object.keys(checkedItems));
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
      await addItemsFromSpeech(itemsToAdd);
    }
  }

  function scrollToAndFlashItem(itemName) {
    const element = itemRefs[itemName];
    if (element) {
      // Scroll to the item with smooth behavior
      element.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
        inline: 'nearest'
      });

      // Add flash class and remove it after animation
      element.classList.add('flash-item');
      setTimeout(() => {
        element.classList.remove('flash-item');
        newlyAddedItems.delete(itemName);
      }, 1500);
    }
  }

  async function addItems(newItems) {
    const previousItems = [...items];

    const response = await fetch(`/kitchenbuddy/api/list/add/`, {
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
      itemCounts = data.item_counts;

      // Find newly added items and mark them for flashing
      const actuallyNewItems = items.filter(item => !previousItems.includes(item));
      actuallyNewItems.forEach(item => newlyAddedItems.add(item));

      // After DOM update, scroll to and flash the first new item
      if (actuallyNewItems.length > 0) {
        setTimeout(() => {
          scrollToAndFlashItem(actuallyNewItems[0]);
        }, 100);
      }
    }
  }
</script>

<ul class="list-group item-list">
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
    <li class="list-group-item d-flex align-items-center gap-2" bind:this={itemRefs[item]}>
      <span class:checked={isShoppingMode && checkedItems[item]}>
        {item}{isShoppingMode && itemCounts[item] > 1 ? ` (${itemCounts[item]})` : ''}
      </span>
      {#if !isShoppingMode}
        <div class="d-flex align-items-center gap-1 ms-auto">
          <div class="btn-group btn-group-sm count-group">
            <button class="btn btn-outline-secondary" on:click={() => updateItemCount(item, -1)}>-</button>
            <span class="px-2">{itemCounts[item] || 1}</span>
            <button class="btn btn-outline-secondary" on:click={() => updateItemCount(item, 1)}>+</button>
          </div>
          <DeleteButton
            iconOnly={true}
            on:delete={() => handleDeleteItem(item)} />
        </div>
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
</ul>
{#if !isShoppingMode}
  <div class="container position-fixed bottom-0 start-0 end-0 mb-2">
    <div class="col-lg-8 col-md-10 col-sm-12 m-auto">
      <div class="d-flex align-items-center gap-2">
        <div class="input-container">
          <input
            bind:this={newItemInput}
            type="text"
            class="form-control"
            placeholder="Enter an item"
            on:keyup={utils.onEnter(addItemFromInput)}
          />
          <SpeechRecognitionButton on:speech={handleSpeech} className="speech-recognition-button" />
        </div>
        <button class="btn btn-primary" on:click={addItemFromInput}>Add</button>
      </div>
    </div>
  </div>
{/if}

<style>
.spinner-border {
  width: 1em;
  height: 1em;
}

.input-container {
  position: relative;
  flex-grow: 1;
}
:global(.speech-recognition-button) {
  position: absolute;
  right: 1em;
  top: 0;
  bottom: 0;
  margin: 0 !important;
}
.input-container input {
  padding-right: 3rem;
  width: 100%;
}

.item-list {
  margin-bottom: 5em;
}
.item-list .checked {
  position: relative;
  color: #999;
  text-decoration: line-through;
}

.count-group {
  margin-right: 1em;
}

.count-group > .btn {
  width: 2em;
  font-size: 0.875rem;
}

:global(.flash-item) {
  animation: flashHighlight 1.5s ease-out;
}

@keyframes flashHighlight {
  0% {
    background-color: #cde7ff;
    transform: scale(1.02);
  }
  25% {
    background-color: #cde7ff;
  }
  100% {
    background-color: transparent;
    transform: scale(1);
  }
}
</style>
