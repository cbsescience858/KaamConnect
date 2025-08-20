// TargetCursor: lightweight, reusable focus helper
// Usage:
// 1) Add data-targetcursor to any input/textarea/select to focus it on page load
// 2) Or keep using the standard autofocus attribute; this will also be respected
// 3) Programmatic: window.TargetCursor.focus('#selector')
(function () {
  function findFirstFocusable() {
    // Priority: [data-targetcursor] first, then [autofocus], then first enabled visible input
    var el = document.querySelector('[data-targetcursor]');
    if (el) return el;
    el = document.querySelector('[autofocus]');
    if (el) return el;
    // Fallback: first visible, enabled input/textarea/select
    var candidates = document.querySelectorAll('input, textarea, select');
    for (var i = 0; i < candidates.length; i++) {
      var c = candidates[i];
      if (!c.disabled && c.offsetParent !== null) return c;
    }
    return null;
  }

  function focusElement(el) {
    if (!el || typeof el.focus !== 'function') return;
    try {
      // Defer to ensure element is painted
      setTimeout(function () {
        el.focus({ preventScroll: true });
        if (typeof el.select === 'function' && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA')) {
          el.select();
        }
      }, 0);
    } catch (_) {
      try { el.focus(); } catch (_) {}
    }
  }

  function focusBySelector(selector) {
    var el = document.querySelector(selector);
    if (el) focusElement(el);
  }

  document.addEventListener('DOMContentLoaded', function () {
    var el = findFirstFocusable();
    focusElement(el);
  });

  // Expose small API
  window.TargetCursor = {
    focus: focusBySelector
  };
})();
