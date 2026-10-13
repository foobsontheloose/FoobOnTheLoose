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

/* Facebook and Instagram open links in their own in-app browser, which is a
   WKWebView with none of the parts a real browser hands a page: no print
   dialog, and no handing a downloaded file to another app. Printing does
   nothing at all, and the calendar file arrives on the screen as text. Neither
   is fixable from in here, so the honest thing is to say so before she taps
   rather than leave her pressing a dead button. Everywhere else - a real
   browser on a phone or a computer - this runs and does nothing. */
(function () {
  var ua = navigator.userAgent || '';
  var app = /FBAN|FBAV|FB_IAB|FBIOS/.test(ua) ? 'Facebook'
          : /Instagram/.test(ua) ? 'Instagram'
          : '';
  if (!app) return;

  var OPEN_IT = "Tap ••• at the top right and open this page in your browser";

  function noteAfter(el, text) {
    var note = document.createElement('p');
    note.className = 'print-note';
    note.textContent = text;
    el.insertAdjacentElement('afterend', note);
    return note;
  }

  var buttons = document.querySelectorAll('.print-btn');
  for (var i = 0; i < buttons.length; i++) {
    noteAfter(buttons[i], app + "’s browser can’t print. " + OPEN_IT
      + " — then Print this list will work.");
  }

  /* The calendar file hits the same wall from the other side: the browser is
     handed a .ics and shows it as text on the screen rather than passing it to
     the Calendar app. The card's own footnote - that the file opens straight
     into Calendar on an iPhone - is the one thing that is not true in here, so
     it stands down while this is showing. */
  var ics = document.getElementById('cal-ics');
  if (ics) {
    var note = noteAfter(ics, app + "’s browser can’t open the calendar file "
      + "— it shows it as text instead. " + OPEN_IT + ", then tap this again.");

    /* webcal: is not a web address, so this browser does not try to open it
       itself - it hands it to the phone, which gives it to the Calendar app.
       That is the one route out of here that does not need her to leave
       first, and it subscribes rather than adding a single event, which is
       why it says subscribe. */
    var sub = document.createElement('a');
    sub.className = 'print-note-link';
    sub.href = 'webcal://foobsontheloose.com/feel-it-on-the-first.ics';
    sub.textContent = 'Or tap here to subscribe in your Calendar app';
    note.appendChild(sub);

    var footnote = document.querySelector('.cal-note');
    if (footnote) footnote.hidden = true;
  }
})();
