import json
import re
from dataclasses import asdict
from pathlib import Path

from models import DealInput


DEFAULT_STORAGE_DIR = Path("saved_deals")


def sanitize_deal_name(name: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9]+", "-", name.strip()).strip("-").lower()
    return sanitized or "untitled-deal"


def ensure_storage_dir(storage_dir: Path = DEFAULT_STORAGE_DIR) -> Path:
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir


def get_deal_path(name: str, storage_dir: Path = DEFAULT_STORAGE_DIR) -> Path:
    return ensure_storage_dir(storage_dir) / f"{sanitize_deal_name(name)}.json"


def save_deal(deal_name: str, deal: DealInput, storage_dir: Path = DEFAULT_STORAGE_DIR) -> Path:
    deal_path = get_deal_path(deal_name, storage_dir)
    with deal_path.open("w", encoding="utf-8") as file:
        json.dump(asdict(deal), file, indent=2)
    return deal_path


def list_saved_deals(storage_dir: Path = DEFAULT_STORAGE_DIR) -> list[str]:
    storage_dir = ensure_storage_dir(storage_dir)
    return sorted(path.stem for path in storage_dir.glob("*.json"))


def load_deal(deal_name: str, storage_dir: Path = DEFAULT_STORAGE_DIR) -> dict[str, float | int]:
    deal_path = get_deal_path(deal_name, storage_dir)
    with deal_path.open("r", encoding="utf-8") as file:
        return json.load(file)
