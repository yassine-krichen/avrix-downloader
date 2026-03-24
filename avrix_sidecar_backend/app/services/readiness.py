from pathlib import Path


def check_storage_ready(config_root: Path) -> tuple[bool, str]:
    try:
        config_root.mkdir(parents=True, exist_ok=True)
        test_file = config_root / ".write_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        return True, "storage_ready"
    except Exception as exc:
        return False, f"storage_unavailable: {exc}"
