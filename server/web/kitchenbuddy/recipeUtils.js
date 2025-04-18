function getUsername() {
  const parts = window.location.pathname.split('/');
  if (parts[1] === 'u' && parts.length > 2) {
    return parts[2];
  }
  return null;
}

export {
  getUsername,
};
