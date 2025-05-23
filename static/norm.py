#!/usr/bin/env python3
# norm.py - 统一 JSON 词库条目格式，将纯字符串包装成 {"word": ...} 对象

import os
import json
import glob

def normalize_file(filepath):
    """
    读取 JSON 文件，规范化每条记录为 {'word': ...} 格式，并覆盖写回。
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            raw = json.load(f)
    except Exception as e:
        print(f"读取 {filepath} 失败: {e}")
        return

    normalized = []
    for item in raw:
        if isinstance(item, str):
            normalized.append({'word': item})
        elif isinstance(item, dict) and 'word' in item:
            normalized.append(item)
        else:
            print(f"跳过无效条目 in {filepath}: {item!r}")

    # 写回
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(normalized, f, ensure_ascii=False, indent=2)
        print(f"已规范化并写回: {filepath}")
    except Exception as e:
        print(f"写入 {filepath} 失败: {e}")

def main():
    # 匹配所有年级 JSON 以及根目录 words.json（如存在）
    base_dir = os.path.dirname(__file__)
    patterns = [
        os.path.join(base_dir, 'words_grade*.json'),
        os.path.join(base_dir, 'words.json'),
    ]
    for pattern in patterns:
        for path in glob.glob(pattern):
            normalize_file(path)

if __name__ == '__main__':
    main()
