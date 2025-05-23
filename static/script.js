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
const manageBtn   = document.getElementById("manageBtn");

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

// 管理词库
if (manageBtn) {
  manageBtn.onclick = () => {
    window.location.href = "/static/manage.html";
  };
}

// 本地音频发音
if (pronounceBtn) {
  pronounceBtn.onclick = () => {
    const grade = gradeSelect ? gradeSelect.value : "1";
    const word = currentWord.word || "";
    const safe = encodeURIComponent(word);
    const audio = new Audio(`/static/audio/grade${grade}/${safe}.mp3`);
    audio.play().catch(err => {
      console.error("播放本地音频失败，可能文件不存在：", err);
      alert("音频文件未找到或播放失败");
    });
  };
}