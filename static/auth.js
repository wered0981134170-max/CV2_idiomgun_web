/* auth.js  ── 學生身分識別模組（班級 + 座號 + 姓名） */

const Auth = (() => {
  let _student = null;   // null | { class_name, seat_no, name, best }

  const $ = id => document.getElementById(id);

  // ── 初始化：從 /auth/me 還原 session 狀態 ─────────────────
  async function init() {
    try {
      const res  = await fetch('/auth/me');
      const data = await res.json();
      if (data.logged_in) {
        _student = { class_name: data.class_name, seat_no: data.seat_no,
                     name: data.name, best: data.best };
        _applyIdentified();
      } else {
        _applyGuest();
      }
    } catch (e) {
      _applyGuest();
    }
  }

  // ── UI 切換 ───────────────────────────────────────────────
  function _applyIdentified() {
    const guestEl  = $('guest-area');
    const loggedEl = $('logged-in-area');
    if (guestEl)  guestEl.style.display  = 'none';
    if (loggedEl) loggedEl.style.display = 'flex';

    const nameEl = $('logged-in-name');
    if (nameEl) nameEl.textContent =
      `${_student.class_name} ${_student.seat_no}號 ${_student.name}`;

    const bestEl = $('logged-in-best');
    if (bestEl) {
      bestEl.textContent = _student.best
        ? `最高 ${_student.best.score} 分　⏱ ${_student.best.duration_fmt}`
        : '尚無紀錄';
    }
  }

  function _applyGuest() {
    const guestEl  = $('guest-area');
    const loggedEl = $('logged-in-area');
    if (guestEl)  guestEl.style.display  = 'flex';
    if (loggedEl) loggedEl.style.display = 'none';
  }

  // ── Modal ─────────────────────────────────────────────────
  function openModal() {
    $('auth-error').textContent    = '';
    $('auth-class').value          = '';
    $('auth-seat').value           = '';
    $('auth-name').value           = '';
    $('auth-modal').style.display  = 'flex';
    setTimeout(() => $('auth-class').focus(), 50);
  }

  function closeModal() {
    $('auth-modal').style.display = 'none';
  }

  async function _submit() {
    const class_name = ($('auth-class').value || '').trim();
    const seat_no    = ($('auth-seat').value  || '').trim();
    const name       = ($('auth-name').value  || '').trim();
    const errEl      = $('auth-error');
    errEl.textContent = '';

    if (!class_name || !seat_no || !name) {
      errEl.textContent = '請填寫所有欄位';
      return;
    }

    try {
      const res  = await fetch('/auth/login', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ class_name, seat_no: Number(seat_no), name }),
      });
      const data = await res.json();
      if (data.ok) {
        _student = { class_name: data.class_name, seat_no: data.seat_no,
                     name: data.name, best: data.best };
        _applyIdentified();
        closeModal();
      } else {
        errEl.textContent = data.error || '輸入有誤，請重試';
      }
    } catch (e) {
      errEl.textContent = '網路錯誤，請稍後再試';
    }
  }

  async function logout() {
    await fetch('/auth/logout', { method: 'POST' });
    _student = null;
    _applyGuest();
  }

  function getStudent()  { return _student; }
  function isIdentified(){ return _student !== null; }

  // ── 綁定 DOM 事件 ─────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', () => {
    const btnIdentify = $('btn-identify');
    const btnLogout   = $('btn-logout');
    const closeBtn    = $('auth-close');
    const submitBtn   = $('auth-submit');
    const nameInput   = $('auth-name');
    const modal       = $('auth-modal');

    if (btnIdentify) btnIdentify.addEventListener('click', openModal);
    if (btnLogout)   btnLogout.addEventListener('click', logout);
    if (closeBtn)    closeBtn.addEventListener('click',  closeModal);
    if (submitBtn)   submitBtn.addEventListener('click', _submit);
    if (nameInput)   nameInput.addEventListener('keydown', e => { if (e.key === 'Enter') _submit(); });
    if (modal)       modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });
  });

  return { init, logout, getStudent, isIdentified };
})();
