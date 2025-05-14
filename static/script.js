/* =========================================================
   口语练习 · 前端脚本（transform+opacity 动效版）
   =======================================================*/

   const wordEl = document.getElementById("word");
   const defEl  = document.getElementById("definition");
   
   const recGroup  = document.getElementById("recGroup");   // 开始/停止
   const postGroup = document.getElementById("postGroup");  // 再来/下一
   
   const startBtn = document.getElementById("startBtn");
   const stopBtn  = document.getElementById("stopBtn");
   const retryBtn = document.getElementById("retryBtn");
   const nextBtn  = document.getElementById("nextBtn");
   
   const resBox   = document.getElementById("result");
   const barInner = document.getElementById("barInner");
   const scoreTxt = document.getElementById("scoreText");
   
   let mediaRecorder, chunks = [];
   let currentWord = {};
   
   /* ---------- 动画辅助：transform + opacity ---------- */
   function fadeIn(el){
     el.hidden = false;
     el.classList.remove("t-out");
     void el.offsetWidth;            // 强制回流
     el.classList.add("t-in");
   }
   function fadeOut(el){
     if(el.hidden) return;
     el.classList.remove("t-in");
     el.classList.add("t-out");
     el.addEventListener("animationend", ()=> el.hidden = true, {once:true});
   }
   
   /* ---------- 取随机词 ---------- */
   async function initWord(){
     try{
       currentWord = await fetch("/api/random_word?level=1").then(r=>r.json());
     }catch{
       const local = await fetch("/static/words.json").then(r=>r.json());
       currentWord = local[Math.floor(Math.random()*local.length)];
     }
     wordEl.textContent = currentWord.word;
     defEl.textContent  = currentWord.def_zh || currentWord.def_en || "";
   }
   initWord();
   
   /* ---------- 开始录音 ---------- */
   startBtn.onclick = async () => {
     const stream = await navigator.mediaDevices.getUserMedia({audio:true});
     mediaRecorder = new MediaRecorder(stream,{mimeType:"audio/webm"});
     chunks = [];
     mediaRecorder.ondataavailable = e=>chunks.push(e.data);
     mediaRecorder.start();
   
     fadeOut(postGroup);
     fadeIn(recGroup);
   
     startBtn.disabled = true;
     stopBtn.disabled  = false;
     resBox.hidden     = true;
   };
   
   /* ---------- 停止并评分 ---------- */
   stopBtn.onclick = () => {
     stopBtn.disabled = true;
     if(!mediaRecorder || mediaRecorder.state!=="recording"){
       alert("录音尚未开始或被拒绝");
       startBtn.disabled = false;
       return;
     }
     mediaRecorder.stop();
   
     mediaRecorder.onstop = async ()=>{
       if(!chunks.length){ alert("未捕获到音频，请重试"); return; }
   
       const blob = new Blob(chunks,{type:"audio/webm"});
       const fd = new FormData();
       fd.append("audio", blob, "in.webm");
       fd.append("target", currentWord.word);
       const data = await fetch("/api/score",{method:"POST",body:fd}).then(r=>r.json());
   
       const score = Math.max(0, Math.min(100, Math.round(data.score)));
       barInner.style.width = `${score}%`;
       scoreTxt.textContent = `得分： ${score} / 100`;
       scoreTxt.classList.remove("score-pop"); void scoreTxt.offsetWidth;
       scoreTxt.classList.add("score-pop");
       resBox.hidden = false;
   
       fadeOut(recGroup);
       fadeIn(postGroup);
   
       startBtn.disabled = false;
       stopBtn.disabled  = true;
     };
   };
   
   /* ---------- 再来一次 ---------- */
   retryBtn.onclick = ()=>{
     fadeOut(postGroup);
     fadeIn(recGroup);
     startBtn.click();
   };
   
   /* ---------- 下一题 ---------- */
   nextBtn.onclick = async ()=>{
     fadeOut(postGroup);
     fadeIn(recGroup);
     barInner.style.width = "0";
     scoreTxt.textContent = "";
     scoreTxt.classList.remove("score-pop");
     await initWord();
   };
   