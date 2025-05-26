// static/script.js  —— 整文件替换

/* --------- DOM refs --------- */
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
const playBtn     = document.getElementById("playBtn");   // 🔉 播放
const manageBtn   = document.getElementById("manageBtn");

let mediaRecorder, chunks = [], currentWord = {};


/* --------- 拉一个随机词 --------- */
async function initWord () {
  const grade = gradeSelect?.value || "1";
  let entry   = {};

  try {
    const res  = await fetch(`/api/random_word?grade=${grade}`);
    entry      = await res.json();
    if (!entry || !entry.word) throw new Error("Empty");
  } catch {
    // 本地兜底
    const list = await fetch(`/static/words_grade${grade}.json`).then(r=>r.json());
    entry      = list[Math.floor(Math.random()*list.length)] || {};
  }

  currentWord          = entry;
  wordEl.textContent   = entry.word || "";
  defEl.textContent    = entry.def || "";
  resBox.hidden        = true;
  retryBtn.hidden      = nextBtn.hidden = true;
}
initWord();
gradeSelect?.addEventListener("change", initWord);


/* --------- 录音 / 停止并评分 --------- */
startBtn.onclick = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({audio:true});
    mediaRecorder = new MediaRecorder(stream, { mimeType:"audio/webm" });
    chunks       = [];

    mediaRecorder.ondataavailable = e => chunks.push(e.data);
    mediaRecorder.start();

    startBtn.disabled = true;
    stopBtn.disabled  = false;
    resBox.hidden     = true;
  } catch (e) {
    alert("无法访问麦克风，请检查浏览器权限。");
  }
};

stopBtn.onclick = async () => {
  if (!mediaRecorder || mediaRecorder.state!=="recording") return;
  stopBtn.disabled = true;
  mediaRecorder.stop();

  mediaRecorder.onstop = async () => {
    const blob = new Blob(chunks, {type:"audio/webm"});
    const fd   = new FormData();
    fd.append("audio", blob, "clip.webm");
    fd.append("target", currentWord.word || "");

    const res  = await fetch("/api/score", {method:"POST", body:fd});
    const data = await res.json();

    const score = Math.max(0, Math.min(100, Math.round(data.score || 0)));
    barInner.style.width = `${score}%`;
    scoreTxt.textContent = `得分： ${score} / 100`;
    resBox.hidden        = false;

    retryBtn.hidden = nextBtn.hidden = false;
    startBtn.disabled = false;
  };
};


/* --------- 再来一次 / 下一题 --------- */
retryBtn.onclick = () => {
  resBox.hidden     = true;
  retryBtn.hidden   = nextBtn.hidden = true;
  wordEl.scrollIntoView({behavior:"smooth", block:"center"});
};

nextBtn.onclick  = () => {
  initWord();
  wordEl.scrollIntoView({behavior:"smooth", block:"center"});
};


/* --------- 本地语音播放 --------- */
playBtn.onclick = e => {
  e.preventDefault();
  const grade = gradeSelect?.value || "1";
  const safe  = encodeURIComponent(currentWord.word || "");
  const audio = new Audio(`/static/audio/grade${grade}/${safe}.mp3`);
  audio.play()
       .catch(err=>{
         console.error("播放失败：", err);
         alert("找不到本地音频，或浏览器阻止自动播放。");
       });
};

/* --------- 词库管理 --------- */
manageBtn?.addEventListener("click", e => {
  // 直接跳到 manage.html（已设置 href）
});
