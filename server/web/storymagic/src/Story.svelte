<script>
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';

  export let story;

  const dispatch = createEventDispatcher();

  let timer;
  let storyEl;

  function massageWord(word) {
    return word.replace(/[^a-zA-Z]/g, '');
  }

  function handleFocus(event) {
    Array.from(document.querySelectorAll('.focus')).forEach(word => {
      word.classList.remove('focus');
    });
    event.target.classList.add('focus');
  }

  function handlePrevious() {
    const currentWordEl = document.querySelector('.word.focus');
    if (currentWordEl?.previousElementSibling) {
      currentWordEl.previousElementSibling.focus();
    }
    else {
      currentWordEl?.parentElement?.previousElementSibling?.querySelector('.word')?.focus();
    }
  }

  function handleOpenWordHelp() {
    const currentWordEl = document.querySelector('.word.focus');
    dispatch('word-help', {
      word: massageWord(currentWordEl.textContent),
    });
  }

  function handleNext() {
    const currentWordEl = document.querySelector('.word.focus');
    if (currentWordEl?.nextElementSibling) {
      currentWordEl.nextElementSibling.focus();
    }
    else {
      currentWordEl?.parentElement?.nextElementSibling?.querySelector('.word')?.focus();
    }
  }

  function startPress(event) {
    if (event.target.classList.contains('word')) {
      timer = setTimeout(() => {
        dispatch('word-help', {
          word: massageWord(event.target.textContent),
        });
      }, 500);
    }
  }

  function cancelPress(event) {
    if (event.target.classList.contains('word')) {
      clearTimeout(timer);
    }
  }

  function handleKeyDown(event) {
    switch (event.key) {
      case 'ArrowLeft':
        handlePrevious();
        break;
      case 'ArrowRight':
        handleNext();
        break;
      case ' ':
        event.preventDefault();
        handleOpenWordHelp();
        break;
    }
  }

  function handleStartOver() {
    dispatch('start-over');
  }

  onMount(() => {
    document.querySelector('.word')?.focus();

    document.addEventListener('keydown', handleKeyDown);

    // Mouse events
    document.addEventListener('mousedown', startPress);
    document.addEventListener('mouseup', cancelPress);
    document.addEventListener('mouseleave', cancelPress);

    // Touch events (for mobile long press)
    document.addEventListener('touchstart', startPress);
    document.addEventListener('touchend', cancelPress);
    document.addEventListener('touchcancel', cancelPress);
  });

  onDestroy(() => {
    document.removeEventListener('keydown', handleKeyDown);

    document.removeEventListener('mousedown', startPress);
    document.removeEventListener('mouseup', cancelPress);
    document.removeEventListener('mouseleave', cancelPress);

    storyEl.removeEventListener('touchstart', startPress);
    storyEl.removeEventListener('touchend', cancelPress);
    storyEl.removeEventListener('touchcancel', cancelPress);
  });
</script>

<div class="story" bind:this={storyEl}>
  <h3 class="mb-3">{story.title}</h3>
  {#each story.sentences as sentence}
    <p class="sentence fs-3 mt-4">
      {#each sentence.split(' ') as word}
        <span class="word" tabindex="0" on:focus={handleFocus}>{word}</span>
      {/each}
    </p>
  {/each}
</div>
<div class="actions">
  <button class="btn btn-light me-auto action-btn" on:click={handleStartOver}>⟳</button>
  <button class="btn btn-light action-btn" on:click={handleOpenWordHelp}>?</button>
  <button class="btn btn-light action-btn" on:click={handlePrevious}>&lt;</button>
  <button class="btn btn-light action-btn" on:click={handleNext}>&gt;</button>
</div>

<style>
.story {
  font-family: 'Georgia', 'Times New Roman', 'Palatino', 'Serif';
}
.sentence {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5em;
}
.word {
  border-bottom: 3px solid transparent;
  cursor: pointer;
  padding: 0 0.25em 0.2em 0.25em;
  user-select: none;
}
.word:global(.focus) {
  border-bottom-color: #000;
  outline: none;
}

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
</style>
