/* Daasa Saahitya — Tab switcher */
(function () {
  'use strict';

  function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const panels  = document.querySelectorAll('.lang-panel');
    if (!tabBtns.length) return;

    // Restore last chosen language from localStorage
    const saved = localStorage.getItem('ds-lang');

    tabBtns.forEach(function (btn) {
      const target = btn.dataset.target;

      // Restore saved tab
      if (saved && target === saved) {
        tabBtns.forEach(b => b.classList.remove('active'));
        panels.forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        const panel = document.getElementById('panel-' + target);
        if (panel) panel.classList.add('active');
      }

      btn.addEventListener('click', function () {
        tabBtns.forEach(b => b.classList.remove('active'));
        panels.forEach(p => p.classList.remove('active'));

        btn.classList.add('active');
        const panel = document.getElementById('panel-' + target);
        if (panel) panel.classList.add('active');

        try { localStorage.setItem('ds-lang', target); } catch(e) {}
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTabs);
  } else {
    initTabs();
  }
})();
