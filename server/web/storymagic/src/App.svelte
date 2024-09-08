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

    state = 'creating';
    const resp = await fetch('/stories', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        topic,
        grade,
        sentenceCount,
      }),
    });

    const data = await resp.json();
    story = data.story;
    wordMappings = data.wordMappings || {};
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
}
</style>
