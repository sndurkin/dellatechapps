<script>
  import { onMount } from 'svelte';

  import RecentRecipesPage from './RecentRecipesPage.svelte';
  import AddRecipePage from './AddRecipePage.svelte';
  import RecipeDetailPage from './RecipeDetailPage.svelte';
  import GroceryListPage from './GroceryListPage.svelte';

  import * as recipeUtils from './recipeUtils';


  const pages = {
    'home': {
      path: '/',
      title: 'Home',
    },
    'grocery-list': {
      path: '/list/',
      title: 'Grocery list',
    },
    'recipe': {
      path: '/recipe/',
      title: 'Recipe',
    },
    'new-recipe': {
      path: '/new/',
      title: 'New recipe',
    },
    'edit-recipe': {
      path: '/edit/',
      title: 'Edit recipe',
    },
  };

  const pagesByPath = {};
  for (const [key, value] of Object.entries(pages)) {
    pagesByPath[value.path] = key;
  }

  const username = recipeUtils.getUsername();
  let activePage = 'home';
  let activePageData = {};

  function navigateTo(page, pageData) {
    const newPath = `/${username}${pages[page].path}`;
    if (window.location.pathname !== newPath) {
      window.history.pushState({}, '', newPath);
      setPageFromPath(pageData);
    }
  }

  function handleNavClick(event) {
    navigateTo(event.target.id);
  }

  function setPageFromPath(pageData = {}) {
    const paths = window.location.pathname.split('/');
    activePage = pagesByPath[`/${paths?.[2]}/`] || 'home';
    activePageData = pageData;
    console.log('setPageFromPath: ', activePage, activePageData);
  }

  function handleOpenRecipe(event) {
    navigateTo('recipe', { recipe: event.detail.recipe });
  }

  function handleNewRecipe() {
    navigateTo('new-recipe');
  }

  onMount(() => {
    setPageFromPath();
    window.addEventListener('popstate', setPageFromPath);
  });
</script>

<nav aria-label="breadcrumb" class="d-flex align-items-center">
  <ol class="breadcrumb mb-0">
    <li class={`breadcrumb-item ${activePage === 'home' ? 'active' : ''}`}>
      {#if activePage === 'home'}
        {pages['home'].title}
      {:else}
        <a id="home" href="javascript:;" on:click={handleNavClick}>{pages['home'].title}</a>
      {/if}
    </li>
    {#if activePage !== 'home'}
      <li class={`breadcrumb-item active`}>
        {pages[activePage].title}
      </li>
    {/if}
  </ol>
  {#if activePage !== 'grocery-list'}
    <a class="grocery-list-link ms-auto" href="javascript:;" on:click={() => navigateTo('grocery-list')}>
      {pages['grocery-list'].title}
    </a>
  {/if}
</nav>
<div class="tab-content mt-3">
  <div class={`tab-pane ${activePage === 'home' ? 'show active' : ''}`}>
    <RecentRecipesPage
      {...activePageData}
      on:recipe-selected={handleOpenRecipe}
      on:new-recipe={handleNewRecipe}
    />
  </div>
  <div class={`tab-pane ${activePage === 'new-recipe' ? 'show active' : ''}`}>
    <AddRecipePage  {...activePageData} on:recipe-fetched={handleOpenRecipe} />
  </div>
  <div class={`tab-pane ${activePage === 'recipe' ? 'show active' : ''}`}>
    <RecipeDetailPage {...activePageData} />
  </div>
  <div class={`tab-pane ${activePage === 'grocery-list' ? 'show active' : ''}`}>
    <GroceryListPage  {...activePageData} />
  </div>
</div>

<style>

</style>
