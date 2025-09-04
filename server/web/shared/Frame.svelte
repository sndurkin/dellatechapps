

<main>
  <div class="container flex-grow-1 d-flex flex-column">
    <div class="row flex-grow-1 d-flex flex-column">
      <slot />
    </div>
  </div>
</main>
<footer>by Della Tech LLC</footer>

<style>
main {
  height: 100vh;

  display: flex;
  flex-direction: column;
}

footer {
  position: fixed;
  left: 0;
  bottom: 0;
  color: #ccc;
  padding: 0.5em;
  pointer-events: none;
  z-index: -1;
}
</style>
