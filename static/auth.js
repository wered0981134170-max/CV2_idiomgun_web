/* auth.js  ── 前端登入系統模組 */

const Auth = (() => {
  let _user = null;   // null | { username, best }

  const $ = id => document.getElementById(id);

  // ── 初始化：從 /auth/me 取得登入狀態 ─────────────────────
  async function init() {
    try {
      const res  = await fetch('/auth/me');
      const data = await res.json();
      if (data.logged_in) {
        _user = { username: data.username, best: data.best };
        _applyLoggedIn();
      } else {
        _applyGuest();
      }
    } catch (e) {
      _applyGuest();
    }
  }

  function _applyLoggedIn() {
    const guestEl  = $('guest-area');
    const loggedEl = $('logged-in-area');
    if (guestEl)  guestEl.style.display  = 'none';
    if (loggedEl) loggedEl.style.display = 'flex';

    const nameEl = $('logged-in-name');
    if (nameEl) nameEl.textContent = _user.username;

    const bestEl = $('logged-in-best');
    if (bestEl) {
      bestEl.textContent = _user.best
        ? `最高 ${_user.best.score} 分　⏱ ${_user.best.duration_fmt}`
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
  let _isRegister = false;

  function openModal(tab) {
    _isRegister = (tab === 'register');
    _switchTab(_isRegister);
    $('auth-error').textContent   = '';
    $('auth-username').value      = '';
    $('auth-password').value      = '';
    $('auth-modal').style.display = 'flex';
    setTimeout(() => $('auth-username').focus(), 50);
  }

  function closeModal() {
    $('auth-modal').style.display = 'none';
  }

  function _switchTab(toRegister) {
    _isRegister = toRegister;
    $('tab-login').classList.toggle('auth-tab-active',    !toRegister);
    $('tab-register').classList.toggle('auth-tab-active',  toRegister);
    $('auth-submit').textContent = toRegister ? '註冊帳號' : '登入';
  }

  async function _submit() {
    const username = ($('auth-username').value || '').trim();
    const password = ($('auth-password').value || '');
    const errEl    = $('auth-error');
    errEl.textContent = '';

    if (!username || !password) {
      errEl.textContent = '請填寫帳號和密碼';
      return;
    }

    const url = _isRegister ? '/auth/register' : '/auth/login';
    try {
      const res  = await fetch(url, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (data.ok) {
        _user = { username: data.username, best: null };
        _applyLoggedIn();
        closeModal();
      } else {
        errEl.textContent = data.error || '操作失敗，請再試一次';
      }
    } catch (e) {
      errEl.textContent = '網路錯誤，請稍後再試';
    }
  }

  async function logout() {
    await fetch('/auth/logout', { method: 'POST' });
    _user = null;
    _applyGuest();
  }

  function getUsername() { return _user?.username || null; }
  function isLoggedIn()  { return _user !== null; }

  // ── 綁定 DOM 事件（在 DOMContentLoaded 後執行） ───────────
  document.addEventListener('DOMContentLoaded', () => {
    const btnLogin    = $('btn-login');
    const btnRegister = $('btn-register');
    const btnLogout   = $('btn-logout');

    if (btnLogin)    btnLogin.addEventListener('click',    () => openModal('login'));
    if (btnRegister) btnRegister.addEventListener('click', () => openModal('register'));
    if (btnLogout)   btnLogout.addEventListener('click',   logout);

    const closeBtn      = $('auth-close');
    const submitBtn     = $('auth-submit');
    const tabLoginBtn   = $('tab-login');
    const tabRegisterBtn= $('tab-register');
    const pwInput       = $('auth-password');
    const modal         = $('auth-modal');

    if (closeBtn)       closeBtn.addEventListener('click',  closeModal);
    if (submitBtn)      submitBtn.addEventListener('click', _submit);
    if (tabLoginBtn)    tabLoginBtn.addEventListener('click',    () => _switchTab(false));
    if (tabRegisterBtn) tabRegisterBtn.addEventListener('click', () => _switchTab(true));
    if (pwInput)        pwInput.addEventListener('keydown', e => { if (e.key === 'Enter') _submit(); });
    if (modal)          modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });
  });

  return { init, logout, getUsername, isLoggedIn, openModal };
})();
