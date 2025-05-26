# ---------- 依赖 ---------- #
import os, sys, json, subprocess, tempfile          # ←★ 新增 subprocess / tempfile
import numpy as np                                  # ←★ 新增 numpy
from pathlib import Path

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from flask import Flask, request, jsonify, send_from_directory
from faster_whisper import WhisperModel
from huggingface_hub import snapshot_download


# ---------- 自动下载 / 读取模型 ---------- #
MODEL_ID = "rhasspy/faster-whisper-base-int8"
MODEL_DIR = Path(__file__).parent / "models" / MODEL_ID.split("/")[-1]

if not MODEL_DIR.exists():                       # 首次启动才会执行下载
    try:
        snapshot_download(
            repo_id   = MODEL_ID,
            local_dir = MODEL_DIR,
            local_dir_use_symlinks=False,        # 真文件，便于拷贝
            resume_download=True                 # 断点续传
        )
    except Exception as e:
        print(f"[ERROR] 无法下载模型：{e}", file=sys.stderr)
        sys.exit(1)

# ---------- 加载 Whisper ---------- #
WHISPER = WhisperModel(
    str(MODEL_DIR),
    device="cpu",
    compute_type="int8",                          # 权重是 int8 量化                 
)



app = Flask(__name__, static_folder="static")


sample_rate = 16000

@app.route("/")
def root():
    return send_from_directory("static", "index.html")

def load_audio(path):
    cmd = [
        "ffmpeg", "-loglevel", "error",
        "-i", path,           # webm 原文件
        "-ac", "1", "-ar", "16000",  # 单声道 16 kHz
        "-f", "s16le", "-"          # 原始 PCM 流
    ]
    pcm = subprocess.check_output(cmd)
    return np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0

@app.route("/api/score", methods=["POST"])
def api_score():
    file  = request.files["audio"]
    grade = request.form.get("grade", "1")
    tgt   = request.form.get("target", "")

    # 直接读取 webm bytes 入 ffmpeg
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        file.save(tmp.name)
        audio = load_audio(tmp.name)
    os.remove(tmp.name)

    # --- Whisper ---
    segments, _ = WHISPER.transcribe(
        audio,
        beam_size=1, best_of=1,
        vad_filter=True
    )
    hyp_text = "".join([s.text.strip() for s in segments])

    # --- 计算分数 ---
    from pypinyin import lazy_pinyin
    from rapidfuzz.distance import Levenshtein
    ref = "".join(lazy_pinyin(tgt))
    hyp = "".join(lazy_pinyin(hyp_text))
    dist = Levenshtein.distance(ref, hyp)
    score = max(0, 100 - int(100 * dist / max(len(ref), 1)))

    return jsonify({"score": score})


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
