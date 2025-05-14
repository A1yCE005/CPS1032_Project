import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from flask import Flask, request, jsonify, send_from_directory
import wave, json, os, tempfile, Levenshtein
from pydub import AudioSegment  
from rapidfuzz import fuzz
from faster_whisper import WhisperModel
WHISPER = WhisperModel(
    "large-v2",                 # ≥1.6 GB
    device="cuda",              # 若想 CPU 推理写 "cpu"
    compute_type="float16"      # 4090 支持 fp16
)

app = Flask(__name__, static_folder="static")
sample_rate = 16000

def score(ref: str, hyp: str) -> int:
    if not hyp:
        return 0
    dist = Levenshtein.distance(ref, hyp)
    return max(0, 100 - int(100 * dist / max(len(ref), 1)))

@app.route("/")
def root():
    return send_from_directory("static", "index.html")

@app.route("/api/score", methods=["POST"])
def api_score():
    # ---------- ① 接收上传的 WebM ----------
    webm_file = request.files["audio"]
    ref_word  = request.form["target"]

    # ---------- ② 转码为 16 kHz mono WAV ----------
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_in:
        webm_file.save(tmp_in.name)

    from pydub import AudioSegment
    SAMPLE_RATE = 16000
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
        AudioSegment.from_file(tmp_in.name)\
                    .set_frame_rate(SAMPLE_RATE)\
                    .set_channels(1)\
                    .export(tmp_wav.name, format="wav")

    # ---------- ③ Whisper 大模型转写 ----------
    # 返回迭代器，逐段文本
    segments, _ = WHISPER.transcribe(tmp_wav.name,
                                     language="zh",
                                     beam_size=5)
    hyp_text = "".join(seg.text for seg in segments).replace(" ", "")

    # ---------- ④ 计算拼音层面的相似度 ----------
    # ---------- ③ 计算拼音层面的相似度（方案 B：rapidfuzz.partial_ratio） ----------
    from pypinyin import lazy_pinyin           # ← 已在文件别处 import 过可略，但重复无害
    from rapidfuzz import fuzz

    rp = ''.join(lazy_pinyin(ref_word.lower()))    # 目标词拼音
    hp = ''.join(lazy_pinyin(hyp_text.lower()))    # 识别结果拼音

    # partial_ratio 会在较长串里找短串的最佳匹配，返回 0-100
    score_val = fuzz.partial_ratio(rp, hp)


    return jsonify({"transcript": hyp_text or "(未识别)", "score": score_val})



@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == "__main__":
    app.run(debug=True)
