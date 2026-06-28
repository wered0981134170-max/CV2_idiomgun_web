// ── 遊戲常數 ─────────────────────────────────────────────
const HOVER_TIME   = 1.5;
let   TOTAL_Q      = 10;
const Q_TIME_LIMIT = 15.0;

const EXPLANATIONS = {
  "畫蛇添足": "「畫」一條「蛇」，又「添」上腳",
  "一鼓作氣": "打一次「鼓」，「作」出「氣勢」",
  "破釜沉舟": "「打破」「鍋釜」，「沉」掉「船」",
  "一目了然": "「一眼」看去，「了解」「然後」全懂",
  "一箭雙鵰": "「一箭」射出，「中」兩隻「鳥」",
  "虎視眈眈": "虎在「看」，「眈眈」地盯著",
  "青出於藍": "「青色」「出自於」「藍色」之調配",
  "當機立斷": "「當下的」「機會」立刻「判斷」要不要",
  "半途而廢": "都到了「一半的路途」，就「作廢」掉了",
  "如魚得水": "「就如」一條「魚」「得到了」水",
};

// ── DOM 工具函式 ──────────────────────────────────────────
const $ = id => document.getElementById(id);
const show = el => { if (el) el.style.display = ''; };
const hide = el => { if (el) el.style.display = 'none'; };

// ── 難度 / 模式選擇狀態 ───────────────────────────────────
let selectedDifficulty = 'elementary_high';
let selectedMode       = 'normal';

// ── 遊戲層顯示切換 ────────────────────────────────────────
const showGame    = () => { $('game-layer').style.visibility = 'visible'; $('game-layer').style.pointerEvents = 'auto'; };
const hideGame    = () => { $('game-layer').style.visibility = 'hidden';  $('game-layer').style.pointerEvents = 'none'; };
const showCompose = () => { $('compose-layer').style.visibility = 'visible'; $('compose-layer').style.pointerEvents = 'auto'; };
const hideCompose = () => { $('compose-layer').style.visibility = 'hidden';  $('compose-layer').style.pointerEvents = 'none'; $('compose-drag').style.display = 'none'; };
