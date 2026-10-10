    /* Footer year — always current */
    (function () {
      var y = document.getElementById('year');
      if (y) y.textContent = new Date().getFullYear();
    })();

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

    (function () {
      var modal = document.getElementById('modal');
      var closeBtn = document.getElementById('modal-close');
      var panels = document.querySelectorAll('.tab-panel');
      var card = modal.querySelector('.modal-card');

      // Where the reader had got to in the reconstruction list. Backing out of
      // a detail returns them to that spot: the list is long enough that
      // snapping to the top loses the option they were just reading about.
      var listScroll = 0;

      /* Every panel also exists as a real page at its own address, generated
         by build-pages.py. Opening one here updates the address bar to match,
         so the view can be shared and the back button steps through panels
         instead of leaving the site. The modal behaves as it always has; if
         this script never runs, the links still reach real pages. */
      var PANEL_URLS = {
        'panel-why': '/why-it-matters',
        'panel-signs': '/know-the-signs',
        'panel-screening': '/screening',
        'panel-recon': '/reconstruction',
        'panel-questions': '/questions-to-ask',
        'panel-men': '/men',
        'panel-support': '/support',
        'panel-risk': '/know-your-risk',
        'panel-about': '/about',
        'panel-follow': '/follow',
        'recon-Direct': '/reconstruction/direct-to-implant',
        'recon-TEtoIMPLANT': '/reconstruction/tissue-expander',
        'recon-DIEP': '/reconstruction/diep',
        'recon-TRAM': '/reconstruction/tram',
        'recon-PAP': '/reconstruction/pap',
        'recon-SGAP': '/reconstruction/sgap',
        'recon-IGAP': '/reconstruction/igap',
        'recon-TUG': '/reconstruction/tug',
        'recon-LAT': '/reconstruction/latissimus',
        'recon-FatGrafting': '/reconstruction/fat-grafting',
        'recon-ComboHybrid': '/reconstruction/combination',
        'recon-NippleAreola': '/reconstruction/nipple-areola',
        'recon-FlatClosure': '/reconstruction/flat-closure'
      };
      var URL_PANELS = {};
      Object.keys(PANEL_URLS).forEach(function (k) { URL_PANELS[PANEL_URLS[k]] = k; });
      var replayingHistory = false;

      function syncUrl(path) {
        if (replayingHistory) return;
        if (location.pathname !== path) history.pushState({ path: path }, '', path);
      }

      window.addEventListener('popstate', function () {
        var id = URL_PANELS[location.pathname.replace(/\/+$/, '') || '/'];
        replayingHistory = true;
        if (id) { openPanel(id); } else { closeModal(); }
        replayingHistory = false;
      });

      function openPanel(panelId) {
        var reconList = document.getElementById('panel-recon');
        var leavingList = reconList && !reconList.hidden;
        var toDetail = /^recon-/.test(panelId) && panelId !== 'panel-recon';
        if (leavingList && toDetail) listScroll = card.scrollTop;

        panels.forEach(function (p) {
          p.hidden = (p.id !== panelId);
        });
        // the corner control backs out one level inside a detail view,
        // so show a back chevron there instead of a close cross
        var isDetail = /^recon-/.test(panelId) && panelId !== 'panel-recon';
        closeBtn.innerHTML = isDetail ? '&lsaquo;' : '&times;';
        closeBtn.setAttribute('aria-label', isDetail ? 'Back to all options' : 'Close');
        modal.classList.add('open');
        document.body.classList.add('panel-open');
        document.body.style.overflow = 'hidden';
        // reading scrollHeight forces layout, so the restored offset is not
        // clamped against the height of the panel we just left
        void card.scrollHeight;
        card.scrollTop = (panelId === 'panel-recon') ? listScroll : 0;
        requestAnimationFrame(updateCue);
        syncUrl(PANEL_URLS[panelId] || '/');
      }

      // The cue points down while there is more below and flips to point up at
      // the end, staying put so it reads as one control. Tapping follows
      // whichever way it is pointing.
      var cue = document.getElementById('scroll-cue');

      function updateCue() {
        if (!cue) return;
        var scrollable = card.scrollHeight - card.clientHeight > 24;
        var atEnd = card.scrollHeight - card.scrollTop - card.clientHeight <= 24;
        card.classList.toggle('can-scroll', scrollable);
        cue.classList.toggle('at-end', scrollable && atEnd);
        cue.setAttribute('aria-label', atEnd ? 'Back to top' : 'Scroll down for more');
      }

      if (cue) {
        card.addEventListener('scroll', updateCue, { passive: true });
        window.addEventListener('resize', updateCue);
        cue.addEventListener('click', function () {
          if (cue.classList.contains('at-end')) {
            card.scrollTo({ top: 0, behavior: 'smooth' });
          } else {
            card.scrollBy({ top: card.clientHeight * 0.82, behavior: 'smooth' });
          }
        });
      }

      function closeModal() {
        // a fresh visit to the list starts at the top again
        listScroll = 0;
        modal.classList.remove('open');
        document.body.classList.remove('panel-open');
        document.body.style.overflow = '';
        syncUrl('/');
      }

      document.querySelectorAll('[data-panel]').forEach(function (el) {
        el.addEventListener('click', function () {
          openPanel(el.dataset.panel);
        });
      });

      document.querySelectorAll('[data-goto]').forEach(function (btn) {
        btn.addEventListener('click', function () {
          openPanel(btn.dataset.goto);
        });
      });

      closeBtn.addEventListener('click', dismiss);

      modal.addEventListener('click', function (e) {
        if (e.target === modal) dismiss();
      });

      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') dismiss();
      });

      // Inside a reconstruction detail, backing out returns to the list
      // rather than dumping the person all the way back to the page.
      function dismiss() {
        var open = null;
        panels.forEach(function (p) { if (!p.hidden) open = p; });
        if (open && open.classList.contains('recon-detail')) {
          openPanel('panel-recon');
        } else {
          closeModal();
        }
      }
    })();

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

    /* Page scroll cue: same control, same behaviour, for the page itself */
    (function () {
      var cue = document.getElementById('page-cue');
      if (!cue) return;

      function update() {
        var doc = document.documentElement;
        var scrollable = doc.scrollHeight - window.innerHeight > 120;
        var atEnd = window.scrollY + window.innerHeight >= doc.scrollHeight - 40;
        document.body.classList.toggle('page-scrollable', scrollable);
        cue.classList.toggle('at-end', scrollable && atEnd);
        cue.setAttribute('aria-label', atEnd ? 'Back to top' : 'Scroll down');
      }

      cue.addEventListener('click', function () {
        if (cue.classList.contains('at-end')) {
          window.scrollTo({ top: 0, behavior: 'smooth' });
        } else {
          window.scrollBy({ top: window.innerHeight * 0.85, behavior: 'smooth' });
        }
      });

      window.addEventListener('scroll', update, { passive: true });
      window.addEventListener('resize', update);
      update();
    })();

    /* ---- Calendar reminder ---- */
    (function () {
      var btn = document.getElementById('cal-btn');
      var calModal = document.getElementById('cal-modal');
      var calClose = document.getElementById('cal-close');
      var icsBtn = document.getElementById('cal-ics');
      var gLink = document.getElementById('cal-google');

      var TITLE = 'Feel It on the First';
      var DETAILS = 'Your monthly reminder to check yourself. Steps at https://foobsontheloose.com';

      function pad(n) { return (n < 10 ? '0' : '') + n; }

      // first day of next month, so the reminder always starts in the future
      function firstOfNextMonth() {
        var now = new Date();
        return new Date(now.getFullYear(), now.getMonth() + 1, 1);
      }

      function dateStamp(d) {
        return d.getFullYear() + pad(d.getMonth() + 1) + pad(d.getDate());
      }

      function buildICS() {
        var start = firstOfNextMonth();
        var end = new Date(start.getFullYear(), start.getMonth(), start.getDate() + 1);
        var now = new Date();
        var stamp = now.getUTCFullYear() + pad(now.getUTCMonth() + 1) + pad(now.getUTCDate())
                  + 'T' + pad(now.getUTCHours()) + pad(now.getUTCMinutes()) + pad(now.getUTCSeconds()) + 'Z';

        var lines = [
          'BEGIN:VCALENDAR',
          'VERSION:2.0',
          'PRODID:-//Foobs On the Loose//Self-exam reminder//EN',
          'CALSCALE:GREGORIAN',
          'BEGIN:VEVENT',
          'UID:' + stamp + '-foobsontheloose@foobsontheloose.com',
          'DTSTAMP:' + stamp,
          'DTSTART;VALUE=DATE:' + dateStamp(start),
          'DTEND;VALUE=DATE:' + dateStamp(end),
          'RRULE:FREQ=MONTHLY;BYMONTHDAY=1',
          'SUMMARY:' + TITLE,
          'DESCRIPTION:' + DETAILS,
          'TRANSP:TRANSPARENT',
          'BEGIN:VALARM',
          'ACTION:DISPLAY',
          'DESCRIPTION:' + TITLE,
          'TRIGGER:PT9H',
          'END:VALARM',
          'END:VEVENT',
          'END:VCALENDAR'
        ];
        return lines.join('\r\n');
      }

      function makeIcsUrl() {
        var data = buildICS();
        try {
          var blob = new Blob([data], { type: 'text/calendar;charset=utf-8' });
          return { url: URL.createObjectURL(blob), isBlob: true };
        } catch (err) {
          return { url: 'data:text/calendar;charset=utf-8,' + encodeURIComponent(data), isBlob: false };
        }
      }

      function googleUrl() {
        var start = firstOfNextMonth();
        var end = new Date(start.getFullYear(), start.getMonth(), start.getDate() + 1);
        return 'https://calendar.google.com/calendar/render?action=TEMPLATE'
          + '&text=' + encodeURIComponent(TITLE)
          + '&details=' + encodeURIComponent(DETAILS)
          + '&dates=' + dateStamp(start) + '/' + dateStamp(end)
          + '&recur=' + encodeURIComponent('RRULE:FREQ=MONTHLY;BYMONTHDAY=1');
      }

      var lastIcsUrl = null;

      function openCal() {
        gLink.href = googleUrl();

        // build a real href up front so the link is a genuine download,
        // not a scripted click (which desktop browsers often block)
        if (lastIcsUrl) {
          try { URL.revokeObjectURL(lastIcsUrl); } catch (e) {}
          lastIcsUrl = null;
        }
        var made = makeIcsUrl();
        icsBtn.href = made.url;
        if (made.isBlob) lastIcsUrl = made.url;

        calModal.classList.add('open');
        document.body.style.overflow = 'hidden';
      }

      function closeCal() {
        calModal.classList.remove('open');
        document.body.style.overflow = '';
      }

      if (btn) btn.addEventListener('click', openCal);
      // anything marked data-cal opens the reminder chooser as well
      document.querySelectorAll('[data-cal]').forEach(function (el) {
        el.addEventListener('click', openCal);
      });
      if (calClose) calClose.addEventListener('click', closeCal);

      // When the .ics opens in Calendar (or Google Calendar opens in a new tab)
      // this page gets backgrounded and timers are suspended, so a setTimeout
      // close is unreliable. Close when the page is hidden or loses focus
      // instead, so it's already dismissed when they come back.
      var calJustUsed = false;

      function markUsed() {
        calJustUsed = true;
        setTimeout(function () {
          if (calModal.classList.contains('open')) closeCal();
        }, 1200);
      }

      if (icsBtn) icsBtn.addEventListener('click', markUsed);
      if (gLink) gLink.addEventListener('click', markUsed);

      document.addEventListener('visibilitychange', function () {
        if (document.hidden && calJustUsed) {
          closeCal();
          calJustUsed = false;
        }
      });

      window.addEventListener('pagehide', function () {
        if (calJustUsed) {
          closeCal();
          calJustUsed = false;
        }
      });

      window.addEventListener('blur', function () {
        if (calJustUsed) {
          closeCal();
          calJustUsed = false;
        }
      });

      calModal.addEventListener('click', function (e) {
        if (e.target === calModal) closeCal();
      });

      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeCal();
      });
    })();
