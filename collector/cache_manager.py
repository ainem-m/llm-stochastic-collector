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
    
    candidates = list(dir_path.glob(f"run-*-{prompt_hash}.json"))
    if not candidates:
        # 旧形式のファイルも一応チェック（中身を見てハッシュが一致するか確認するのは重いので、名前ベースのみ）
        return None
    
    # タイムスタンプ順にソートして最新を返す
    candidates.sort(key=lambda p: p.name, reverse=True)
    return candidates[0]
