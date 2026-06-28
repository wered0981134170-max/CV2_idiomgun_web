// ═══════════════════════════════════════════════════════════
// Game 主控 + 組字模式（compose 與 Game 共享私有狀態，故同檔）
// 狀態機：start → play → result → (play | final)
// ═══════════════════════════════════════════════════════════
const Game = (() => {

  // ── 遊戲狀態 ─────────────────────────────────────────────
  let state             = 'start';
  let currentQ          = null;
  let questionsAnswered = 0;
  let actionLock        = false;
  let proceedLock       = false;
  let autoNextTimer     = null;
  let startHover        = null;
  let resultHover       = null;
  let resultHoverTime   = HOVER_TIME;
  let fh                = null;
  let gameStartTime     = 0;
  let allQuestions      = [];
  let score             = 0;

  // ── 組字模式狀態 ──────────────────────────────────────────
  const composeSt = {
    slots:      [null, null, null, null],
    pool:       [],   // [{ char, inPool }]
    dragChar:   null,
    dragSource: null, // { type:'pool'|'slot', idx }
    answer:     '',
  };

  const g = () => window._gesture || { thumbActive: false, x: 0, y: 0 };

  // ── 幀迴圈 ───────────────────────────────────────────────
  function frame() {
    if (window._detectHands) window._detectHands($('camera-video'));
    const gs = g();
    if      (state === 'start')  doStart(gs);
    else if (state === 'play')   doPlay(gs);
    else if (state === 'result') doResult(gs);
    fh = requestAnimationFrame(frame);
  }

  // ── 開始畫面（懸停難度按鈕 1.5 秒開始） ─────────────────
  function doStart(gs) {
    const diffBtns = Array.from(document.querySelectorAll('.diff-btn')).map(el => {
      const r = el.getBoundingClientRect();
      return { el, grade: el.dataset.grade, mode: el.dataset.mode || 'normal',
               x1: r.left, y1: r.top, x2: r.right, y2: r.bottom };
    });

    let hit = null;
    if (gs.thumbActive) {
      for (let i = 0; i < diffBtns.length; i++) {
        const b = diffBtns[i];
        if (gs.x > b.x1 && gs.x < b.x2 && gs.y > b.y1 && gs.y < b.y2) { hit = i; break; }
      }
    }

    const aim = Aim.update(hit, gs.thumbActive);

    diffBtns.forEach((b, i) => {
      const hov       = (i === hit && gs.thumbActive);
      const prog      = hov ? Aim.getP(i) : 0;
      const isCompose = b.mode === 'compose';
      b.el.style.color = hov ? (isCompose ? 'var(--neon-b)' : 'var(--neon-g)') : 'var(--muted)';
      const ring = b.el.querySelector('.diff-ring');
      if (ring) ring.style.strokeDashoffset = +ring.getAttribute('data-circ') * (1 - prog);
    });

    Cursor.update(gs.x, gs.y, gs.thumbActive, 0);

    if (aim.fired) {
      selectedDifficulty = diffBtns[aim.target].grade;
      selectedMode       = diffBtns[aim.target].mode;
      Aim.reset();
      beginGame();
    }
  }

  // ── 答題畫面 ─────────────────────────────────────────────
  function doPlay(gs) {
    if (!currentQ || actionLock) return;

    if (currentQ.type === 'compose') { updateCompose(gs); return; }

    Timer.update();

    const remain = Timer.remain();
    $('timer-bar').style.width = ((remain / Q_TIME_LIMIT) * 100) + '%';
    $('timer-bar').classList.toggle('urgent', remain <= 5);

    Cursor.update(gs.x, gs.y, gs.thumbActive, 0);
    const boxes = getBoxes();
    const hit   = hitTest(boxes, gs.x, gs.y);
    const aim   = Aim.update(hit, gs.thumbActive);

    boxes.forEach((b, i) => {
      const hov = (i === hit && gs.thumbActive);
      b.el.classList.toggle('hovered', hov);
      const ring = b.el.querySelector('.box-ring');
      if (ring) ring.style.strokeDashoffset = +ring.getAttribute('data-circ') * (1 - (hov ? Aim.getP(i) : 0));
    });

    if (aim.fired) {
      actionLock = true;
      state      = 'result';
      handleAnswer(boxes[aim.target]?.label, aim.target, boxes);
    }
  }

  // ── 結果畫面（手動繼續） ─────────────────────────────────
  function doResult(gs) {
    if (autoNextTimer !== null || proceedLock) return;
    const ring = $('result-ring'), CIRC = 113.1;
    Cursor.update(gs.x, gs.y, gs.thumbActive, 0);
    if (gs.thumbActive) {
      if (!resultHover) resultHover = performance.now();
      const p = Math.min((performance.now() - resultHover) / 1000 / resultHoverTime, 1);
      ring.style.strokeDashoffset = CIRC * (1 - p);
      if (p >= 1) { resultHover = null; proceedNext(); }
    } else {
      resultHover = null;
      ring.style.strokeDashoffset = CIRC;
    }
  }

  // ── 碰撞偵測 ─────────────────────────────────────────────
  function getBoxes() {
    return Array.from(document.querySelectorAll(
      currentQ?.type === 'wrong' ? '.char-box' : '.corner-box'
    )).map(el => {
      const r = el.getBoundingClientRect();
      return { el, label: el.dataset.char, x1: r.left, y1: r.top, x2: r.right, y2: r.bottom };
    });
  }

  function hitTest(boxes, cx, cy) {
    for (let i = 0; i < boxes.length; i++) {
      const b = boxes[i];
      if (cx > b.x1 && cx < b.x2 && cy > b.y1 && cy < b.y2) return i;
    }
    return null;
  }

  // ── 題目渲染 ─────────────────────────────────────────────
  function renderQ(q) {
    $('char-row').innerHTML = $('idiom-template').innerHTML = $('corners').innerHTML = '';
    const tpl = $('idiom-template');
    tpl.style.fontSize = ''; tpl.style.letterSpacing = ''; tpl.style.maxWidth = ''; tpl.style.textAlign = '';

    if (q.type === 'compose') {
      hideGame();
      initCompose(q);
      return;
    }

    hideCompose();
    if (q.type === 'wrong') {
      $('corners').style.display     = 'none';
      $('idiom-template').style.display = 'none';
      $('char-row').style.display    = 'flex';

      ;[...q.display].forEach(ch => {
        const d = document.createElement('div');
        d.className    = 'char-box';
        d.dataset.char = ch;
        d.innerHTML = `<span style="position:relative;z-index:1">${ch}</span>
          <svg style="position:absolute;inset:-10px;width:130px;height:130px;pointer-events:none;overflow:visible" viewBox="0 0 130 130" fill="none">
            <rect x="5" y="5" width="120" height="120" rx="6" stroke="rgba(0,229,160,.12)" stroke-width="4" fill="none"/>
            <rect class="box-ring" x="5" y="5" width="120" height="120" rx="6"
                  stroke="#00e5a0" stroke-width="4" fill="none"
                  data-circ="480" stroke-dasharray="480" stroke-dashoffset="480" stroke-linecap="round"
                  style="transform:rotate(-90deg);transform-origin:65px 65px;
                         filter:drop-shadow(0 0 6px #00e5a0);transition:stroke-dashoffset .05s linear"/>
          </svg>`;
        $('char-row').appendChild(d);
      });

    } else {
      $('char-row').style.display       = 'none';
      $('idiom-template').style.display = '';
      $('corners').style.display        = '';

      $('idiom-template').innerHTML = q.display.replace(/__/g,
        '<span class="blank" style="border-bottom:2px solid var(--neon-b);color:var(--neon-b);text-shadow:var(--glow-b)">＿＿</span>'
      );
      $('idiom-template').style.fontSize     = 'clamp(1.2rem, 2.5vw, 2rem)';
      $('idiom-template').style.letterSpacing = '0.05em';
      $('idiom-template').style.maxWidth     = '60vw';
      $('idiom-template').style.textAlign    = 'center';

      q.options.slice(0, 4).forEach((opt, i) => {
        const d = document.createElement('div');
        d.className = 'corner-box'; d.dataset.char = opt; d.dataset.corner = i;
        d.innerHTML = `<span style="position:relative;z-index:1">${opt}</span>
          <svg style="position:absolute;inset:-10px;width:220px;height:100px;pointer-events:none;overflow:visible" viewBox="0 0 220 100" fill="none">
            <rect x="5" y="5" width="210" height="90" rx="6" stroke="rgba(0,229,160,.12)" stroke-width="3" fill="none"/>
            <rect class="box-ring" x="5" y="5" width="210" height="90" rx="6"
                  stroke="#00e5a0" stroke-width="3" fill="none"
                  data-circ="600" stroke-dasharray="600" stroke-dashoffset="600" stroke-linecap="round"
                  style="transform:rotate(0deg);transform-origin:110px 50px;
                         filter:drop-shadow(0 0 6px #00e5a0);transition:stroke-dashoffset .05s linear"/>
          </svg>`;
        $('corners').appendChild(d);
      });
    }
  }

  // ── 遊戲主流程 ───────────────────────────────────────────
  async function beginGame() {
    const n = selectedMode === 'compose' ? 5 : 10;
    let data;
    try {
      const res = await fetch(`/get_all_questions?grade=${selectedDifficulty}&mode=${selectedMode}&n=${n}`);
      if (!res.ok) throw new Error(res.status);
      data = await res.json();
    } catch (e) {
      const st = $('cam-status');
      if (st) { st.textContent = '⚠ 題目載入失敗，請重整'; st.style.color = 'var(--neon-r)'; }
      return;
    }
    allQuestions = data.questions;
    TOTAL_Q      = allQuestions.length;

    score = 0; questionsAnswered = 0; actionLock = false;
    gameStartTime = Date.now();
    Audio.onStart();
    hide($('screen-start')); hide($('lb-sidebar'));
    show($('hud')); show($('timer-bar-wrap')); show($('hint-text'));
    loadNextQuestion();
  }

  function loadNextQuestion() {
    const idx = questionsAnswered;
    const q   = { ...allQuestions[idx], index: idx };
    currentQ   = q;
    actionLock = false;
    Aim.reset();
    Audio.resetTick();
    $('hud-q').textContent     = `${idx + 1}/${TOTAL_Q}`;
    $('hud-score').textContent = score;
    $('hint-text').textContent = q.hint;
    renderQ(q);

    if (q.type === 'compose') {
      hide($('timer-bar-wrap'));
      hide($('hint-text'));
      showCompose();
    } else {
      show($('timer-bar-wrap'));
      showGame();
      Timer.onExpire(() => {
        if (actionLock) return;
        actionLock = true; state = 'result';
        handleTimeout();
      });
      Timer.onTick(rem => Audio.onTick(rem));
      Timer.start(Q_TIME_LIMIT);
    }

    state = 'play';
    proceedLock = false;
  }

  function handleAnswer(chosen, idx, boxes) {
    Timer.stop();
    const b  = boxes?.[idx];
    const fx = b ? (b.x1 + b.x2) / 2 : innerWidth / 2;
    const fy = b ? (b.y1 + b.y2) / 2 : innerHeight / 2;

    const correct = (chosen === currentQ.answer);
    if (correct) score += 10;

    const d = {
      result:      correct ? 'correct' : 'wrong',
      correct_str: currentQ.correct_char || currentQ.answer,
      meaning:     currentQ.meaning     || '',
      idiom:       currentQ.idiom,
      score,
      explanation: EXPLANATIONS[currentQ.idiom] || currentQ.explanation || '',
    };

    if (correct) { Effects.onCorrect(fx, fy); Audio.onCorrect(); }
    else         { Effects.onWrong(fx, fy);   Audio.onWrong();   }

    questionsAnswered++;
    hideGame(); hideCompose();
    showResultCard(d, false);
  }

  function handleTimeout() {
    Timer.stop();
    Audio.stopTick();
    Effects.onTimeout(innerWidth / 2, innerHeight / 2);
    Audio.onTimeout();

    const d = {
      result:      'timeout',
      correct_str: currentQ.correct_char || currentQ.answer,
      meaning:     currentQ.meaning     || '',
      idiom:       currentQ.idiom,
      score,
      explanation: EXPLANATIONS[currentQ.idiom] || currentQ.explanation || '',
    };

    questionsAnswered++;
    hideGame(); hideCompose();
    showResultCard(d, true);
  }

  // ── 結果卡片 ─────────────────────────────────────────────
  function showResultCard(d, autoNext) {
    $('result-card').className = 'result-card ' + d.result;
    const msgs = {
      correct: ['○ 答對了！', d.meaning || `錯字正是「${d.correct_str}」`, 'correct'],
      wrong:   ['✕ 答錯了',   d.meaning || `正確答案是「${d.correct_str}」`, 'wrong'],
      timeout: ['⏱ 時間到',   d.meaning || `正確答案是「${d.correct_str}」`, 'timeout'],
    };
    const [status, detail, cls] = msgs[d.result] || msgs.timeout;
    $('result-status').textContent = status;
    $('result-status').className   = 'result-status ' + cls;
    $('result-detail').textContent = detail;
    $('result-idiom').textContent  = `成語：${d.idiom}　分數：${d.score}`;

    const expEl = $('result-explanation'), expText = $('explanation-text');
    if ((d.result === 'wrong' || d.result === 'timeout') && d.explanation) {
      expText.textContent = d.explanation; show(expEl);
    } else {
      hide(expEl);
    }

    resultHoverTime = (d.result === 'wrong') ? 5.0 : HOVER_TIME;

    if (autoNext) {
      hide($('result-next')); hide($('result-ring-wrap'));
      show($('result-auto-hint'));
      $('result-auto-hint').textContent = '2 秒後自動繼續...';
      autoNextTimer = setTimeout(() => { autoNextTimer = null; proceedNext(); }, 2000);
    } else {
      const secLabel = resultHoverTime === 5.0 ? '5' : '1.5';
      $('result-next').textContent = `▶ 伸出食指 ${secLabel} 秒繼續`;
      show($('result-next'));
      $('result-ring-wrap').style.display = 'flex';
      hide($('result-auto-hint'));
      $('result-ring').style.strokeDashoffset = '113.1';
      resultHover = null;
    }
    show($('screen-result'));
  }

  async function proceedNext() {
    if (proceedLock) return;
    proceedLock = true;
    if (autoNextTimer) { clearTimeout(autoNextTimer); autoNextTimer = null; }
    hide($('screen-result'));
    resultHover = null;
    if (questionsAnswered >= TOTAL_Q) { showFinal(score); return; }
    loadNextQuestion();
  }

  // ── 結算 ─────────────────────────────────────────────────
  function showFinal(score) {
    state = 'final'; proceedLock = false;
    if (autoNextTimer) { clearTimeout(autoNextTimer); autoNextTimer = null; }
    hideGame();
    hide($('hud')); hide($('timer-bar-wrap')); hide($('hint-text')); hide($('screen-result'));
    hide($('lb-sidebar'));
    show($('screen-final'));
    Audio.onFinish();

    const durationSec = Math.round((Date.now() - gameStartTime) / 1000);
    const mm = String(Math.floor(durationSec / 60)).padStart(2, '0');
    const ss = String(durationSec % 60).padStart(2, '0');

    $('final-score').textContent = `${score} / ${TOTAL_Q * 10}`;
    $('final-rank').textContent  =
      score >= TOTAL_Q * 9 ? '🏆 成語達人' :
      score >= TOTAL_Q * 7 ? '⭐ 表現良好' :
      score >= TOTAL_Q * 5 ? '💪 繼續加油' : '📚 多多練習';

    const timeEl = $('final-duration');
    if (timeEl) timeEl.textContent = `⏱ 遊戲時間：${mm}:${ss}`;

    const playerName = Auth.isIdentified()
      ? Auth.getStudent().name
      : ($('player-name')?.value || '').trim() || '匿名';
    fetch('/leaderboard', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: playerName, score, total: TOTAL_Q * 10, duration: durationSec }),
    })
    .then(r => r.json())
    .then(saved => loadFinalLeaderboard(score, saved?.entry?.id))
    .catch(()  => loadFinalLeaderboard(score, null));
  }

  // ── 積分榜 ───────────────────────────────────────────────
  async function loadFinalLeaderboard(myScore, myId) {
    const listEl = $('lb-final-list');
    try {
      const rows = await (await fetch('/leaderboard')).json();
      if (!rows.length) { listEl.innerHTML = '<div style="color:var(--muted);padding:8px 0">尚無紀錄</div>'; return; }
      const medals = ['🥇', '🥈', '🥉'];
      let myRank = -1;
      rows.forEach((r, i) => { if (myId && r.id === myId) myRank = i; });
      if (myRank === -1) myRank = rows.findIndex(r => r.score === myScore);
      listEl.innerHTML = rows.map((r, i) => {
        const isMe     = (i === myRank);
        const dur      = r.duration_fmt || '--:--';
        const fullName = r.class_name ? `${r.class_name} ${r.seat_no}號 ${r.name}` : r.name;
        return `<div class="lb-row-final ${i < 3 ? 'lb-top' : ''} ${isMe ? 'lb-me' : ''}">
          <span class="lb-rank">${medals[i] || ('#' + r.rank)}</span>
          <span class="lb-name">${fullName}${isMe ? ' ◀ 你' : ''}</span>
          <span class="lb-score-final">${r.score}</span>
          <span style="font-family:var(--font-mono);font-size:.7rem;color:var(--muted);white-space:nowrap">⏱${dur}</span>
        </div>`;
      }).join('');
    } catch (e) {
      listEl.innerHTML = '<div style="color:var(--neon-r);font-size:.75rem">無法載入</div>';
    }
  }

  async function loadSidebarLeaderboard() {
    const listEl = $('lb-sidebar-list');
    show($('lb-sidebar'));
    try {
      const rows = await (await fetch('/leaderboard')).json();
      if (!rows.length) {
        listEl.innerHTML = '<div style="font-family:var(--font-mono);font-size:.65rem;color:var(--muted);text-align:center;padding:6px 0">尚無紀錄</div>';
        return;
      }
      const medals = ['🥇', '🥈', '🥉'];
      listEl.innerHTML = rows.map((r, i) => {
        const shortName = r.seat_no ? `${r.seat_no}號 ${r.name}` : r.name;
        return `<div class="lb-row-side ${i < 3 ? 'lb-top-side' : ''}">
          <span class="lb-rank-side">${medals[i] || r.rank}</span>
          <span class="lb-name-side">${shortName}</span>
          <span class="lb-score-side">${r.score}</span>
        </div>`;
      }).join('');
    } catch (e) {
      listEl.innerHTML = '<div style="font-size:.65rem;color:var(--neon-r)">無法載入</div>';
    }
  }

  // ── 組字模式 ─────────────────────────────────────────────
  function initCompose(q) {
    composeSt.slots      = [null, null, null, null];
    composeSt.pool       = q.options.map(c => ({ char: c, inPool: true }));
    composeSt.dragChar   = null;
    composeSt.dragSource = null;
    composeSt.answer     = q.answer;

    $('compose-hint').textContent = q.display;
    renderComposeSlots();
    renderComposePool();
    $('compose-done-wrap').style.visibility = 'hidden';
    $('compose-drag').style.display         = 'none';
  }

  function renderComposeSlots() {
    const c = $('compose-slots');
    c.innerHTML = '';
    for (let i = 0; i < 4; i++) {
      const char = composeSt.slots[i] || '';
      const d = document.createElement('div');
      d.className = 'compose-slot';
      d.dataset.slotIdx = i;
      d.style.cssText = [
        'position:relative','width:72px','height:72px',
        'display:flex','align-items:center','justify-content:center',
        "font-family:var(--font-main)",'font-size:2.2rem',
        'color:var(--neon-g)','background:rgba(8,16,28,0.88)',
        'border:2px solid rgba(0,229,160,0.22)','border-radius:6px',
        'transition:border-color .15s',
      ].join(';');
      d.innerHTML = `<span style="position:relative;z-index:1">${char}</span>
        <svg style="position:absolute;inset:-8px;width:88px;height:88px;pointer-events:none;overflow:visible" viewBox="0 0 88 88" fill="none">
          <rect x="4" y="4" width="80" height="80" rx="6" stroke="rgba(0,229,160,.1)" stroke-width="3" fill="none"/>
          <rect class="slot-ring" x="4" y="4" width="80" height="80" rx="6"
                stroke="#00e5a0" stroke-width="3" fill="none"
                data-circ="320" stroke-dasharray="320" stroke-dashoffset="320"
                stroke-linecap="round"
                style="transform:rotate(-90deg);transform-origin:44px 44px;
                       filter:drop-shadow(0 0 6px #00e5a0);
                       transition:stroke-dashoffset .05s linear"/>
        </svg>`;
      c.appendChild(d);
    }
  }

  function renderComposePool() {
    const c = $('compose-pool');
    c.innerHTML = '';
    composeSt.pool.forEach((item, i) => {
      if (!item.inPool) return;
      const d = document.createElement('div');
      d.className = 'pool-char';
      d.dataset.poolIdx = i;
      d.style.cssText = [
        'position:relative','width:60px','height:60px',
        'display:flex','align-items:center','justify-content:center',
        "font-family:var(--font-main)",'font-size:1.9rem',
        'color:var(--text)','background:rgba(8,16,28,0.88)',
        'border:1px solid rgba(0,229,160,0.2)','border-radius:6px',
        'transition:border-color .15s',
      ].join(';');
      d.innerHTML = `<span style="position:relative;z-index:1">${item.char}</span>
        <svg style="position:absolute;inset:-6px;width:72px;height:72px;pointer-events:none;overflow:visible" viewBox="0 0 72 72" fill="none">
          <rect x="4" y="4" width="64" height="64" rx="6" stroke="rgba(0,229,160,.1)" stroke-width="3" fill="none"/>
          <rect class="pool-ring" x="4" y="4" width="64" height="64" rx="6"
                stroke="#00e5a0" stroke-width="3" fill="none"
                data-circ="256" stroke-dasharray="256" stroke-dashoffset="256"
                stroke-linecap="round"
                style="transform:rotate(-90deg);transform-origin:36px 36px;
                       filter:drop-shadow(0 0 6px #00e5a0);
                       transition:stroke-dashoffset .05s linear"/>
        </svg>`;
      c.appendChild(d);
    });
  }

  function updateCompose(gs) {
    const isDragging = composeSt.dragChar !== null;
    const targets    = [];

    if (!isDragging) {
      document.querySelectorAll('.pool-char').forEach(el => {
        const r = el.getBoundingClientRect();
        targets.push({ type: 'pool', idx: +el.dataset.poolIdx, el,
                       x1: r.left, y1: r.top, x2: r.right, y2: r.bottom });
      });
      document.querySelectorAll('.compose-slot').forEach(el => {
        const i = +el.dataset.slotIdx;
        if (composeSt.slots[i] !== null) {
          const r = el.getBoundingClientRect();
          targets.push({ type: 'slot-remove', idx: i, el,
                         x1: r.left, y1: r.top, x2: r.right, y2: r.bottom });
        }
      });
      if (composeSt.slots.every(s => s !== null)) {
        const el = $('compose-done');
        if (el) {
          const r = el.getBoundingClientRect();
          targets.push({ type: 'done', idx: 0, el,
                         x1: r.left, y1: r.top, x2: r.right, y2: r.bottom });
        }
      }
    } else {
      document.querySelectorAll('.compose-slot').forEach(el => {
        const i = +el.dataset.slotIdx;
        if (composeSt.slots[i] === null) {
          const r = el.getBoundingClientRect();
          targets.push({ type: 'slot-place', idx: i, el,
                         x1: r.left, y1: r.top, x2: r.right, y2: r.bottom });
        }
      });
    }

    let hit = null;
    if (gs.thumbActive) {
      for (let i = 0; i < targets.length; i++) {
        const t = targets[i];
        if (gs.x >= t.x1 && gs.x <= t.x2 && gs.y >= t.y1 && gs.y <= t.y2) { hit = i; break; }
      }
    }

    const aim = Aim.update(hit, gs.thumbActive);

    targets.forEach((t, i) => {
      const hov  = (i === hit && gs.thumbActive);
      const prog = hov ? Aim.getP(i) : 0;
      const ring = t.el.querySelector('.slot-ring, .pool-ring, .compose-done-ring');
      if (ring) ring.style.strokeDashoffset = +ring.getAttribute('data-circ') * (1 - prog);
      t.el.style.borderColor = hov ? 'var(--neon-g)' : '';
    });

    const dragEl = $('compose-drag');
    if (isDragging) {
      dragEl.style.display  = 'flex';
      dragEl.style.left     = gs.x + 'px';
      dragEl.style.top      = gs.y + 'px';
      dragEl.textContent    = composeSt.dragChar;
    } else {
      dragEl.style.display = 'none';
    }

    Cursor.update(gs.x, gs.y, gs.thumbActive, 0);
    if (aim.fired) handleComposeFire(targets[aim.target]);
  }

  function handleComposeFire(target) {
    if (target.type === 'pool') {
      composeSt.dragChar   = composeSt.pool[target.idx].char;
      composeSt.dragSource = { type: 'pool', idx: target.idx };
      composeSt.pool[target.idx].inPool = false;
      renderComposePool();
      Aim.reset();

    } else if (target.type === 'slot-place') {
      composeSt.slots[target.idx] = composeSt.dragChar;
      composeSt.dragChar   = null;
      composeSt.dragSource = null;
      $('compose-drag').style.display = 'none';
      renderComposeSlots();
      checkComposeComplete();
      Aim.reset();

    } else if (target.type === 'slot-remove') {
      const removed = composeSt.slots[target.idx];
      composeSt.slots[target.idx] = null;
      const item = composeSt.pool.find(p => p.char === removed && !p.inPool);
      if (item) item.inPool = true;
      renderComposeSlots();
      renderComposePool();
      checkComposeComplete();
      Aim.reset();

    } else if (target.type === 'done') {
      actionLock = true; state = 'result';
      const assembled = composeSt.slots.join('');
      const correct   = assembled === composeSt.answer;
      if (correct) { score += 10; Effects.onCorrect(innerWidth / 2, innerHeight / 2); Audio.onCorrect(); }
      else         {              Effects.onWrong(innerWidth / 2, innerHeight / 2);   Audio.onWrong();   }
      questionsAnswered++;
      hideCompose();
      showResultCard({
        result:      correct ? 'correct' : 'wrong',
        correct_str: composeSt.answer,
        meaning:     currentQ.meaning || '',
        idiom:       currentQ.idiom,
        score,
        explanation: EXPLANATIONS[currentQ.idiom] || currentQ.explanation || '',
      }, false);
    }
  }

  function checkComposeComplete() {
    const done = composeSt.slots.every(s => s !== null);
    $('compose-done-wrap').style.visibility = done ? 'visible' : 'hidden';
  }

  // ── 重置 / 初始化 ─────────────────────────────────────────
  async function reset() {
    cancelAnimationFrame(fh);
    if (autoNextTimer) { clearTimeout(autoNextTimer); autoNextTimer = null; }
    Timer.stop();
    state = 'start'; currentQ = null;
    questionsAnswered = 0; actionLock = false; proceedLock = false;
    allQuestions = []; score = 0; gameStartTime = 0;
    startHover = null; resultHover = null;
    selectedMode = 'normal';
    composeSt.slots = [null, null, null, null]; composeSt.pool = [];
    composeSt.dragChar = null; composeSt.dragSource = null;
    Aim.reset(); Audio.resetTick();
    hide($('screen-final')); hide($('screen-result'));
    hideGame(); hideCompose();
    hide($('hud')); hide($('timer-bar-wrap')); hide($('hint-text'));
    show($('screen-start'));
    loadSidebarLeaderboard();
    init();
  }

  function init() { fh = requestAnimationFrame(frame); }
  return { reset, init, loadSidebarLeaderboard };
})();
