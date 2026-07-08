import json
import os
from typing import Any


def ensure_file_exists(file_path: str, default_data: Any) -> None:
    folder = os.path.dirname(file_path)

    if folder and not os.path.exists(folder):
        os.makedirs(folder)

    if not os.path.exists(file_path):
        save_json(file_path, default_data)


def load_json(file_path: str, default_data: Any) -> Any:
    ensure_file_exists(file_path, default_data)

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read().strip()

            # If file exists but is empty, initialize it properly
            if not content:
                save_json(file_path, default_data)
                return default_data

            return json.loads(content)

    except json.JSONDecodeError:
        # If JSON is broken/invalid, reset it to default
        save_json(file_path, default_data)
        return default_data


def save_json(file_path: str, data: Any) -> None:
    folder = os.path.dirname(file_path)

    if folder and not os.path.exists(folder):
        os.makedirs(folder)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
