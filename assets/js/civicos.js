// ── Page routing ──────────────────────────────

// ── Scroll animations ─────────────────────────
function observeAnimations() {
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('vis');
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.08 });

  document.querySelectorAll('.page.active .fi, .fi').forEach(el => {
    if (!el.classList.contains('vis')) io.observe(el);
  });

  // Immediately reveal elements already in viewport on load
  document.querySelectorAll('.fi').forEach(el => {
    const rect = el.getBoundingClientRect();
    if (rect.top < window.innerHeight) {
      el.classList.add('vis');
    }
  });
}

// ── FAQ accordion ─────────────────────────────
function toggleFaq(el) {
  const item = el.closest('.faq-item');
  const wasOpen = item.classList.contains('open');
  // Close all
  document.querySelectorAll('.faq-item.open').forEach(i => i.classList.remove('open'));
  // Open if wasn't open
  if (!wasOpen) item.classList.add('open');
}

// ── Governance doc accordion + layer tabs ─────
function toggleGovDoc(header) {
  const row = header.closest('.gov-doc-row');
  const wasOpen = row.classList.contains('open');
  document.querySelectorAll('.gov-doc-row.open').forEach(r => r.classList.remove('open'));
  if (!wasOpen) {
    row.classList.add('open');
    const firstTab = row.querySelector('.gov-layer-tab');
    if (firstTab && !firstTab.classList.contains('active')) switchGovLayer(firstTab);
  }
}

function switchGovLayer(tab) {
  const body = tab.closest('.gov-doc-body');
  body.querySelectorAll('.gov-layer-tab').forEach(t => t.classList.remove('active'));
  body.querySelectorAll('.gov-layer-panel').forEach(p => p.classList.remove('active'));
  tab.classList.add('active');
  const target = body.querySelector('#' + tab.dataset.target);
  if (target) target.classList.add('active');
}

// ── Letter drill-down ─────────────────────────



window.addEventListener('load', () => {
  document.querySelectorAll('.au').forEach(el => {
    el.style.animationPlayState = 'running';
  });
  observeAnimations();
});

// ── Also animate on scroll ─────────────────────
window.addEventListener('scroll', () => {
  document.querySelectorAll('.page.active .fi:not(.vis)').forEach(el => {
    const rect = el.getBoundingClientRect();
    if (rect.top < window.innerHeight * 0.92) el.classList.add('vis');
  });
}, { passive: true });

// Init
observeAnimations();
