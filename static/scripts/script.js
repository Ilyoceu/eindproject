document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.product[data-href]').forEach(function (product) {
    product.style.cursor = 'pointer';
    product.addEventListener('click', function () {
      window.location.href = product.dataset.href;
    });
  });

  // Intercept favorite form submissions so the page doesn't reload/scroll to top
  document.addEventListener('submit', function (e) {
    const form = e.target;
    if (!form || !form.querySelector) return;
    const favButton = form.querySelector('.fav-button');
    if (!favButton) return;

    e.preventDefault();

    // send POST via fetch to toggle favorite; include credentials for session cookie
    fetch(form.action, { method: 'POST', credentials: 'same-origin' })
      .then(function (resp) {
        // Toggle icon locally to reflect the change
        const icon = favButton.querySelector('i');
        if (icon) {
          if (icon.classList.contains('fa-regular')) {
            icon.classList.remove('fa-regular');
            icon.classList.add('fa-solid');
            icon.style.color = '#ff0000';
          } else {
            icon.classList.remove('fa-solid');
            icon.classList.add('fa-regular');
            icon.style.color = 'black';
          }
        }
      })
      .catch(function (err) {
        console.error('Error toggling favorite:', err);
      });
  });
});
