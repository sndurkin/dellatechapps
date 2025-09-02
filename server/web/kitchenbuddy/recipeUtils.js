function getUsername() {
  const parts = window.location.pathname.split('/');
  if (parts[2] === 'u' && parts.length > 3) {
    return parts[3];
  }
  return null;
}

export {
  getUsername,
};
