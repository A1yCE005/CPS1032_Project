# ====================== static/gen_audio.py ======================
import os, json, time
from pathlib import Path
import pyttsx3
from pydub import AudioSegment
import subprocess


TXT_DIR   = Path(__file__).with_suffix("")          # static/gen_audio
AUDIO_DIR = TXT_DIR.parent / "audio"                # static/audio
AUDIO_DIR.mkdir(exist_ok=True)

engine = pyttsx3.init()        # Windows: SAPI5   Linux: eSpeak
engine.setProperty("rate", 160)    # 语速可自行调节

def text_to_mp3(text:str, out_mp3:Path):
    """
    使用 pyttsx3 先生成 WAV，随后用 pydub 保存为 mp3。
    整个过程不再显式调用 subprocess。
    """
    tmp_wav = out_mp3.with_suffix(".wav")

    # --- TTS 保存 WAV ---
    engine.save_to_file(text, str(tmp_wav))
    engine.runAndWait()

    # --- WAV → MP3 ---
    wav_audio = AudioSegment.from_wav(tmp_wav)
    wav_audio.export(out_mp3, format="mp3", bitrate="96k")

    tmp_wav.unlink(missing_ok=True)      # 清理临时文件

def ensure_grade_audio(grade_json:Path):
    """检查 gradeX 的 json，把缺失的词语语音补齐"""
    grade = grade_json.stem.split("grade")[-1]
    with open(grade_json, "r", encoding="utf-8") as f:
        words = json.load(f)

    out_dir = AUDIO_DIR / f"grade{grade}"
    out_dir.mkdir(parents=True, exist_ok=True)

    for item in words:
        word = item["word"] if isinstance(item, dict) else item
        mp3_path = out_dir / f"{word}.mp3"
        if not mp3_path.exists():
            print(f" [生成] {grade=} {word=}")
            text_to_mp3(word, mp3_path)

if __name__ == "__main__":
    # 遍历 static/ 下所有 gradeX.json
    for j in sorted(Path("static").glob("words_grade*.json")):
        ensure_grade_audio(j)
    print("✅ 语音文件全部就绪")
