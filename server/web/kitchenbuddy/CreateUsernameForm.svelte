<script>
  import * as utils from '../utils';


  let username = '';

  function handleUsernameInput(event) {
    username = event.target.value.replace(/[^A-Za-z0-9_-]/g, '').toLowerCase();
  }

  function handleSelectUsername() {
    window.location.href = `/${username}/`;
  }
</script>

<div class="form-floating mb-3">
  <input
    type="text"
    class="form-control"
    placeholder="e.g. janedoe"
    id="username"
    on:input={handleUsernameInput}
    on:keyup={utils.onEnter(handleSelectUsername)}
    value={username}
  />
  <label for="username">Enter a username</label>
</div>
<div>
  <button class="btn btn-primary" type="button" title="Select username" on:click={handleSelectUsername}>
    Select
  </button>
</div>

<style>

</style>
