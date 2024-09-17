function getUsername() {
  return window.location.pathname.split('/')[1];
}

export {
  getUsername,
};
