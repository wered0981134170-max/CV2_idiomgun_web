// ── Timer 模組：集中管理每題倒數計時 ────────────────────────
const Timer = (() => {
  let endTime     = 0;
  let running     = false;
  let expireFired = false;
  let _onExpire   = null;
  let _onTick     = null;

  function start(seconds) {
    endTime     = performance.now() + seconds * 1000;
    running     = true;
    expireFired = false;
  }

  function stop() {
    running     = false;
    expireFired = true;   // 停止後不再觸發 expire
  }

  function remain() {
    if (!running) return 0;
    return Math.max(0, (endTime - performance.now()) / 1000);
  }

  // 每幀由 doPlay 呼叫一次
  function update() {
    if (!running) return;
    const r = remain();
    if (_onTick && r <= 5 && r > 0) _onTick(r);
    if (r <= 0 && !expireFired) {
      expireFired = true;
      running     = false;
      if (_onExpire) _onExpire();
    }
  }

  function onExpire(fn) { _onExpire = fn; }
  function onTick(fn)   { _onTick   = fn; }

  return { start, stop, remain, update, onExpire, onTick };
})();
