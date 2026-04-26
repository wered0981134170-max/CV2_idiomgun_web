/* effects.js  ── 射擊動畫 & 視覺特效 */

const Effects = (() => {
  const layer = document.getElementById('effects-layer');
  const canvas = document.createElement('canvas');
  canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;';
  layer.appendChild(canvas);
  const ctx = canvas.getContext('2d');

  let W, H;
  const resize = () => {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  };
  resize();
  window.addEventListener('resize', resize);

  // ── 粒子池 ────────────────────────────────────────────
  const particles = [];

  class Particle {
    constructor(x, y, color, vx, vy, life, size, type = 'dot') {
      this.x = x; this.y = y;
      this.vx = vx; this.vy = vy;
      this.life = life; this.maxLife = life;
      this.size = size; this.color = color;
      this.type = type;
      this.alpha = 1;
    }

    update(dt) {
      this.x  += this.vx * dt;
      this.y  += this.vy * dt;
      this.vy += 120 * dt;
      this.life -= dt;
      this.alpha = Math.max(0, this.life / this.maxLife);
    }

    draw(ctx) {
      ctx.save();
      ctx.globalAlpha = this.alpha;
      ctx.fillStyle   = this.color;
      if (this.type === 'square') {
        ctx.fillRect(this.x - this.size/2, this.y - this.size/2, this.size, this.size);
      } else if (this.type === 'line') {
        ctx.strokeStyle = this.color;
        ctx.lineWidth   = this.size;
        ctx.beginPath();
        ctx.moveTo(this.x, this.y);
        ctx.lineTo(this.x - this.vx * 0.06, this.y - this.vy * 0.06);
        ctx.stroke();
      } else {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI*2);
        ctx.fill();
      }
      ctx.restore();
    }

    get dead() { return this.life <= 0; }
  }

  // ── 局部爆炸 ──────────────────────────────────────────
  function burst(x, y, color, count = 28) {
    for (let i = 0; i < count; i++) {
      const angle = (Math.PI * 2 * i) / count + (Math.random() - .5) * .4;
      const speed = 140 + Math.random() * 220;
      const type  = Math.random() < .3 ? 'square' : 'dot';
      particles.push(new Particle(
        x, y, color,
        Math.cos(angle) * speed,
        Math.sin(angle) * speed - 60,
        .5 + Math.random() * .4,
        2 + Math.random() * 4,
        type
      ));
    }
    for (let i = 0; i < 6; i++) {
      const angle = (Math.PI * 2 * i) / 6 + Math.random();
      const speed = 300 + Math.random() * 180;
      particles.push(new Particle(
        x, y, color,
        Math.cos(angle) * speed,
        Math.sin(angle) * speed,
        .25, 1.5 + Math.random() * 2, 'line'
      ));
    }
  }

  // ── 全畫面爆炸（答對用）─────────────────────────────
  const COLORS = ['#00e5a0','#ffd700','#00c8ff','#ffffff','#ff9940','#a0ffcc'];

  function fullscreenBurst(count = 140) {
    // 從四邊射向中心
    for (let i = 0; i < count; i++) {
      const edge = Math.floor(Math.random() * 4);
      let sx, sy;
      if      (edge === 0) { sx = Math.random() * W; sy = 0; }
      else if (edge === 1) { sx = Math.random() * W; sy = H; }
      else if (edge === 2) { sx = 0;                 sy = Math.random() * H; }
      else                 { sx = W;                 sy = Math.random() * H; }

      const color = COLORS[Math.floor(Math.random() * COLORS.length)];
      const angle = Math.atan2(H/2 - sy, W/2 - sx) + (Math.random() - .5) * 1.2;
      const speed = 300 + Math.random() * 500;
      particles.push(new Particle(
        sx, sy, color,
        Math.cos(angle) * speed,
        Math.sin(angle) * speed,
        .6 + Math.random() * .6,
        3 + Math.random() * 7,
        Math.random() < .35 ? 'square' : 'dot'
      ));
    }
    // 中心向外爆
    for (let i = 0; i < 60; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = 200 + Math.random() * 600;
      const color = COLORS[Math.floor(Math.random() * COLORS.length)];
      particles.push(new Particle(
        W/2, H/2, color,
        Math.cos(angle) * speed,
        Math.sin(angle) * speed - 80,
        .5 + Math.random() * .8,
        2 + Math.random() * 6,
        Math.random() < .3 ? 'square' : 'dot'
      ));
    }
  }

  // ── 畫面震動 ─────────────────────────────────────────
  function shakeScreen(duration = 600) {
    document.body.classList.remove('shake');
    void document.body.offsetWidth;   // 強制 reflow，讓動畫重播
    document.body.classList.add('shake');
    setTimeout(() => document.body.classList.remove('shake'), duration);
  }

  // ── 衝擊波 ───────────────────────────────────────────
  const waves = [];
  function shockwave(x, y, color) {
    waves.push({ x, y, r: 0, life: 1, color, scale: 1 });
  }
  function fullscreenShockwave(color = '#00e5a0') {
    waves.push({ x: W/2, y: H/2, r: 0, life: 1, color, scale: 8 });
  }

  // ── 浮字 ─────────────────────────────────────────────
  const floats = [];
  function floatText(x, y, text, color) {
    floats.push({ x, y, text, color, life: 1.2, vy: -60, alpha: 1 });
  }

  // ── 準線閃光 ─────────────────────────────────────────
  const reticles = [];
  function reticleFlash(x, y, color) {
    reticles.push({ x, y, r: 18, life: .4, color });
  }

  // ── 公開 API ─────────────────────────────────────────
  function onCorrect(x, y) {
    burst(x, y, '#00e5a0', 32);
    burst(x, y, '#ffffff', 10);
    shockwave(x, y, '#00e5a0');
    reticleFlash(x, y, '#00e5a0');
    floatText(x, y - 30, '正確！+10', '#00e5a0');
    // 全畫面慶祝
    fullscreenBurst(140);
    fullscreenShockwave('#00e5a0');
  }

  function onWrong(x, y) {
    burst(x, y, '#ff4466', 24);
    shockwave(x, y, '#ff4466');
    floatText(x, y - 30, '答錯了', '#ff4466');
    reticleFlash(x, y, '#ff4466');
    // 畫面震動
    shakeScreen(600);
  }

  function onTimeout(x, y) {
    burst(x, y, '#00c8ff', 18);
    floatText(x, y - 30, '時間到', '#00c8ff');
    shakeScreen(400);
  }

  // ── 主迴圈 ───────────────────────────────────────────
  let last = performance.now();
  function loop(now) {
    const dt = Math.min((now - last) / 1000, .05);
    last = now;

    ctx.clearRect(0, 0, W, H);

    // 粒子
    for (let i = particles.length - 1; i >= 0; i--) {
      particles[i].update(dt);
      particles[i].draw(ctx);
      if (particles[i].dead) particles.splice(i, 1);
    }

    // 衝擊波
    for (let i = waves.length - 1; i >= 0; i--) {
      const w = waves[i];
      w.r    += 600 * dt * (w.scale || 1);
      w.life -= dt / .5;
      if (w.life <= 0) { waves.splice(i, 1); continue; }
      ctx.save();
      ctx.globalAlpha = Math.max(0, w.life) * 0.5;
      ctx.strokeStyle = w.color;
      ctx.lineWidth   = 3;
      ctx.beginPath();
      ctx.arc(w.x, w.y, w.r, 0, Math.PI*2);
      ctx.stroke();
      ctx.restore();
    }

    // 浮字
    for (let i = floats.length - 1; i >= 0; i--) {
      const f = floats[i];
      f.y    += f.vy * dt;
      f.life -= dt;
      f.alpha = Math.max(0, f.life);
      if (f.life <= 0) { floats.splice(i, 1); continue; }
      ctx.save();
      ctx.globalAlpha = f.alpha;
      ctx.font        = 'bold 20px "Noto Serif TC", serif';
      ctx.fillStyle   = f.color;
      ctx.textAlign   = 'center';
      ctx.shadowColor = f.color;
      ctx.shadowBlur  = 12;
      ctx.fillText(f.text, f.x, f.y);
      ctx.restore();
    }

    // 準線閃光
    for (let i = reticles.length - 1; i >= 0; i--) {
      const re = reticles[i];
      re.r    += 80 * dt;
      re.life -= dt / .4;
      if (re.life <= 0) { reticles.splice(i, 1); continue; }
      const a = Math.max(0, re.life);
      ctx.save();
      ctx.globalAlpha = a;
      ctx.strokeStyle = re.color;
      ctx.lineWidth   = 2;
      const s = re.r * .6;
      ctx.beginPath();
      ctx.moveTo(re.x - s, re.y); ctx.lineTo(re.x + s, re.y);
      ctx.moveTo(re.x, re.y - s); ctx.lineTo(re.x, re.y + s);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(re.x, re.y, re.r, 0, Math.PI*2);
      ctx.stroke();
      ctx.restore();
    }

    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);

  return { onCorrect, onWrong, onTimeout, burst, shockwave, floatText };
})();
