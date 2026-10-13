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

/* Facebook and Instagram open links in their own in-app browser, and that
   browser has no print dialog at all - WKWebView leaves printing to the host
   app, and neither app built one. window.print() fires and nothing happens.
   Nothing here can change that, so the honest thing is to say so before she
   taps rather than leave her pressing a dead button. Everywhere else - a real
   browser on a phone or a computer - this runs and does nothing. */
(function () {
  var ua = navigator.userAgent || '';
  var app = /FBAN|FBAV|FB_IAB|FBIOS/.test(ua) ? 'Facebook'
          : /Instagram/.test(ua) ? 'Instagram'
          : '';
  if (!app) return;

  var buttons = document.querySelectorAll('.print-btn');
  for (var i = 0; i < buttons.length; i++) {
    var note = document.createElement('p');
    note.className = 'print-note';
    note.textContent = app + "’s browser can’t print. Tap ••• at the "
      + "top right and open this page in your browser — then Print this list "
      + "will work.";
    buttons[i].insertAdjacentElement('afterend', note);
  }
})();
