import os
import json
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from flask import Flask, request, jsonify, send_from_directory

import wave, tempfile
from pydub import AudioSegment  
from rapidfuzz import fuzz
from faster_whisper import WhisperModel
import subprocess
import sys
# 使用 CPU 版 base-int8，适合无独显的教室电脑 (≈500 MB，内存占用 <1.5 GB)
WHISPER = WhisperModel(
    "base",               # 500 MB 权重
    device="cpu",
    compute_type="int8"   # 量化推理，速度与占用折中
)

app = Flask(__name__, static_folder="static")


sample_rate = 16000

@app.route("/")
def root():
    return send_from_directory("static", "index.html")

@app.route("/api/score", methods=["POST"])
def api_score():
    try:
        # ---------- ① 接收上传的 WebM ----------
        webm_file = request.files["audio"]
        ref_word  = request.form["target"]

        # ---------- ② 转码为 16 kHz mono WAV ----------
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_in:
            webm_file.save(tmp_in.name)

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

        # ---------- ④ 计算拼音层面的相似度（rapidfuzz.partial_ratio） ----------
        from pypinyin import lazy_pinyin           # ← 已在文件别处 import 过可略，但重复无害

        rp = ''.join(lazy_pinyin(ref_word.lower()))    # 目标词拼音
        hp = ''.join(lazy_pinyin(hyp_text.lower()))    # 识别结果拼音

        # partial_ratio 会在较长串里找短串的最佳匹配，返回 0-100
        score_val = fuzz.partial_ratio(rp, hp)


        return jsonify({"transcript": hyp_text or "(未识别)", "score": score_val})

    except Exception as e:
        return jsonify({"error": str(e)}), 200



@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

@app.route("/api/words/<int:grade>", methods=["GET"])
def words_by_grade(grade):
    """
    Serve the word list for the given grade (1-8).
    Normalize entries so each is an object with a 'word' field.
    """
    try:
        filepath = os.path.join(app.static_folder, f"words_grade{grade}.json")
        with open(filepath, "r", encoding="utf-8") as f:
            raw = json.load(f)
        normalized = []
        for item in raw:
            if isinstance(item, str):
                normalized.append({"word": item})
            elif isinstance(item, dict) and "word" in item:
                normalized.append(item)
        return jsonify(normalized)
    except Exception:
        # Return empty list on error
        return jsonify([])


# --- POST handler for updating grade words ---
@app.route("/api/words/<int:grade>", methods=["POST"])
def update_words(grade):
    """
    Update the word list JSON for the given grade.
    """
    try:
        # Parse JSON body as list of word entries
        data = request.get_json(force=True) or []
        filepath = os.path.join(app.static_folder, f"words_grade{grade}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # After saving new word list, regenerate audio for this grade
        try:
            subprocess.run([sys.executable, os.path.join(app.static_folder, "gen_audio.py")], check=False)
        except Exception as e:
            # Log but do not fail the API if audio generation fails
            print(f"[Warning] Audio generation failed: {e}")
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/random_word", methods=["GET"])
def random_word():
    # Default to grade 1 if not specified
    grade = int(request.args.get("grade", 1))
    # Load corresponding JSON
    try:
        filepath = os.path.join(app.static_folder, f"words_grade{grade}.json")
        with open(filepath, "r", encoding="utf-8") as f:
            words = json.load(f)
    except Exception:
        words = []
    if not words:
        return jsonify({})
    import random
    word_entry = random.choice(words)
    # If word_entry is a raw string, wrap into dict
    if isinstance(word_entry, str):
        word_entry = {"word": word_entry}
    return jsonify(word_entry)

if __name__ == "__main__":
    # Generate missing audio before startup
    try:
        script_path = os.path.join(app.static_folder, "gen_audio.py")
        subprocess.run([sys.executable, script_path], check=False)
    except Exception as e:
        print(f"[Warning] Initial audio generation failed: {e}")
    app.run(debug=True)
