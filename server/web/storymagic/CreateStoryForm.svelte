<script>
  import { onMount, createEventDispatcher } from "svelte";
  const dispatch = createEventDispatcher();

  export let creating = false;

  let topic;
  let grade;
  let sentenceCount;

  onMount(() => {
    grade = localStorage.getItem("grade") || "Preschool";
    sentenceCount = localStorage.getItem("sentenceCount");
  });

  function createStory() {
    localStorage.setItem("grade", grade);
    localStorage.setItem("sentenceCount", sentenceCount);

    dispatch("create-story", {
      topic,
      grade,
      sentenceCount,
    });
  }
</script>

<h3 class="mb-3">Create a story</h3>
<div class="mb-3">
  <label for="topic" class="form-label">Topic</label>
  <textarea bind:value={topic} class="form-control" id="topic" rows="3" placeholder="finding a baby dragon" aria-label="Enter a topic"></textarea>
</div>
<div class="mb-3">
  <label for="grade" class="form-label">Grade level</label>
  <select bind:value={grade} id="grade" class="form-select" aria-label="Select grade level">
    <option value="Preschool">Preschool</option>
    <option value="Kindergarten">Kindergarten</option>
    <option value="1st Grade">1st Grade</option>
    <option value="2nd Grade">2nd Grade</option>
    <option value="3rd Grade">3rd Grade</option>
    <option value="4th Grade">4th Grade</option>
    <option value="5th Grade">5th Grade</option>
    <option value="6th Grade">6th Grade</option>
  </select>
</div>
<div class="mb-3">
  <label for="sentence-count" class="form-label">Max sentence count</label>
  <input bind:value={sentenceCount} type="number" id="sentence-count" class="form-control" placeholder="4" aria-label="Enter max sentence count">
</div>
<div>
  <button on:click={createStory} class="btn btn-primary create-btn" type="button" title="Create book">
    Create story
    {#if !creating}
      <i class="bi bi-arrow-right"></i>
    {:else}
      <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
    {/if}
  </button>
</div>

<style>
  .create-btn {
    display: flex;
    align-items: center;
    gap: 0.75em;
  }
</style>
