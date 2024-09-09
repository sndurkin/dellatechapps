<script>
  import CreateStoryForm from './CreateStoryForm.svelte';
  import Story from './Story.svelte';
  import WordHelp from './WordHelp.svelte';

  let state = 'initial';
  let story = null;
  let wordMappings = {};
  let wordToHelpWith = null;

  async function handleCreateStory (event) {
    const { topic, grade, sentenceCount } = event.detail;

    const csrfToken = getCookie('csrftoken');

    state = 'creating';
    const resp = await fetch('/storymagic/api/stories/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
      body: JSON.stringify({
        topic,
        grade,
        sentence_count: sentenceCount,
      }),
    });

    const data = await resp.json();
    story = data.story;
    wordMappings = data.word_mappings || {};
    state = 'reading-story';
  }

  function handleWordHelpOpen (event) {
    const { word } = event.detail;
    if (word in wordMappings) {
      wordToHelpWith = word;
      state = 'seeking-word-help';
    }
  }

  function handleStartOver () {
    state = 'initial';
    story = null;
    wordMappings = {};
  }

  function handleWordHelpClose () {
    state = 'reading-story';
    wordToHelpWith = null;
  }

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Check if this cookie string begins with the name we want
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
</script>

<main>
  <div class="container">
    <div class="row mt-3 justify-content-center">
      <div class="col-md-6">
        {#if state === 'initial' || state === 'creating'}
          <CreateStoryForm
            creating={state === 'creating'}
            on:create-story={handleCreateStory}
          />
        {:else if state === 'reading-story' || state === 'seeking-word-help'}
          <Story
            story={story}
            on:word-help={handleWordHelpOpen}
            on:start-over={handleStartOver}
          />
          {#if state === 'seeking-word-help'}
            <WordHelp
              word={wordToHelpWith}
              wordMapping={wordMappings[wordToHelpWith]}
              on:close={handleWordHelpClose}
            />
          {/if}
        {/if}
      </div>
    </div>
  </div>
</main>
<footer>by Della Tech LLC</footer>

<style>
footer {
  position: fixed;
  bottom: 0;
  width: 100%;
  color: #ccc;
  padding: 0.5em;
  text-align: center;
  user-select: none;
}
</style>
