import os
import sys
from pathlib import Path


APP_NAME = "SignFlow"


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def get_resource_dir() -> Path:
    if _is_frozen():
        base = getattr(sys, "_MEIPASS", None)
        if base:
            base_path = Path(base)
            if (base_path / "models").exists() or (base_path / "default_settings.json").exists():
                return base_path
            internal = base_path / "_internal"
            if internal.exists():
                return internal
            return base_path
        exe_dir = Path(sys.executable).resolve().parent
        internal = exe_dir / "_internal"
        if internal.exists():
            return internal
        return exe_dir
    return Path(__file__).resolve().parent


def get_resource_path(*parts: str) -> Path:
    return get_resource_dir().joinpath(*parts)


def get_user_data_dir(create: bool = True) -> Path:
    if not _is_frozen():
        base = Path(__file__).resolve().parent
    else:
        if sys.platform == "win32":
            root = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
            if not root:
                root = str(Path.home() / "AppData" / "Local")
            base = Path(root) / APP_NAME
        else:
            base = Path.home() / f".{APP_NAME.lower()}"
    if create:
        base.mkdir(parents=True, exist_ok=True)
    return base


def get_logs_dir(create: bool = True) -> Path:
    log_dir = get_user_data_dir(create=create) / "logs"
    if create:
        log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir
