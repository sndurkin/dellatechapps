<script>
  import { onMount } from 'svelte';
  import * as recipeUtils from './recipeUtils';
  import * as utils from '../shared/utils';
  import DeleteButton from '../shared/DeleteButton.svelte';


  export let active;

  let items = [];
  let draggedItem = null;
  let editingItem = null;
  let editingValue = '';
  let touchStartY = 0;
  let touchTarget = null;
  let targetIndex = -1; // Track where the dragged item will be inserted

  // Move dialog state
  let showMoveDialog = false;
  let moveDialogItem = null;
  let moveDialogInput = '';
  let availableItems = [];

  $: if (active) {
    loadItems();
  }

  onMount(async () => {
    await loadItems();
  });

  async function loadItems() {
    const response = await fetch(`/kitchenbuddy/api/manage-all/?username=${encodeURIComponent(recipeUtils.getUsername())}`);
    const data = await response.json();
    items = data.all_items_sorted || [];
  }

  async function updateItems(action, payload) {
    const response = await fetch('/kitchenbuddy/api/manage-all/', {
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
        if (targetIndex > currentIndex) {
          targetIndex--;
        }
        await updateItems('move', {
          item: draggedItem,
          new_position: targetIndex,
        });
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
        if (targetIndex > currentIndex) {
          targetIndex--;
        }
        await updateItems('move', {
          item: touchTarget,
          new_position: targetIndex,
        });
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

    function openMoveDialog(item) {
    moveDialogItem = item;
    moveDialogInput = '';
    availableItems = items.filter(i => i !== item); // Exclude the current item
    showMoveDialog = true;
  }

  function closeMoveDialog() {
    showMoveDialog = false;
    moveDialogItem = null;
    moveDialogInput = '';
    availableItems = [];
  }

  async function handleMoveToPosition() {
    if (!moveDialogItem || !moveDialogInput) return;

    // Find the selected item in the available items
    const selectedItem = availableItems.find(item => item === moveDialogInput);
    if (selectedItem) {
      let targetIndex = items.indexOf(selectedItem);
      if (targetIndex !== -1) {
        if (targetIndex > items.indexOf(moveDialogItem)) {
          targetIndex--;
        }
        await updateItems('move', {
          item: moveDialogItem,
          new_position: targetIndex,
        });
      }
    }
    closeMoveDialog();
  }

  function handleMoveDialogKeydown(e) {
    if (e.key === 'Enter') {
      handleMoveToPosition();
    } else if (e.key === 'Escape') {
      closeMoveDialog();
    }
  }
</script>

<div class="container mt-4">
  <h2>All Grocery Items</h2>
  <p class="text-muted">Drag and drop items to reorder. Click to edit. Use move icon to jump to position. Use delete button to remove.</p>

  <div class="list-container">
    <ul class="list-group">
      {#each items as item, index}
        <li class="list-group-item d-flex align-items-center gap-2">
          <div
            role="button"
            aria-label="Drag to reorder"
            tabindex="0"
            class="drag-handle"
            draggable={true}
            on:dragstart={() => handleDragStart(item)}
            on:dragover={(e) => handleDragOver(e, item)}
            on:dragend={handleDragEnd}
            on:touchstart={(e) => handleTouchStart(e, item)}
            on:touchmove={(e) => handleTouchMove(e, item)}
            on:touchend={handleTouchEnd}
          >
            ⋮⋮
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
            <button
              type="button"
              class="item-text-btn"
              on:click={() => startEditing(item)}
            >
              {item}
            </button>
            <span class="ms-auto d-flex gap-2">
              <button
                class="btn btn-sm btn-outline-secondary move-btn"
                title="Move to position"
                on:click={() => openMoveDialog(item)}
              >
                ↗️
              </button>
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

<!-- Move Dialog -->
{#if showMoveDialog}
  <div class="modal-backdrop" role="button" tabindex="0" on:click={closeMoveDialog} on:keydown={(e) => e.key === 'Escape' && closeMoveDialog()}></div>
  <div class="move-dialog">
    <div class="dialog-header">
      <h5>Move "{moveDialogItem}" to position</h5>
      <button class="btn-close" on:click={closeMoveDialog}>&times;</button>
    </div>
    <div class="dialog-body">
      <label for="move-input" class="form-label">Type to search and select position:</label>
      <input
        id="move-input"
        type="text"
        class="form-control"
        placeholder="Start typing to find item..."
        list="move-positions"
        bind:value={moveDialogInput}
        on:keydown={handleMoveDialogKeydown}
        autofocus
      />
      <datalist id="move-positions">
        {#each availableItems as item}
          <option value={item}></option>
        {/each}
      </datalist>
      <div class="mt-3">
        <button
          type="button"
          class="btn btn-primary"
          disabled={!moveDialogInput || !availableItems.includes(moveDialogInput)}
          on:click={handleMoveToPosition}
        >
          Move Here
        </button>
        <button
          type="button"
          class="btn btn-secondary ms-2"
          on:click={closeMoveDialog}
        >
          Cancel
        </button>
      </div>
    </div>
  </div>
{/if}

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
    width: 1.5em;
    margin-right: 0.25em;
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

  .item-text-btn {
    background: none;
    border: none;
    text-align: left;
    cursor: pointer;
    flex-grow: 1;
    padding: 0;
    color: inherit;
  }

  .item-text-btn:hover {
    text-decoration: underline;
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



  /* Hide the default touch action hints */
  @media (pointer: coarse) {
    .list-group-item {
      touch-action: none;
    }
  }

  .move-btn {
    padding: 0.2rem 0.4rem;
    font-size: 0.75rem;
    border: none;
    background: transparent;
    color: #6c757d;
  }

  .move-btn:hover {
    background-color: #f8f9fa;
    color: #495057;
  }

  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 1040;
  }

  .move-dialog {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: white;
    border-radius: 0.375rem;
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
    z-index: 1050;
    width: 90%;
    max-width: 500px;
    max-height: 80vh;
    overflow-y: auto;
  }

  .dialog-header {
    padding: 1rem;
    border-bottom: 1px solid #dee2e6;
    display: flex;
    justify-content: between;
    align-items: center;
  }

  .dialog-header h5 {
    margin: 0;
    flex-grow: 1;
  }

  .btn-close {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: #6c757d;
    margin-left: auto;
  }

  .btn-close:hover {
    color: #000;
  }

  .dialog-body {
    padding: 1rem;
  }
</style>
