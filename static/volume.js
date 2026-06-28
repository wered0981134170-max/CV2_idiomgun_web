// ── 音量控制初始化 + App 啟動 ────────────────────────────────
window.addEventListener('load', () => {
  Audio.init();
  const masterSlider = $('vol-master');
  const bgmSlider    = $('vol-bgm');
  const sfxSlider    = $('vol-sfx');
  const muteBtn      = $('vol-mute');
  const pct = v => Math.round(v * 100) + '%';

  [
    [masterSlider, Audio.setMaster, 'vol-master-val'],
    [bgmSlider,    Audio.setBGM,    'vol-bgm-val'],
    [sfxSlider,    Audio.setSFX,    'vol-sfx-val'],
  ].forEach(([slider, setter, valId]) => {
    slider.addEventListener('input', () => {
      setter(+slider.value);
      $(valId).textContent = pct(slider.value);
    });
  });

  let muted = false, prevMaster = 0.8;
  muteBtn.addEventListener('click', () => {
    muted = !muted;
    if (muted) {
      prevMaster = Audio.getMaster();
      Audio.setMaster(0); masterSlider.value = 0;
      $('vol-master-val').textContent = '0%';
      muteBtn.textContent = '恢復';
      muteBtn.style.borderColor = 'var(--neon-r)';
      muteBtn.style.color = 'var(--neon-r)';
    } else {
      Audio.setMaster(prevMaster); masterSlider.value = prevMaster;
      $('vol-master-val').textContent = pct(prevMaster);
      muteBtn.textContent = '靜音';
      muteBtn.style.borderColor = 'rgba(0,229,160,0.25)';
      muteBtn.style.color = 'var(--muted)';
    }
  });

  Auth.init();
  Game.loadSidebarLeaderboard();
  Game.init();
});
