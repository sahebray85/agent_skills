"""
Staleness detection and async background refresh for the GeoNames-sourced
knowledge files (global_postal_code_map.csv and geonames_country_info.txt).

Called automatically from core.py on every AddressParser() construction --
cheap to check (one small JSON read), expensive only to actually refresh
(a multi-minute download), which is exactly why refreshing never blocks
the caller.

Stale-while-revalidate: if knowledge/cache_meta.json's downloaded_at is
older than config.yaml's knowledge_cache.expiry_days, a background
refresh is kicked off as a fully detached subprocess (survives this
process exiting) and the CURRENT run keeps using the old data completely
unchanged. refresh_knowledge.py downloads to temp files and atomically
swaps them into place, then updates cache_meta.json -- only once that's
done does the NEXT invocation see the fresh data. This process never
re-downloads anything itself; it only ever decides whether to ask
refresh_knowledge.py to do so, in the background.
"""
import json
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"
META_PATH = KNOWLEDGE_DIR / "cache_meta.json"
LOCK_PATH = KNOWLEDGE_DIR / ".refresh_lock"
REFRESH_SCRIPT = Path(__file__).resolve().parent / "refresh_knowledge.py"
LOCK_STALE_AFTER_SECONDS = 6 * 3600  # a crashed background refresh shouldn't lock forever


def read_meta():
    if META_PATH.exists():
        try:
            return json.loads(META_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def write_meta(meta):
    META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def _lock_is_stale():
    if not LOCK_PATH.exists():
        return True
    try:
        age = time.time() - LOCK_PATH.stat().st_mtime
    except OSError:
        return True
    return age > LOCK_STALE_AFTER_SECONDS


def _age_days(downloaded_at, expiry_days):
    if not downloaded_at:
        return expiry_days + 1  # never recorded -- treat as stale
    try:
        return (date.today() - date.fromisoformat(downloaded_at)).days
    except ValueError:
        return expiry_days + 1  # unparseable -- treat as stale


def maybe_trigger_background_refresh(config):
    """Returns True if a background refresh was just kicked off, else False.
    Never raises -- a refresh-trigger failure must never break parsing."""
    try:
        cache_cfg = config.get("knowledge_cache", {})
        if not cache_cfg.get("auto_refresh", True):
            return False
        expiry_days = cache_cfg.get("expiry_days", 60)

        meta = read_meta()
        if _age_days(meta.get("downloaded_at"), expiry_days) < expiry_days:
            return False  # still fresh

        if LOCK_PATH.exists() and not _lock_is_stale():
            return False  # another process is already refreshing

        LOCK_PATH.write_text(str(time.time()), encoding="utf-8")
        _spawn_detached_refresh()
        return True
    except OSError:
        return False


def _spawn_detached_refresh():
    log_path = KNOWLEDGE_DIR / "refresh_last_run.log"
    log_file = open(log_path, "w", encoding="utf-8")
    kwargs = {"stdout": log_file, "stderr": subprocess.STDOUT, "stdin": subprocess.DEVNULL}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen([sys.executable, str(REFRESH_SCRIPT)], **kwargs)
