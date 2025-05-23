

// static/manage.js
// 词库管理脚本

// DOM 句柄
const gradeSelect    = document.getElementById("gradeManageSelect");
const wordList       = document.getElementById("wordList");
const newWordInput   = document.getElementById("newWordInput");
const addWordBtn     = document.getElementById("addWordBtn");
const saveWordBtn    = document.getElementById("saveWordBtn");
const backBtn        = document.getElementById("backBtn");

// 当前年级词数组
let words = [];

/**
 * 加载指定年级的词库
 */
async function loadWords() {
  const grade = gradeSelect.value;
  try {
    const res = await fetch(`/api/words/${grade}`);
    words = await res.json();
  } catch (err) {
    console.error("获取词库失败", err);
    words = [];
  }
  renderList();
}

/**
 * 渲染词列表
 */
function renderList() {
  wordList.innerHTML = "";
  words.forEach((item, index) => {
    const li = document.createElement("li");
    li.textContent = item.word || item;
    // 删除按钮
    const delBtn = document.createElement("button");
    delBtn.textContent = "删除";
    delBtn.onclick = () => {
      words.splice(index, 1);
      renderList();
    };
    li.appendChild(delBtn);
    wordList.appendChild(li);
  });
}

/**
 * 添加新词
 */
addWordBtn.onclick = () => {
  const v = newWordInput.value.trim();
  if (v) {
    words.push({ word: v });
    newWordInput.value = "";
    renderList();
  }
};

/**
 * 保存修改到后端
 */
saveWordBtn.onclick = async () => {
  const grade = gradeSelect.value;
  try {
    const res = await fetch(`/api/words/${grade}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(words),
    });
    const data = await res.json();
    if (data.status === "ok") {
      alert("词库已保存");
    } else {
      alert("保存失败");
    }
  } catch (err) {
    console.error("保存词库失败", err);
    alert("保存时出错，请检查控制台");
  }
};

/**
 * 返回练习
 */
backBtn.onclick = () => {
  window.location.href = "/";
};

// 年级切换事件
gradeSelect.onchange = loadWords;

// 页面首次加载
loadWords();