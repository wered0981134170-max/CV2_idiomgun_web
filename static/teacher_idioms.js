// teacher_idioms.js  ── 教師成語頁：右側抽屜 + 輸入成語（新成語目前只顯示在頁面，不存檔）
(() => {
  const bank   = JSON.parse(document.getElementById('idiom-data').textContent);
  const LABELS = Object.fromEntries(bank.columns.map(c => [c.grade, c.label]));
  const $      = id => document.getElementById(id);

  const drawer = $('drawer');
  let current  = null;     
  let tab      = 'typo';    

  function el(tag, cls, text) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }

  function chips(list) {
    const box = el('div', 'chips');
    list.forEach(t => box.append(el('span', 'chip', t)));
    return box;
  }

  function addField(dl, term, value) {
    dl.append(el('dt', null, term));
    const dd = el('dd');
    const empty = value == null || value === '' || (Array.isArray(value) && !value.length);
    if (empty)                       dd.append(el('span', 'hint', '尚未填寫'));
    else if (value instanceof Node)  dd.append(value);
    else                             dd.textContent = value;
    dl.append(dd);
  }

  function renderLearning(name) {
    const info = bank.learning[name] || {};
    const dl = $('learning');
    dl.replaceChildren();
    addField(dl, '解釋', info.meaning);
    const chars = (info.breakdown || []).map(b => {
      const row = el('div', 'char-row');
      row.append(el('strong', null, b.char), el('span', null, b.meaning));
      return row;
    });
    const box = el('div', 'char-list');
    box.append(...chars);
    addField(dl, '字義', chars.length ? box : null);
    addField(dl, '例句', info.example);
  }

  function renderQuestion(grade, name) {
    const q  = ((bank.questions[grade] || {})[name] || {})[tab];
    const dl = $('question');
    dl.replaceChildren();
    if (!q) {
      dl.append(el('p', 'hint', '這個難度還沒有這種題目'));
      return;
    }
    const opts = q.options || [];
    if (tab === 'typo') {
      addField(dl, '題目', (q.question || '').replace('_', '＿'));
      addField(dl, '正確字', q.answer);
      addField(dl, '錯字選項', opts.length ? chips(opts) : null);
    } else if (tab === 'compose') {
      addField(dl, '提示', q.question);
      addField(dl, '答案', q.answer);
      addField(dl, `字卡（${opts.length} 個）`, opts.length ? chips(opts) : null);
    } else {
      addField(dl, '句子', q.question);
      addField(dl, '答案', q.answer);
      addField(dl, '選項', opts.length ? chips(opts) : null);
    }
  }

  function renderTabs() {
    document.querySelectorAll('.tabs [role=tab]').forEach(b => {
      const on = b.dataset.tab === tab;
      b.classList.toggle('active', on);
      b.setAttribute('aria-selected', on);
    });
  }

  function openDrawer(btn) {
    if (current) current.classList.remove('selected');
    current = btn;
    btn.classList.add('selected');
    const { grade, idiom } = btn.dataset;
    $('drawer-title').textContent = idiom;
    $('drawer-grade').textContent = LABELS[grade] || '';
    renderLearning(idiom);
    renderTabs();
    renderQuestion(grade, idiom);
    drawer.hidden = false;
    document.body.classList.add('drawer-open');
  }

  function closeDrawer() {
    if (current) current.classList.remove('selected');
    current = null;
    drawer.hidden = true;
    document.body.classList.remove('drawer-open');
  }

  document.querySelector('.bank').addEventListener('click', e => {
    const btn = e.target.closest('.idiom-item');
    if (btn) openDrawer(btn);
  });
  document.querySelector('.tabs').addEventListener('click', e => {
    const b = e.target.closest('[role=tab]');
    if (!b || !current) return;
    tab = b.dataset.tab;
    renderTabs();
    renderQuestion(current.dataset.grade, current.dataset.idiom);
  });
  $('drawer-close').addEventListener('click', closeDrawer);
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && current) closeDrawer(); });

  const addBtn   = $('add-btn');
  const addForm  = $('add-form');
  const addInput = $('add-input');
  const TARGET   = 'elementary_low';

  function syncAddBtn() {
    addBtn.textContent = addInput.value.trim() ? '新增成語' : '輸入成語';
  }

  function addIdiom() {
    const name = addInput.value.trim();
    const list = document.querySelector(`.idiom-list[data-grade="${TARGET}"]`);
    const btn  = el('button', 'idiom-item is-new', name);
    btn.type = 'button';
    btn.dataset.grade = TARGET;
    btn.dataset.idiom = name;
    btn.title = '尚未儲存';
    const li = el('li');
    li.append(btn);
    list.append(li);
    list.parentElement.querySelector('.empty-col')?.remove();
    const count = document.querySelector(`[data-count="${TARGET}"]`);
    count.textContent = `${list.children.length} 個`;

    addInput.value = '';
    addForm.hidden = true;
    syncAddBtn();
    btn.scrollIntoView({ block: 'nearest' });
    openDrawer(btn);
  }

  addBtn.addEventListener('click', () => {
    if (addForm.hidden) {
      addForm.hidden = false;
      addInput.focus();
    } else if (addInput.value.trim()) {
      addIdiom();
    } else {
      addInput.focus();
    }
  });
  addInput.addEventListener('input', syncAddBtn);
  addInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && addInput.value.trim()) { e.preventDefault(); addIdiom(); }
    if (e.key === 'Escape') { addInput.value = ''; addForm.hidden = true; syncAddBtn(); }
  });
})();
