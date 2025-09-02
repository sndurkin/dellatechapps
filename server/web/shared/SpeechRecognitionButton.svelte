<script>
  import { onMount, createEventDispatcher } from 'svelte';


  const dispatch = createEventDispatcher();

  export let className = '';

  let speechRecognitionSupported = 'SpeechRecognition' in window || 'webkitSpeechRecognition' in window;
  let listening = false;
  let recognition;

  onMount(() => {
    recognition = new (window['SpeechRecognition'] || window['webkitSpeechRecognition'])();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      listening = true;
    };

    recognition.onresult = (event) => {
      if (!event.results) {
        listening = false;
        recognition.onend = null;
        recognition.stop();
        return;
      }

      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      if (transcript) {
        dispatch('speech', { transcript });
      }
    };

    recognition.onend = () => {
      listening = false;
    };

    recognition.onerror = (event) => {
      // error could be one of: 'no-speech', 'aborted', 'audio-capture', 'network', 'not-allowed', 'service-not-allowed', 'bad-grammar', 'language-not-supported'
      dispatch('error', { error: event.error });
    };
  });

  function toggleListening() {
    if (!listening) {
      recognition.start();
    }
    else {
      recognition.stop();
    }
  }
</script>

{#if speechRecognitionSupported}
  <button
    class={`btn rounded-circle m-3 ${listening ? 'listening' : ''} ${className}`}
    on:click={toggleListening}
  >
    <i class={`bi ${listening ? 'bi-stop-circle' : 'bi-mic'}`}></i>
  </button>
{/if}

<style>
  button {
    transition: background-color 0.3s ease, opacity 0.3s ease;
    opacity: 0.75;
    width: 2rem;
    height: 2rem;
  }

  button:hover {
    color: #025fc2;
    opacity: 1;
  }

  button:focus {
    box-shadow: none;
  }
</style>
