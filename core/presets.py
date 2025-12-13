# core/presets.py
from pathlib import Path
import json

# 프리셋 저장 파일 경로
PRESETS_FILE = Path("presets.json")


def load_presets() -> dict:
    """프리셋 파일에서 설정을 불러옵니다."""
    if PRESETS_FILE.exists():
        try:
            with open(PRESETS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_presets(presets: dict):
    """프리셋을 파일에 저장합니다."""
    try:
        with open(PRESETS_FILE, "w", encoding="utf-8") as f:
            json.dump(presets, f, ensure_ascii=False, indent=2)
    except Exception:
        # 굳이 에러를 터뜨릴 필요는 없어서 조용히 무시
        pass