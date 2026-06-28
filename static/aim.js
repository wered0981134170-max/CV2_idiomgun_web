// ── Aim 模組：秒準判定（懸停 HOVER_TIME 秒後觸發） ─────────
const Aim = (() => {
  let cur = null, t0 = null, prog = 0;

  function update(id, active) {
    if (!active || id === null) { cur = null; t0 = null; prog = 0; return { fired: false }; }
    if (id !== cur) { cur = id; t0 = performance.now(); prog = 0; }
    prog = Math.min((performance.now() - t0) / 1000 / HOVER_TIME, 1);
    if (prog >= 1) {
      const c = cur; cur = null; t0 = null; prog = 0;
      return { fired: true, target: c };
    }
    return { fired: false };
  }

  function reset()  { cur = null; t0 = null; prog = 0; }
  function getP(id) { return id === cur ? prog : 0; }

  return { update, reset, getP };
})();
