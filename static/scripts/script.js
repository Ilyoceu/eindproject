document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.product[data-href]').forEach(function (product) {
    product.style.cursor = 'pointer';
    product.addEventListener('click', function () {
      window.location.href = product.dataset.href;
    });
  });
});
