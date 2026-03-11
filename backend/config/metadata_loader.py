# config/metadata_loader.py
"""Load metadata from external configuration files"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any

CONFIG_DIR = Path(__file__).parent


def load_strategy_explainers() -> Dict[str, Dict[str, Dict[str, str]]]:
    """Load strategy explainers from YAML file"""
    yaml_path = CONFIG_DIR / "strategies.yaml"
    
    if not yaml_path.exists():
        return {}
    
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    return data.get("strategies", {})


def load_pattern_definitions() -> Dict[str, Dict[str, Any]]:
    """Load pattern definitions from JSON file"""
    json_path = CONFIG_DIR / "patterns.json"
    
    if not json_path.exists():
        return {}
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data.get("pattern_definitions", {})


def get_strategy_explainer(
    strategy_id: str,
    lang: str = "ko",
    rsi_ob: int = 70,
    sma_main_len: int = 200,
    sma1_len: int = 20,
    sma2_len: int = 60,
) -> Dict[str, str]:
    """
    Get formatted strategy explainer with parameter substitution.
    
    Args:
        strategy_id: Strategy identifier (e.g., "Connors", "Sqz")
        lang: Language code ("ko" or "en")
        rsi_ob: RSI overbought threshold
        sma_main_len: Main SMA length
        sma1_len: SMA1 length
        sma2_len: SMA2 length
    
    Returns:
        Dictionary with concept, Long, Short, regime keys
    """
    explainers = load_strategy_explainers()
    
    if strategy_id not in explainers:
        return {}
    
    strategy_data = explainers[strategy_id]
    lang_data = strategy_data.get(lang, {})
    
    if not lang_data:
        return {}
    
    rsi_os = 100 - rsi_ob
    # Format strings with parameters
    formatted = {
        "concept": lang_data.get("concept", ""),
        "Long": lang_data.get("long", "").format(
            rsi_ob=rsi_ob,
            rsi_os=rsi_os,
            sma_main_len=sma_main_len,
            sma1_len=sma1_len,
            sma2_len=sma2_len,
        ),
        "Short": lang_data.get("short", "").format(
            rsi_ob=rsi_ob,
            rsi_os=rsi_os,
            sma_main_len=sma_main_len,
            sma1_len=sma1_len,
            sma2_len=sma2_len,
        ),
        "regime": lang_data.get("regime", ""),
    }
    
    return formatted
