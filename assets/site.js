    /* One place that freezes and restores the page behind any overlay. */
    var pageLockY = 0, pageLocked = false;
    function lockPage() {
      if (pageLocked) return;
      pageLockY = window.scrollY || document.documentElement.scrollTop || 0;
      document.body.style.setProperty('--page-lock-top', (-pageLockY) + 'px');
      document.body.classList.add('panel-open');
      pageLocked = true;
    }
    function unlockPage() {
      if (!pageLocked) return;
      document.body.classList.remove('panel-open');
      document.body.style.removeProperty('--page-lock-top');
      // the page has smooth scrolling; restoring must be instant or the
      // reader watches it glide back after closing a panel
      window.scrollTo({ top: pageLockY, left: 0, behavior: 'instant' });
      pageLocked = false;
    }

    /* Footer year — always current */
    (function () {
      var y = document.getElementById('year');
      if (y) y.textContent = new Date().getFullYear();
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
        'recon-FlatClosure': '/reconstruction/flat-closure',
        'q-breast': '/questions-to-ask/breast-surgeon',
        'q-plastic': '/questions-to-ask/plastic-surgeon'
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
        // The corner control means the same thing on every panel: close.
        // Going back a level is the "All options" link at the top left, so
        // each control does one job, the corner behaves the same everywhere,
        // and leaving a detail takes one tap rather than backing out first.
        closeBtn.innerHTML = '&times;';
        closeBtn.setAttribute('aria-label', 'Close');
        modal.classList.add('open');
        lockPage();
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

      // The card's own bottom padding, read while the cue is not there. The
      // cue's padding replaces it rather than adding to it, so the room the
      // cue actually costs is the difference between the two - and that is
      // the only part that may be subtracted below.
      var basePadBottom = null;

      function updateCue() {
        if (!cue) return;
        // Measure the content itself, not the room the cue is standing in.
        // Without this a panel that overflows by a hair gets a cue, the cue
        // adds padding, and the panel now overflows by plenty - the cue
        // arguing itself into existence. Subtracting the reserved space
        // means the same number is measured whether the cue is there or not,
        // so a panel that does not really need to scroll never gets one.
        //
        // That subtraction used to be the whole 70px, but 28px of it is the
        // card's ordinary padding and was in the measurement already. The two
        // states disagreed by 28px, and a panel landing in that gap flipped
        // between them forever: Latissimus Dorsi measured 45px over without
        // the cue - enough to earn one - and 17px over with it, not enough to
        // keep it. On a computer it settles on the first answer. On an iPhone
        // Safari's toolbar sends a resize every few milliseconds while it
        // slides, so this ran again and again and the card flickered and
        // fought the reader's thumb.
        var padBottom = parseFloat(getComputedStyle(card).paddingBottom) || 0;
        var hasCue = card.classList.contains('can-scroll');
        if (!hasCue) basePadBottom = padBottom;
        var reserved = (hasCue && basePadBottom !== null)
          ? Math.max(0, padBottom - basePadBottom)
          : 0;
        var scrollable = card.scrollHeight - card.clientHeight - reserved > 24;
        // A panel that is a dozen pixels too tall should not move at all.
        // It has no cue, nothing worth reading is below the fold, and all
        // the drag does is make the card feel loose. Anything it clips is
        // inside the card's own bottom padding, which is 24px at its
        // smallest - the same number as the threshold.
        card.classList.toggle('fits', !scrollable);
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
        unlockPage();
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

      closeBtn.addEventListener('click', closeModal);

      modal.addEventListener('click', function (e) {
        if (e.target === modal) closeModal();
      });

      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeModal();
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

      /* Which machine she is on. An iPad calls itself a Macintosh, so a touch
         screen is what tells the two apart - and getting that wrong would send
         a Mac's route to an iPad, which does not need it. Anything we do not
         recognise is left alone and keeps the label in the markup. */
      var PLATFORM = (function () {
        var ua = navigator.userAgent;
        if (/iPhone|iPad|iPod/.test(ua)) return 'ios';
        if (/Macintosh/.test(ua)) return navigator.maxTouchPoints ? 'ios' : 'mac';
        if (/Android/.test(ua)) return 'android';
        if (/Windows/.test(ua)) return 'windows';
        return '';
      })();

      /* The option named every calendar it serves - Apple, Samsung and
         Outlook - which meant whoever was reading it had to find herself in a
         list. Nobody reads a label looking for her own name; she either sees
         it or she does not. So it says the one that is hers, and what will
         happen when she taps it, which is different on each of them.

         The file behind it is the same everywhere. Only a Mac is a different
         address, because only a Mac cannot open the file without a trip to
         Downloads - see below. */
      var LABELS = {
        ios:     ['Apple Calendar', 'Opens straight into your Calendar app'],
        mac:     ['Apple Calendar', 'Opens Calendar \u2014 nothing to download'],
        android: ['Samsung & other calendars', 'Downloads a file \u2014 tap it to import'],
        windows: ['Outlook & other calendars', 'Downloads a file \u2014 open it to add']
      };

      if (icsBtn && LABELS[PLATFORM]) {
        var title = icsBtn.querySelector('.cal-opt-title');
        var sub = icsBtn.querySelector('.cal-opt-sub');
        if (title) title.textContent = LABELS[PLATFORM][0];
        if (sub) sub.textContent = LABELS[PLATFORM][1];

        /* The footnote is a sentence about iPhones and a sentence about
           Android phones, written when the option could not say which was
           which. Now it can, and the footnote only repeats it or talks about
           a machine she is not on. It stays for anything unrecognised. */
        var footnote = document.querySelector('.cal-note');
        if (footnote) footnote.hidden = true;
      }

      /* A phone hands the file straight to Calendar in one tap. A Mac cannot:
         it saves it to Downloads and she has to go and find it. So on a Mac
         the option itself becomes the thing that works there - webcal: is not
         a web address, so the browser passes it to the machine, which has it
         bound to Calendar - and nobody has to read a word to get it.

         It is Apple's calendar that answers webcal:, so the file moves down to
         the small print for anyone on a Mac running Outlook or anything else.
         The line nobody reads carries the rare case rather than the common
         one. */
      if (icsBtn && PLATFORM === 'mac') {
        var ICS_HREF = icsBtn.getAttribute('href');
        icsBtn.href = 'webcal://foobsontheloose.com/feel-it-on-the-first.ics';
        icsBtn.removeAttribute('download');

        var other = document.createElement('p');
        other.className = 'cal-mac';
        other.appendChild(document.createTextNode('Outlook, or something else? '));
        var file = document.createElement('a');
        file.href = ICS_HREF;
        file.setAttribute('download', 'feel-it-on-the-first.ics');
        file.textContent = 'Download the calendar file';
        other.appendChild(file);
        other.appendChild(document.createTextNode(' instead.'));
        icsBtn.insertAdjacentElement('afterend', other);
      }

      /* These feed the Google Calendar link, and build-pages.py reads them
         out of here to write /feel-it-on-the-first.ics, so the two routes
         cannot drift apart. Rename either one and the build stops. */
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

      function googleUrl() {
        var start = firstOfNextMonth();
        var end = new Date(start.getFullYear(), start.getMonth(), start.getDate() + 1);
        return 'https://calendar.google.com/calendar/render?action=TEMPLATE'
          + '&text=' + encodeURIComponent(TITLE)
          + '&details=' + encodeURIComponent(DETAILS)
          + '&dates=' + dateStamp(start) + '/' + dateStamp(end)
          + '&recur=' + encodeURIComponent('RRULE:FREQ=MONTHLY;BYMONTHDAY=1');
      }

      /* The Apple option is a plain link to a real file in the markup, so it
         works with no script at all and arrives with its own name. Only the
         Google link, which carries the dates in its address, is built here. */
      function openCal() {
        gLink.href = googleUrl();
        calModal.classList.add('open');
        lockPage();
      }

      function closeCal() {
        calModal.classList.remove('open');
        unlockPage();
      }

      if (btn) btn.addEventListener('click', openCal);
      // anything marked data-cal opens the reminder chooser as well
      document.querySelectorAll('[data-cal]').forEach(function (el) {
        el.addEventListener('click', openCal);
      });
      if (calClose) calClose.addEventListener('click', closeCal);

      // A section page has no chooser on it, so "Set your reminder" there
      // links to /?reminder and the chooser is already open when she lands -
      // one tap from anywhere rather than one tap and then a hunt for the
      // badge. The marker is dropped from the address afterwards so a
      // refresh or a bookmark does not reopen it.
      if (/[?&]reminder\b/.test(location.search)) {
        openCal();
        history.replaceState(null, '', location.pathname + location.hash);
      }

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
