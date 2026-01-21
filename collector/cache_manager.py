import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any

def calculate_prompt_hash(config_dict: Dict[str, Any]) -> str:
    """
    プロンプトやモデル設定から一意なハッシュを計算する。
    順序を固定するためにソートしてJSON化してからハッシュ化する。
    """
    # ハッシュに含めるべき重要な設定項目
    relevant_keys = ["model", "prompt", "temp", "max_tokens", "debug"]
    config_to_hash = {k: config_dict.get(k) for k in relevant_keys}
    
    config_str = json.dumps(config_to_hash, sort_keys=True)
    return hashlib.sha256(config_str.encode("utf-8")).hexdigest()

def find_latest_run(output_dir: str, prompt_hash: str) -> Optional[Path]:
    """
    指定されたディレクトリから、特定のプロンプトハッシュを含む最新のJSONファイルを探す。
    ファイル名形式: run-{timestamp}-{hash}.json を想定。
    """
    dir_path = Path(output_dir)
    if not dir_path.exists():
        return None
    
    # run-*.json と checkpoint-*.json の両方を探す
    candidates = list(dir_path.glob(f"run-*-{prompt_hash}.json"))
    candidates.extend(list(dir_path.glob(f"checkpoint-*-{prompt_hash}.json")))
    
    if not candidates:
        return None
    
    # タイムスタンプ部分（インデックス1:日付, 2:時刻）でソートして最新を返す
    # 形式: {prefix}-{date}-{time}-{hash}.json
    def sort_key(p: Path):
        parts = p.name.split("-")
        if len(parts) >= 3:
            return f"{parts[1]}-{parts[2]}" # YYYYMMDD-HHMMSS
        return p.name

    candidates.sort(key=sort_key, reverse=True)
    return candidates[0]
