

<main>
  <div class="container">
    <div class="row mt-3 justify-content-center">
      <slot />
    </div>
  </div>
</main>
<footer>by Della Tech LLC</footer>

<style>
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
