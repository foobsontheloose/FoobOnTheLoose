/* The hamburger menu. Shared by the homepage and every standalone section
   page, so there is one implementation rather than two that could drift. */
/* Hamburger menu, narrow screens only */
(function () {
  var nav = document.querySelector('.ribbon-nav');
  var toggle = document.getElementById('nav-toggle');
  if (!nav || !toggle) return;

  function setOpen(open) {
    nav.classList.toggle('menu-open', open);
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
  }

  toggle.addEventListener('click', function () {
    setOpen(!nav.classList.contains('menu-open'));
  });

  // Choosing a destination closes the menu behind you.
  nav.querySelectorAll('.ribbon-link').forEach(function (link) {
    link.addEventListener('click', function () { setOpen(false); });
  });

  document.addEventListener('click', function (e) {
    if (!nav.contains(e.target)) setOpen(false);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') setOpen(false);
  });
})();
