// ═══════════════════════════════════════════════════════════
// 學習顧問室：錯題本（localStorage，依學生身分分開存）+ 畫面
// 操作：滑鼠點擊，或手勢準心懸停 1.5 秒（.adv-hit 元素）
// ═══════════════════════════════════════════════════════════
const Advisor = (() => {

  const TYPE_LABEL = { wrong: '錯別字', compose: '組合題', application: '應用題' };
  const TYPES      = ['wrong', 'compose', 'application'];

  // ── 儲存 ─────────────────────────────────────────────────
  const storeKey = () => {
    const s = (typeof Auth !== 'undefined' && Auth.getStudent) ? Auth.getStudent() : null;
    return 'idiomgun_advisor_v1:' + (s ? `${s.class_name}-${s.seat_no}-${s.name}` : 'guest');
  };

  function load() {
    const empty = { items: {}, stats: { answered: 0, correct: 0, streak: 0, maxStreak: 0,
                                         byType: { wrong: [0, 0], compose: [0, 0], application: [0, 0] } } };
    try {
      const d = JSON.parse(localStorage.getItem(storeKey()));
      return d && d.items && d.stats ? d : empty;
    } catch (e) { return empty; }
  }
  function save() { try { localStorage.setItem(storeKey(), JSON.stringify(db)); } catch (e) {} }

  let db = load();

  const itemKey = (idiom, type) => `${idiom}|${type}`;

  // ── 記錄一次作答（由 Game 在答題／超時時呼叫） ─────────────
  function record(q, d) {
    db = load();
    const ok = d.result === 'correct';
    const st = db.stats;
    st.answered++;
    const bt = st.byType[q.type] || (st.byType[q.type] = [0, 0]);
    bt[0]++;
    if (ok) { st.correct++; bt[1]++; st.streak++; st.maxStreak = Math.max(st.maxStreak, st.streak); }
    else    { st.streak = 0; }

    const key = itemKey(q.idiom, q.type);
    const it  = db.items[key];
    if (ok) {
      if (it) it.mastered = true;           // 之前錯過、這次答對
    } else {
      const base = it || { count: 0, reviewed: false };
      db.items[key] = {
        ...base,
        idiom: q.idiom, type: q.type, display: q.display, options: q.options || [],
        answer: q.answer, correct_str: d.correct_str, chosen: d.chosen || null,
        wrongChar: d.wrongChar || null, meaning: q.meaning || '', teaching: q.teaching || null,
        count: base.count + 1, mastered: false, reviewed: false, last: Date.now(),
      };
    }
    save();
  }

  // ── 狀態 ─────────────────────────────────────────────────
  let filter    = 'all';
  let keyword   = '';
  const open    = new Set();      // 展開的卡片 key
  const covered = new Set();      // 隱藏答案的卡片 key
  const retest  = {};             // key → { picked: [], result: null|true|false }
  let bound     = false;

  const esc = s => String(s ?? '').replace(/[&<>"']/g,
    c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  const items = () => Object.values(db.items).sort((a, b) => b.last - a.last);

  // ── 左側：個人資訊 / 等級 / 成就 ─────────────────────────
  function renderSide() {
    const s  = (typeof Auth !== 'undefined' && Auth.getStudent) ? Auth.getStudent() : null;
    const st = db.stats;
    const mastered = items().filter(i => i.mastered).length;
    const lv = 1 + Math.floor(st.correct / 10);
    const ach = [
      ['成語達人', st.correct,   10, '累計答對'],
      ['滅錯高手', mastered,     5,  '掌握錯題'],
      ['連勝王者', st.maxStreak, 5,  '最高連對'],
    ];
    $('adv-side').innerHTML = `
      <div class="adv-card adv-profile">
        <div class="adv-avatar">${esc((s ? s.name : '訪客')[0])}</div>
        <div class="adv-lv">Lv. ${lv}</div>
        <div class="adv-name">${s ? esc(s.name) : '訪客'}</div>
        <div class="adv-sub">${s ? `${esc(s.class_name)}　${s.seat_no} 號` : '尚未確認身分'}</div>
      </div>
      ${ach.map(([n, v, max, label]) => {
        const done = v >= max;
        return `<div class="adv-card adv-ach ${done ? 'done' : ''}">
          <div class="adv-ach-t">🏆 ${n}${done ? ' ✓' : ''}</div>
          <div class="adv-bar"><i style="width:${Math.min(100, v / max * 100)}%"></i></div>
          <div class="adv-sub">${label} ${Math.min(v, max)}/${max}</div>
        </div>`;
      }).join('')}`;
  }

  // ── 工具列 ───────────────────────────────────────────────
  function renderChips() {
    const list = items();
    const cnt  = t => t === 'all' ? list.length : list.filter(i => i.type === t).length;
    const chips = [['all', '全部'], ['wrong', '❌ 錯別字'], ['compose', '🧩 組合題'], ['application', '📝 應用題']];
    $('adv-chips').innerHTML = chips.map(([t, label]) =>
      `<button class="adv-chip adv-hit ${filter === t ? 'on' : ''}" data-act="filter" data-v="${t}">${label} (${cnt(t)})</button>`
    ).join('');
  }

  // ── 顧問提示 ─────────────────────────────────────────────
  function renderBanner() {
    const st = db.stats, list = items();
    let msg;
    if (!st.answered) {
      msg = '還沒有作答紀錄，先去玩一場遊戲，答錯的題目會自動收進這裡喔！';
    } else if (!list.length) {
      msg = '太棒了！目前沒有錯題，繼續保持！';
    } else {
      // 正確率最低的題型（至少作答 1 題且有錯題）
      const worst = TYPES.filter(t => st.byType[t][0] && list.some(i => i.type === t))
        .sort((a, b) => st.byType[a][1] / st.byType[a][0] - st.byType[b][1] / st.byType[b][0])[0];
      const todo = list.filter(i => !i.mastered);
      if (!todo.length) {
        msg = '所有錯題都已掌握，可以再挑戰一場，看看能不能全對！';
      } else {
        const pick = todo.filter(i => i.type === worst).slice(0, 2).map(i => `「${esc(i.idiom)}」`).join('與')
                  || todo.slice(0, 2).map(i => `「${esc(i.idiom)}」`).join('與');
        const rate = Math.round(st.byType[worst][1] / st.byType[worst][0] * 100);
        msg = `你在【${TYPE_LABEL[worst]}】的正確率是 ${rate}%，建議優先複習 ${pick}。還有 ${todo.length} 題尚未掌握。`;
      }
    }
    $('adv-banner').innerHTML = `💡 <b>顧問小叮嚀</b>　${msg}`;
  }

  // ── 教學內容 ─────────────────────────────────────────────
  function noteFromArr(arr, key) {
    if (!Array.isArray(arr) || !key) return null;
    for (const o of arr) if (o && Object.prototype.hasOwnProperty.call(o, key)) return o[key];
    return null;
  }
  const noteRow = (kind, tag, label, def) => def
    ? `<div class="adv-note ${kind}"><span class="t">${tag}</span><span class="c">${esc(label)}</span><span class="d">${esc(def)}</span></div>` : '';

  function renderTeach(it) {
    const t = it.teaching || {};
    const cs = it.correct_str;
    let h = '';
    if (it.type === 'wrong') {
      const chars = (t.breakdown && t.breakdown.length) ? t.breakdown.map(b => b.char) : [...it.idiom];
      h += `<div class="adv-chars">${chars.map(ch => `<span class="${ch === cs ? 'hl' : ''}">${esc(ch)}</span>`).join('')}</div>`;
      h += noteRow('correct', '正確', cs, t.typos_answer && t.typos_answer[cs]);
      h += noteRow('wrong', '混淆', it.wrongChar, it.wrongChar && t.options_notes && t.options_notes[it.wrongChar]);
    } else if (it.type === 'application') {
      if (t.example) {
        h += `<div class="adv-example">📖 ${esc(t.example).split(esc(cs)).join(`<span class="hl">${esc(cs)}</span>`)}</div>`;
      }
      const opts = it.options.length ? it.options : [cs];
      h += opts.map(o => {
        const ok = o === cs, bad = !ok && o === it.chosen;
        return noteRow(ok ? 'correct' : bad ? 'wrong' : 'other', ok ? '✓ 正確' : bad ? '✕ 你選的' : '其他', o,
          ok ? (noteFromArr(t.application_answers, o) || t.plain || it.meaning) : noteFromArr(t.application_notes, o));
      }).join('');
    } else {
      h += `<div class="adv-chars compose">${[...it.idiom].map((ch, i) => `<span class="${(it.chosen || '')[i] !== cs[i] ? 'bad' : ''}">${esc(ch)}</span>`).join('')}</div>`;
      if (t.plain || it.meaning) h += `<div class="adv-example adv-plain">${esc(t.plain || it.meaning)}</div>`;
      if (t.breakdown && t.breakdown.length) {
        h += `<div class="adv-break">${t.breakdown.map((b, i) => `<div class="${(it.chosen || '')[i] !== cs[i] ? 'hl' : ''}"><b>${esc(b.char)}</b><span>${esc(b.meaning || '')}</span></div>`).join('')}</div>`;
      }
      if (t.example) h += `<div class="adv-example">💬 ${esc(t.example)}</div>`;
    }
    return h;
  }

  // ── 重新測驗 ─────────────────────────────────────────────
  function renderRetest(it, key) {
    const r = retest[key];
    if (!r) return '';
    const btn = (v, extra = '') =>
      `<button class="adv-opt adv-hit ${extra}" data-act="pick" data-k="${esc(key)}" data-v="${esc(v)}">${esc(v)}</button>`;
    let body;
    if (it.type === 'wrong') {
      body = `<div class="adv-q">找出下面成語中的錯字</div><div class="adv-opts big">${[...it.display].map(ch => btn(ch)).join('')}</div>`;
    } else if (it.type === 'application') {
      body = `<div class="adv-q">${esc(it.display).replace(/__/g, '<span class="blank">＿＿</span>')}</div>
              <div class="adv-opts">${it.options.slice(0, 4).map(o => btn(o)).join('')}</div>`;
    } else {
      body = `<div class="adv-q">${esc(it.display)}</div>
              <div class="adv-slots">${[0, 1, 2, 3].map(i => `<span>${esc(r.picked[i] || '')}</span>`).join('')}</div>
              <div class="adv-opts big">${it.options.map((c, i) => btn(c, r.picked.includes(i) ? 'used' : '').replace('data-v=', `data-i="${i}" data-v=`)).join('')}</div>`;
    }
    if (r.result !== null) {
      body += `<div class="adv-res ${r.result ? 'ok' : 'bad'}">${r.result ? '○ 答對了！已標記為「已掌握」' : `✕ 答錯了，正確答案是「${esc(it.correct_str)}」`}</div>`;
    }
    return `<div class="adv-retest">${body}</div>`;
  }

  function onPick(key, v, idx) {
    const it = db.items[key], r = retest[key];
    if (!it || !r || r.result !== null) return;
    let ok;
    if (it.type === 'compose') {
      if (r.picked.includes(idx)) return;
      r.picked.push(idx);
      if (r.picked.length < 4) return;
      ok = r.picked.map(i => it.options[i]).join('') === it.answer;
    } else {
      ok = v === it.answer;
    }
    r.result = ok;
    if (ok) it.mastered = true; else { it.mastered = false; it.count++; }
    save();
  }

  // ── 錯題卡 ───────────────────────────────────────────────
  function renderList() {
    const list = items().filter(i =>
      (filter === 'all' || i.type === filter) && (!keyword || i.idiom.includes(keyword)));
    if (!list.length) {
      $('adv-list').innerHTML = `<div class="adv-empty">${items().length ? '沒有符合的題目' : '🎉 目前沒有錯題'}</div>`;
      return;
    }
    $('adv-list').innerHTML = list.map(it => {
      const key = itemKey(it.idiom, it.type);
      const isOpen = open.has(key), hid = covered.has(key);
      const status = it.mastered ? '已掌握' : it.reviewed ? '已複習' : '未複習';
      const head = (it.type === 'wrong' && it.wrongChar && it.wrongChar !== it.correct_str) ? ['選了', it.wrongChar]
                 : (it.chosen && it.chosen !== it.correct_str) ? ['你選了', it.chosen] : null;
      return `<div class="adv-item ${isOpen ? 'open' : ''}">
        <div class="adv-item-h adv-hit" data-act="toggle" data-k="${esc(key)}">
          <span class="arrow">${isOpen ? '▼' : '▶'}</span>
          <span class="tag ${it.type}">${TYPE_LABEL[it.type]}</span>
          <span class="nm">${esc(it.idiom)}</span>
          <span class="st ${it.mastered ? 'ok' : ''}">錯了 ${it.count} 次 ｜ ${status}</span>
        </div>
        ${isOpen ? `<div class="adv-item-b">
          <div class="adv-cmp">✕ 答錯了：${head ? `${head[0]}「<b class="x">${esc(head[1])}</b>」 ➔ ` : ''}正確答案應為「<b class="y">${esc(it.correct_str)}</b>」</div>
          <div class="adv-ans ${hid ? 'covered' : ''}">${renderTeach(it)}</div>
          <div class="adv-acts">
            <button class="adv-btn adv-hit" data-act="cover" data-k="${esc(key)}">${hid ? '👁️ 顯示答案' : '👁️ 隱藏答案'}</button>
            <button class="adv-btn adv-hit primary" data-act="retest" data-k="${esc(key)}">重新測驗 🔄</button>
          </div>
          ${renderRetest(it, key)}
        </div>` : ''}
      </div>`;
    }).join('');
  }

  function render() {
    const scroll = $('adv-list') ? $('adv-list').scrollTop : 0;
    renderSide(); renderChips(); renderBanner(); renderList();
    $('adv-list').scrollTop = scroll;
  }

  // ── 事件（滑鼠 click 與手勢懸停共用） ────────────────────
  function onAction(el) {
    const act = el.dataset.act, key = el.dataset.k;
    if (act === 'back')   { Game.reset(); return; }
    if (act === 'filter') { filter = el.dataset.v; }
    if (act === 'toggle') {
      if (open.has(key)) open.delete(key);
      else {
        open.add(key);
        const it = db.items[key];
        if (it && !it.reviewed && !it.mastered) { it.reviewed = true; save(); }
      }
    }
    if (act === 'cover')  { covered.has(key) ? covered.delete(key) : covered.add(key); }
    if (act === 'retest') { retest[key] = { picked: [], result: null }; }
    if (act === 'pick')   { onPick(key, el.dataset.v, el.dataset.i === undefined ? null : +el.dataset.i); }
    render();
  }

  function bind() {
    if (bound) return;
    bound = true;
    $('screen-advisor').addEventListener('click', e => {
      const el = e.target.closest('[data-act]');
      if (el) onAction(el);
    });
    $('adv-search').addEventListener('input', e => { keyword = e.target.value.trim(); renderList(); });
  }

  // ── 進入 / 手勢更新 ──────────────────────────────────────
  function enter() {
    bind();
    db = load();
    filter = 'all'; keyword = ''; $('adv-search').value = '';
    open.clear(); covered.clear();
    for (const k in retest) delete retest[k];
    render();
  }

  function update(gs) {
    const els = [], rects = [];
    const listBox = $('adv-list').getBoundingClientRect();
    document.querySelectorAll('#screen-advisor .adv-hit').forEach(el => {
      const r = el.getBoundingClientRect();
      if (!r.width) return;
      // 列表內的元素必須在可視範圍內才能被選
      if (el.closest('#adv-list') && (r.top < listBox.top || r.bottom > listBox.bottom)) return;
      els.push(el); rects.push(r);
    });

    let hit = null;
    if (gs.thumbActive) {
      rects.forEach((r, i) => {
        if (hit === null && gs.x > r.left && gs.x < r.right && gs.y > r.top && gs.y < r.bottom) hit = i;
      });
      // 準心停在列表上下緣：自動捲動
      if (gs.x > listBox.left && gs.x < listBox.right) {
        if (gs.y > listBox.top && gs.y < listBox.top + 50)          $('adv-list').scrollTop -= 8;
        else if (gs.y < listBox.bottom && gs.y > listBox.bottom - 50) $('adv-list').scrollTop += 8;
      }
    }
    const aim = Aim.update(hit, gs.thumbActive);
    els.forEach((el, i) => {
      const on = i === hit && gs.thumbActive;
      el.classList.toggle('hov', on);
      el.style.setProperty('--p', on ? Aim.getP(i) : 0);
    });
    Cursor.update(gs.x, gs.y, gs.thumbActive, 0);
    if (aim.fired) { Aim.reset(); onAction(els[aim.target]); }
  }

  return { record, enter, update };
})();
