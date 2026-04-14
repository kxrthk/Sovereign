"""
sovereign_encoding.py — Windows UTF-8 Bootstrap
=================================================
Import this module AT THE TOP of any Python entry point to permanently fix
the 'charmap' codec crash caused by emoji/Unicode characters on Windows.

Usage:
    import sovereign_encoding  # Must be first import in entry-point files

This module:
  1. Reconfigures sys.stdout/stderr to UTF-8 with 'replace' error handling
  2. Sets PYTHONIOENCODING env var so child processes inherit the fix
  3. Is safe to import multiple times (idempotent)
  4. Is a no-op on Linux/macOS (they already default to UTF-8)
"""

import sys
import os


def _apply():
    """Apply UTF-8 encoding fixes for the current process."""
    if sys.platform != "win32":
        return  # Unix systems default to UTF-8; nothing to do

    # 1. Reconfigure stdout/stderr to UTF-8
    #    'replace' ensures we NEVER crash — worst case an emoji becomes '?'
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass  # Already reconfigured or not a TextIO wrapper

    # 2. Set env vars so any child processes we spawn also get UTF-8
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")


# Auto-apply on import — just `import sovereign_encoding` is enough
_apply()
