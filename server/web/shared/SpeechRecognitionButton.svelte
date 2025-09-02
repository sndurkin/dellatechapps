<script>
  import { onMount, createEventDispatcher } from 'svelte';


  const dispatch = createEventDispatcher();

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
    class={`btn btn-primary rounded-circle position-fixed bottom-0 end-0 m-3 ${listening ? 'listening' : ''}`}
    on:click={toggleListening}
  >
    <i class={`bi ${listening ? 'bi-stop-circle' : 'bi-mic'}`}></i>
  </button>
{/if}

<style>
  button {
    transition: background-color 0.3s ease, opacity 0.3s ease;
    opacity: 0.65;
    width: 3rem;
    height: 3rem;
  }

  button:hover {
    background-color: #0056b3;
    opacity: 1;
  }
</style>
