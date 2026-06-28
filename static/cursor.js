// ── 游標模組：管理準心 SVG 的位置與環形進度 ─────────────────
const Cursor = (() => {
  const el = $('cursor'), ring = $('cursor-ring'), CIRC = 138.23;

  function update(x, y, active, prog = 0) {
    el.style.left = x + 'px';
    el.style.top  = y + 'px';
    if (active) {
      el.classList.remove('hidden');
      ring.style.strokeDashoffset = CIRC * (1 - prog);
    } else {
      el.classList.add('hidden');
      ring.style.strokeDashoffset = CIRC;
    }
  }

  return { update };
})();
