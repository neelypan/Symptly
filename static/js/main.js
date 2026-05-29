(function () {
  'use strict';

  function icons() { if (window.lucide) window.lucide.createIcons(); }

  // ---- Theme toggle -------------------------------------------------------
  function initTheme() {
    var btn = document.getElementById('themeToggle');
    if (!btn) return;
    btn.addEventListener('click', function () {
      var cur = document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
      var next = cur === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', next);
      try { localStorage.setItem('symptly-theme', next); } catch (e) {}
    });
  }

  // ---- Sidebar collapse ---------------------------------------------------
  function initSidebar() {
    var app = document.getElementById('app');
    var toggle = document.getElementById('sidebarToggle');
    if (!app || !toggle) return;

    // Apply persisted state without animating on first paint.
    var collapsed = false;
    try { collapsed = localStorage.getItem('symptly-sidebar') === 'collapsed'; } catch (e) {}
    if (collapsed) {
      app.style.transition = 'none';
      app.classList.add('collapsed');
      void app.offsetWidth; // force reflow
      app.style.transition = '';
    }
    toggle.addEventListener('click', function () {
      app.classList.toggle('collapsed');
      try {
        localStorage.setItem('symptly-sidebar', app.classList.contains('collapsed') ? 'collapsed' : 'open');
      } catch (e) {}
    });

    var resolvedToggle = document.getElementById('resolvedToggle');
    if (resolvedToggle) {
      resolvedToggle.addEventListener('click', function () {
        resolvedToggle.closest('.nav-section').classList.toggle('collapsed-section');
      });
    }
  }

  // ---- Toasts -------------------------------------------------------------
  function showToast(opts) {
    var region = document.getElementById('toastRegion');
    if (!region) return;
    var toast = document.createElement('div');
    toast.className = 'toast';

    var html = '';
    if (opts.title) html += '<div class="toast__title">' + opts.title + '</div>';
    if (opts.msg) html += '<div class="toast__msg">' + opts.msg + '</div>';
    toast.innerHTML = html;

    if (opts.actions && opts.actions.length) {
      var row = document.createElement('div');
      row.className = 'toast__actions';
      opts.actions.forEach(function (a) {
        var el = a.href ? document.createElement('a') : document.createElement('button');
        if (a.href) el.href = a.href;
        el.className = 'btn ' + (a.primary ? 'btn--primary' : 'btn--ghost');
        el.textContent = a.label;
        if (a.onClick) el.addEventListener('click', function () { a.onClick(); dismiss(); });
        row.appendChild(el);
      });
      toast.appendChild(row);
    }

    region.appendChild(toast);
    requestAnimationFrame(function () { toast.classList.add('is-visible'); });

    var timer = setTimeout(dismiss, opts.autoDismiss || 10000);
    function dismiss() {
      clearTimeout(timer);
      toast.classList.remove('is-visible');
      setTimeout(function () { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 250);
    }
    return dismiss;
  }

  // ---- Symptom checker ----------------------------------------------------
  function cleanLabel(id) {
    var s = String(id).replace(/_/g, ' ').replace(/\s+/g, ' ').trim();
    return s.charAt(0).toUpperCase() + s.slice(1);
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function initChecker() {
    var checker = document.getElementById('checker');
    if (!checker) return;

    var endpoint = checker.getAttribute('data-endpoint');
    var mode = checker.getAttribute('data-mode');
    var groups = document.getElementById('symptomGroups');
    var search = document.getElementById('symptomSearch');
    var predictBtn = document.getElementById('predictBtn');
    var countEl = document.getElementById('selectedCount');
    var resultsRegion = document.getElementById('resultsRegion');
    var noResults = document.getElementById('noResults');

    function selectedIds() {
      return Array.prototype.map.call(
        groups.querySelectorAll('.chip--selected:not(.chip--locked)'),
        function (c) { return c.getAttribute('data-id'); }
      );
    }

    function updateCount() {
      var n = selectedIds().length;
      countEl.textContent = n ? (n + ' selected') : '';
    }

    // Toggle chips (event delegation).
    groups.addEventListener('click', function (e) {
      var chip = e.target.closest('.chip');
      if (!chip || chip.disabled || chip.classList.contains('chip--locked')) return;
      chip.classList.toggle('chip--selected');
      updateCount();
    });

    // Search filter.
    if (search) {
      search.addEventListener('input', function () {
        var q = search.value.trim().toLowerCase();
        var anyVisible = false;
        groups.querySelectorAll('.sym-group').forEach(function (group) {
          var groupHasVisible = false;
          group.querySelectorAll('.chip').forEach(function (chip) {
            var match = !q || chip.getAttribute('data-label').indexOf(q) !== -1;
            chip.style.display = match ? '' : 'none';
            if (match) groupHasVisible = true;
          });
          group.style.display = groupHasVisible ? '' : 'none';
          if (groupHasVisible) anyVisible = true;
        });
        if (noResults) noResults.hidden = anyVisible;
      });
    }

    // Submit.
    predictBtn.addEventListener('click', function () {
      var ids = selectedIds();
      if (!ids.length) {
        showToast({ msg: 'Select at least one symptom first.', autoDismiss: 3000 });
        return;
      }
      predictBtn.classList.add('is-loading');
      predictBtn.disabled = true;

      fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symptoms: ids })
      })
        .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
        .then(function (res) {
          if (!res.ok) {
            showToast({ title: 'Something went wrong', msg: res.data.error || 'Please try again.', autoDismiss: 5000 });
            return;
          }
          var data = res.data;
          if (mode === 'new') {
            // First check-in created the episode; load it to show saved results.
            window.location = '/episode/' + data.episodeId;
            return;
          }
          renderResult(resultsRegion, data);
          lockSelected(groups, ids);
          updateCount();
          if (data.overlap === false) {
            var unrelated = ids.slice();
            var checkinId = data.checkinId;
            showToast({
              title: 'These symptoms seem different',
              msg: 'They don’t overlap with this issue. Move them to a new one instead?',
              actions: [
                { label: 'Switch to new issue', primary: true, onClick: function () {
                    switchToNewIssue(endpoint, checkinId, unrelated);
                  } },
                { label: 'Keep here', onClick: function () {} }
              ],
              autoDismiss: 10000
            });
          }
          resultsRegion.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        })
        .catch(function () {
          showToast({ title: 'Network error', msg: 'Could not reach the server.', autoDismiss: 5000 });
        })
        .then(function () {
          predictBtn.classList.remove('is-loading');
          predictBtn.disabled = false;
        });
    });

    // Render any predictions/emergency already saved on this episode.
    if (window.SYMPTLY_INITIAL) {
      var init = window.SYMPTLY_INITIAL;
      if (init.emergency) renderResult(resultsRegion, { isEmergency: true, emergency: init.emergency, predictions: init.predictions });
      else if (init.predictions && init.predictions.length) renderResult(resultsRegion, { predictions: init.predictions });
    }

    updateCount();
  }

  // Move just-added, unrelated symptoms off this issue: drop the check-in that
  // saved them here, then carry them to a fresh episode pre-selected.
  function switchToNewIssue(checkinEndpoint, checkinId, symptomIds) {
    var query = symptomIds.map(encodeURIComponent).join(',');
    var go = function () { window.location = '/episode/new?symptoms=' + query; };
    if (!checkinId) { go(); return; }
    fetch(checkinEndpoint + '/' + encodeURIComponent(checkinId), { method: 'DELETE' })
      .then(function (r) {
        if (r.ok) { go(); return; }
        showToast({ title: 'Could not move symptoms', msg: 'Please try again.', autoDismiss: 4000 });
      })
      .catch(function () {
        showToast({ title: 'Network error', msg: 'Could not reach the server.', autoDismiss: 4000 });
      });
  }

  function lockSelected(groups, ids) {
    ids.forEach(function (id) {
      var chip = groups.querySelector('.chip[data-id="' + (window.CSS && CSS.escape ? CSS.escape(id) : id) + '"]');
      if (chip) {
        chip.classList.add('chip--locked', 'chip--selected');
        chip.disabled = true;
        chip.title = 'From a previous check-in';
      }
    });
  }

  function injectPredictions(container, preds) {
    container.innerHTML = predictionsHtml(preds);
    icons();
    // Animate the confidence bars from 0 to their final width.
    requestAnimationFrame(function () {
      container.querySelectorAll('.pred__fill').forEach(function (fill) {
        fill.style.width = fill.getAttribute('data-width') + '%';
      });
    });
  }

  function renderResult(region, data) {
    if (data.isEmergency && data.emergency) {
      region.innerHTML = emergencyHtml(data.emergency);
      icons();
      // Let the user opt in to model suggestions without burying the warning.
      var preds = data.predictions || [];
      if (preds.length) {
        var wrap = document.createElement('div');
        wrap.className = 'post-emergency';
        wrap.innerHTML =
          '<p class="post-emergency__note">If you’re safe and still want to explore ' +
          'possibilities, you can view the model’s suggestions. They don’t replace urgent care.</p>' +
          '<button type="button" class="btn btn--ghost" id="revealPredictions">' +
          '<i data-lucide="eye"></i> Show possible conditions anyway</button>' +
          '<div class="post-emergency__results" id="postEmergencyResults"></div>';
        region.appendChild(wrap);
        icons();
        var btn = wrap.querySelector('#revealPredictions');
        var out = wrap.querySelector('#postEmergencyResults');
        btn.addEventListener('click', function () {
          injectPredictions(out, preds);
          wrap.querySelector('.post-emergency__note').remove();
          btn.remove();
        });
      }
      return;
    }
    var preds = data.predictions || [];
    if (!preds.length) { region.innerHTML = ''; return; }
    injectPredictions(region, preds);
  }

  function predictionsHtml(preds) {
    var rows = preds.map(function (p) {
      var pct = Math.max(0, Math.min(100, p.confidence));
      return '' +
        '<div class="pred">' +
          '<div class="pred__row">' +
            '<span class="pred__name">' + escapeHtml(p.disease.trim()) + '</span>' +
            '<span class="pred__pct">' + Math.round(pct) + '%</span>' +
          '</div>' +
          '<div class="pred__bar"><div class="pred__fill" data-width="' + pct + '"></div></div>' +
        '</div>';
    }).join('');
    return '' +
      '<div class="results">' +
        '<h2 class="results__title">Top suggestions</h2>' +
        '<div class="pred-list">' + rows + '</div>' +
        '<p class="results__framing">These suggestions are starting points for a conversation ' +
        'with your doctor, not a diagnosis.</p>' +
      '</div>';
  }

  function emergencyHtml(em) {
    var resources = (em.resources || []).map(function (r) {
      return '<li><span class="res-label">' + escapeHtml(r.label) + '</span>' +
             '<span class="res-value">' + escapeHtml(r.value) + '</span></li>';
    }).join('');
    var matched = (em.matchedSymptoms || []).map(function (m) { return cleanLabel(m); }).join(', ');
    return '' +
      '<div class="banner banner--danger emergency">' +
        '<div class="emergency__head"><i data-lucide="alert-triangle"></i>' +
          '<h2>' + escapeHtml(em.title || 'Possible medical emergency') + '</h2></div>' +
        '<p>' + escapeHtml(em.message || '') + '</p>' +
        '<ul class="resources">' + resources + '</ul>' +
        (matched ? '<p class="emergency__matched">Symptoms noted: ' + escapeHtml(matched) + '</p>' : '') +
        '<p class="emergency__framing">' + escapeHtml(em.note || '') + '</p>' +
      '</div>';
  }

  // ---- Resolve episode ----------------------------------------------------
  function initResolve() {
    var btn = document.getElementById('resolveBtn');
    if (!btn) return;
    btn.addEventListener('click', function () {
      if (!window.confirm('Mark this issue as resolved?')) return;
      btn.disabled = true;
      fetch(btn.getAttribute('data-endpoint'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      })
        .then(function (r) { return r.json(); })
        .then(function (d) { window.location = d.redirect || '/episodes'; })
        .catch(function () {
          btn.disabled = false;
          showToast({ title: 'Could not resolve', msg: 'Please try again.', autoDismiss: 4000 });
        });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initTheme();
    initSidebar();
    initChecker();
    initResolve();
    icons();
  });
})();
