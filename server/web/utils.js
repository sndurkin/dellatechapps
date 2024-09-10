function onEnter(fn) {
  return (event) => {
    if (event.key === 'Enter') {
      fn();
    }
  };
}

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          // Check if this cookie string begins with the name we want
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
          }
      }
  }
  return cookieValue;
}

function getCsrfToken() {
  return getCookie('csrftoken');
}

export {
  onEnter,
  getCookie,
  getCsrfToken,
};
