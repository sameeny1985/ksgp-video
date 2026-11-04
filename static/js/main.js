// KSGP Video - Main JS
document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss alerts after 5s
    document.querySelectorAll('.alert-dismissible').forEach(function (el) {
        setTimeout(function () {
            var btn = el.querySelector('.btn-close');
            if (btn) btn.click();
        }, 5000);
    });

    // Confirm dangerous actions
    document.querySelectorAll('[data-confirm]').forEach(function (el) {
        el.addEventListener('click', function (e) {
            if (!confirm(el.getAttribute('data-confirm'))) {
                e.preventDefault();
            }
        });
    });
});

// Simple cookie consent banner
(function() {
  if (localStorage.getItem('ksgp_cookie_ok')) return;
  var bar = document.createElement('div');
  bar.id = 'cookie-bar';
  bar.style.cssText = 'position:fixed;bottom:0;left:0;right:0;background:#1e1b4b;color:#fff;padding:12px 16px;z-index:9999;display:flex;justify-content:space-between;align-items:center;gap:12px;font-size:14px;';
  bar.innerHTML = '<span>We use cookies for essential site functions and preferences. <a href="/cookies/" style="color:#fbbf24">Learn more</a></span><button id="cookie-ok" style="background:#f59e0b;border:0;padding:6px 14px;border-radius:6px;cursor:pointer;font-weight:600">OK</button>';
  document.body.appendChild(bar);
  document.getElementById('cookie-ok').onclick = function() {
    localStorage.setItem('ksgp_cookie_ok', '1');
    bar.remove();
  };
})();
