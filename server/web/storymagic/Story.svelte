<script>
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';

  export let story;

  const dispatch = createEventDispatcher();

  let wordHelpTimer;
  let startOverTimer;
  let startOverBtn;
  let wakeLock;

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
      currentWordEl?.parentElement?.previousElementSibling?.querySelector('.word:last-child')?.focus();
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
    if (event.target?.classList?.contains('word')) {
      wordHelpTimer = setTimeout(() => {
        dispatch('word-help', {
          word: massageWord(event.target.textContent),
        });
      }, 500);
    }
    else if (event.target?.classList?.contains('action-btn')) {
      event.target.classList.add('active');
      startOverTimer = setTimeout(() => {
        dispatch('start-over');
      }, 1000);
    }
  }

  function cancelPress(event) {
    clearTimeout(wordHelpTimer);
    startOverBtn?.classList?.remove('active');
    clearTimeout(startOverTimer);
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

  onMount(async () => {
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

    wakeLock = await navigator.wakeLock.request('screen');
  });

  onDestroy(async () => {
    wakeLock.release();

    document.removeEventListener('keydown', handleKeyDown);

    document.removeEventListener('mousedown', startPress);
    document.removeEventListener('mouseup', cancelPress);
    document.removeEventListener('mouseleave', cancelPress);

    document.removeEventListener('touchstart', startPress);
    document.removeEventListener('touchend', cancelPress);
    document.removeEventListener('touchcancel', cancelPress);
  });
</script>

<div class="story">
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
  <button class="btn btn-light me-auto action-btn start-over-btn" bind:this={startOverBtn}>⟳</button>
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
.start-over-btn::before {
  content: "";
  position: absolute;
  left: 1.5em;
  width: 0;
  height: 0;
  border-radius: 0;
  background: #2c2cff;
  transform: translate(-50%, 0);
  z-index: -1;
  opacity: 0.65;
  transition: border-radius 1s ease, width 1s ease, height 1s ease;
}
.start-over-btn:global(.active)::before {
  width: 3em;
  height: 3em;
  border-radius: 3em;
}
</style>
