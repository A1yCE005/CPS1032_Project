#!/usr/bin/env python3
# gen_audio.py — 批量为词库生成本地发音文件
#
# 使用示例:
#   pip install pyttsx3
#   python static/gen_audio.py

import os
import json
import pyttsx3
from glob import glob
import platform
import subprocess
import shutil

# 初始化 TTS 引擎（macOS 下使用 say 命令）
is_mac = platform.system() == "Darwin"
engine = None
if not is_mac:
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)    # 语速，可根据需要调整
        engine.setProperty('volume', 1.0)  # 音量
    except Exception as e:
        print(f"[Warning] pyttsx3 初始化失败: {e}")
        engine = None

def normalize_word(word: str) -> str:
    """将词语转换为文件名安全的形式。"""
    # 只保留合法字符，其他替换为下划线
    safe = "".join(ch if ch.isalnum() else "_" for ch in word)
    return safe

def gen_for_grade(grade: int):
    """
    为指定年级的词库生成语音文件。
    JSON 文件路径: static/words_grade{grade}.json
    输出目录:     static/audio/grade{grade}/
    """
    json_path = os.path.join(os.path.dirname(__file__), f"words_grade{grade}.json")
    audio_dir = os.path.join(os.path.dirname(__file__), "audio", f"grade{grade}")
    os.makedirs(audio_dir, exist_ok=True)

    # 读取词库
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as e:
        print(f"[Error] 无法读取 {json_path}: {e}")
        return

    # 逐词生成
    for entry in raw:
        word = entry.get("word") if isinstance(entry, dict) else str(entry)
        if not word:
            continue
        safe_name = normalize_word(word)
        out_file = os.path.join(audio_dir, f"{safe_name}.mp3")
        if os.path.exists(out_file):
            # 文件已存在，跳过
            continue
        print(f"生成发音: 年级 {grade} → {word} -> {out_file}")
        if is_mac:
            # macOS: say 输出为 AIFF，再用 ffmpeg 转为 MP3
            aiff_file = out_file.replace(".mp3", ".aiff")
            # 生成 AIFF
            subprocess.run(["say", "-o", aiff_file, word], check=False)
            # 将 AIFF 转为 MP3 (16kHz)
            subprocess.run([
                "ffmpeg", "-y", "-loglevel", "error",
                "-i", aiff_file,
                "-ar", "16000",
                "-ac", "1",
                out_file
            ], check=False)
            # 删除中间 AIFF 文件
            try:
                os.remove(aiff_file)
            except OSError:
                pass
        elif engine:
            engine.save_to_file(word, out_file)
        else:
            print(f"[Error] 无可用 TTS 引擎，跳过 {word}")

    # 执行所有待生成任务
    if engine:
        engine.runAndWait()

def main():
    # 为所有 1-8 年级执行生成
    for grade in range(1, 9):
        gen_for_grade(grade)
    print("全部语音文件生成完毕。")

if __name__ == "__main__":
    main()