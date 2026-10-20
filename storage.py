import json
import os
import tempfile
from pathlib import Path


def atomic_write_json(path, data):
    """Write JSON without leaving a truncated file when the process dies mid-write."""
    target = Path(path)
    directory = target.parent if str(target.parent) else Path(".")
    directory.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=str(directory)
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=4)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, target)
    except BaseException:
        try:
            os.unlink(temp_name)
        except OSError:  # hygiene: allow best-effort cleanup of the temp file after a failed write
            pass
        raise
    return target
