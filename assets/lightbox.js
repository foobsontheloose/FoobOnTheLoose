/* Tap a photo to see it full size, with its caption underneath. Shared by
   the homepage and the standalone About page, so the captions are never
   stranded on a page that cannot show them. */
/* Photo wall: tap a snapshot to see it full size */
(function () {
  var box = document.getElementById('lightbox');
  var img = document.getElementById('lightbox-img');
  var cap = document.getElementById('lightbox-cap');
  var dateEl = document.getElementById('lightbox-date');
  if (!box || !img) return;
  var lastFocused = null;

  document.querySelectorAll('.wall-shot').forEach(function (shot) {
    shot.addEventListener('click', function () {
      lastFocused = shot;
      var inner = shot.querySelector('img');
      img.src = inner.src;
      img.alt = inner.alt || '';
      if (cap) cap.textContent = shot.getAttribute('data-caption') || '';
      if (dateEl) dateEl.textContent = shot.getAttribute('data-date') || '';
      box.classList.add('open');
    });
  });

  function close() {
    box.classList.remove('open');
    // release the full-size image so it is not held in memory
    setTimeout(function () { if (!box.classList.contains('open')) img.src = ''; }, 300);
    if (lastFocused) lastFocused.focus();
  }

  box.addEventListener('click', close);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && box.classList.contains('open')) close();
  });
})();
