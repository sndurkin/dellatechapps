<script>
  import { onMount } from 'svelte';

  import Home from './Home.svelte';
  import CreateUsernameForm from './CreateUsernameForm.svelte';

  import Frame from '../Frame.svelte';
  import * as recipeUtils from './recipeUtils';

  const paths = window.location.pathname.split('/');
  const state = paths.filter(p => p).length === 0 ? 'select-username' : 'home';

  onMount(() => {
    if (state === 'home') {
      document.title = `${recipeUtils.getUsername()} - Kitchen Buddy`;
    }
  });
</script>

<Frame>
  <div class="col-lg-8 col-md-10 col-sm-12">
    {#if state === 'select-username'}
      <CreateUsernameForm />
    {:else}
      <Home />
    {/if}
  </div>
</Frame>

<style>

</style>
