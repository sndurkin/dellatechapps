<script>
  import { onMount } from 'svelte';
  import * as recipeUtils from './recipeUtils';
  import * as utils from '../utils';
  import DeleteButton from '../DeleteButton.svelte';


  export let active;

  let items = [];
  let draggedItem = null;
  let editingItem = null;
  let editingValue = '';
  let touchStartY = 0;
  let touchTarget = null;

  $: if (active) {
    loadItems();
  }

  onMount(async () => {
    await loadItems();
  });

  async function loadItems() {
    const response = await fetch(`/api/manage-all/?username=${encodeURIComponent(recipeUtils.getUsername())}`);
    const data = await response.json();
    items = data.all_items_sorted || [];
  }

  async function updateItems(action, payload) {
    const response = await fetch('/api/manage-all/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': utils.getCsrfToken(),
      },
      body: JSON.stringify({
        username: recipeUtils.getUsername(),
        action,
        ...payload
      }),
    });

    if (response.ok) {
      const data = await response.json();
      items = data.all_items_sorted;
    }
  }

  function handleDragStart(item) {
    draggedItem = item;
  }

  function handleDragOver(e, targetItem) {
    e.preventDefault();
    if (!draggedItem || draggedItem === targetItem) return;

    const targetIndex = items.indexOf(targetItem);
    const draggedIndex = items.indexOf(draggedItem);

    if (targetIndex !== draggedIndex) {
      updateItems('move', { item: draggedItem, new_position: targetIndex });
    }
  }

  function handleDragEnd() {
    draggedItem = null;
  }

  // Touch events for mobile support
  function handleTouchStart(e, item) {
    touchStartY = e.touches[0].clientY;
    touchTarget = item;
  }

  function handleTouchMove(e, targetItem) {
    if (!touchTarget) return;

    e.preventDefault();
    const touchY = e.touches[0].clientY;
    const deltaY = touchY - touchStartY;

    if (Math.abs(deltaY) > 30) { // Threshold for considering it a drag
      const targetIndex = items.indexOf(targetItem);
      const touchedIndex = items.indexOf(touchTarget);

      if (targetIndex !== touchedIndex) {
        updateItems('move', { item: touchTarget, new_position: targetIndex });
        touchStartY = touchY;
      }
    }
  }

  function handleTouchEnd() {
    touchTarget = null;
  }

  function startEditing(item) {
    editingItem = item;
    editingValue = item;
  }

  async function handleEditSave() {
    if (!editingValue.trim() || editingValue === editingItem) {
      editingItem = null;
      return;
    }

    // Remove old item and add new one
    await updateItems('remove', { items: [editingItem] });
    const newItems = [...items];
    const index = newItems.indexOf(editingItem);
    newItems[index] = editingValue;
    await updateItems('replace', { items: newItems });

    editingItem = null;
  }

  async function handleDelete(item) {
    await updateItems('remove', { items: [item] });
  }
</script>

<div class="container mt-4">
  <h2>All Grocery Items</h2>
  <p class="text-muted">Drag and drop items to reorder. Click to edit. Use delete button to remove.</p>

  <ul class="list-group">
    {#each items as item}
      <li
        class="list-group-item d-flex align-items-center gap-2"
        draggable={true}
        on:dragstart={() => handleDragStart(item)}
        on:dragover={(e) => handleDragOver(e, item)}
        on:dragend={handleDragEnd}
        on:touchstart={(e) => handleTouchStart(e, item)}
        on:touchmove={(e) => handleTouchMove(e, item)}
        on:touchend={handleTouchEnd}
      >
        <div class="drag-handle" aria-label="Drag to reorder">
          ⋮
        </div>
        {#if editingItem === item}
          <input
            type="text"
            class="form-control"
            bind:value={editingValue}
            on:blur={handleEditSave}
            on:keyup={utils.onEnter(handleEditSave)}
            autofocus
          />
        {:else}
          <span on:click={() => startEditing(item)} style="cursor: pointer; flex-grow: 1;">
            {item}
          </span>
          <span class="ms-auto">
            <DeleteButton
              iconOnly={true}
              on:delete={() => handleDelete(item)}
            />
          </span>
        {/if}
      </li>
    {/each}
  </ul>
</div>

<style>
  .list-group-item {
    cursor: default;
  }

  .drag-handle {
    cursor: move; /* Fallback */
    cursor: -webkit-grab;
    cursor: grab;
    color: #aaa;
    margin-right: 8px;
    padding: 5px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    line-height: 1;
  }

  .drag-handle:active {
    cursor: -webkit-grabbing;
    cursor: grabbing;
  }

  li[draggable="true"] {
    cursor: move; /* Fallback */
    cursor: -webkit-grab;
    cursor: grab;
  }

  li[draggable="true"]:active {
    cursor: -webkit-grabbing;
    cursor: grabbing;
  }

  /* Hide the default touch action hints */
  @media (pointer: coarse) {
    .list-group-item {
      touch-action: none;
    }
  }
</style>
