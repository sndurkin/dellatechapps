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
  let targetIndex = -1; // Track where the dragged item will be inserted

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

  function calculateTargetIndex(e, targetItem) {
    if (!e.currentTarget || !targetItem || items.length === 0) {
      return -1;
    }

    const targetElement = e.currentTarget;
    const rect = targetElement.getBoundingClientRect();
    const baseIndex = items.indexOf(targetItem);

    // If item not found, return -1
    if (baseIndex === -1) {
      return -1;
    }

    // Ensure clientY exists (for mouse events)
    if (typeof e.clientY !== 'number') {
      return baseIndex;
    }

    const relativeY = e.clientY - rect.top;
    const isBottomHalf = relativeY > rect.height / 2;
    return isBottomHalf ? baseIndex + 1 : baseIndex;
  }

  function handleDragOver(e, targetItem) {
    e.preventDefault();
    if (!draggedItem || draggedItem === targetItem) return;

    targetIndex = calculateTargetIndex(e, targetItem);
  }

  async function handleDragEnd() {
    if (draggedItem) {
      const currentIndex = items.indexOf(draggedItem);
      if (targetIndex !== -1 && targetIndex !== currentIndex) {
        await updateItems('move', { item: draggedItem, new_position: targetIndex });
      }
    }
    draggedItem = null;
    targetIndex = -1;
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
      targetIndex = calculateTargetIndex(e, targetItem);
    }
  }

  async function handleTouchEnd() {
    if (touchTarget) {
      const currentIndex = items.indexOf(touchTarget);
      if (targetIndex !== -1 && targetIndex !== currentIndex) {
        await updateItems('move', { item: touchTarget, new_position: targetIndex });
      }
    }
    touchTarget = null;
    targetIndex = -1;
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

  <div class="list-container">
    <ul class="list-group">
      {#each items as item, index}
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
    {#if targetIndex !== -1}
      <div class="drop-indicator" style="top: {targetIndex * 50}px"></div>
    {/if}
  </div>
</div>

<style>
  .list-group-item {
    cursor: default;
    position: relative;
    height: 50px;
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

  .list-container {
    position: relative;
  }

  .drop-indicator {
    position: absolute;
    left: 0;
    width: 100%;
    height: 2px;
    background-color: #007bff;
    display: flex;
    align-items: center;
    pointer-events: none;
  }

  .triangle {
    position: absolute;
    left: 0;
    color: #007bff;
    font-size: 0.8rem;
    transform: translateY(-50%);
  }

  /* Hide the default touch action hints */
  @media (pointer: coarse) {
    .list-group-item {
      touch-action: none;
    }
  }
</style>
