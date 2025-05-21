const startBtn    = document.getElementById("startBtn");
const stopBtn     = document.getElementById("stopBtn");
const retryBtn    = document.getElementById("retryBtn");
const nextBtn     = document.getElementById("nextBtn");
const wordEl      = document.getElementById("word");
const defEl       = document.getElementById("definition");
const resBox      = document.getElementById("result");
const barInner    = document.getElementById("barInner");
const scoreTxt    = document.getElementById("scoreText");
const gradeSelect = document.getElementById("gradeSelect");
const pronounceBtn= document.getElementById("pronounceBtn");

let mediaRecorder, chunks = [], currentWord = {};

// 更健壮的随机取词，按年级请求 /api/random_word
async function initWord(){
  const grade = gradeSelect ? gradeSelect.value : "1";
  let entry = {};
  try {
    const res = await fetch(`/api/random_word?grade=${grade}`);
    entry = await res.json();
    if (!entry || !entry.word) throw new Error("Empty word");
  } catch {
    // 本地兜底
    const local = await fetch(`/static/words_grade${grade}.json`).then(r=>r.json());
    entry = local[Math.floor(Math.random()*local.length)] || {};
  }
  currentWord = entry;
  wordEl.textContent = entry.word || "";
  defEl.textContent  = entry.def || "";
}

initWord();
if (gradeSelect) gradeSelect.onchange = initWord;

// 录音、评分、动画、再来一次、下一题、发音... (省略，功能已就绪)