"""
Optional dependency management.
Centralizes try/except import logic for libraries that may not be installed.
"""
from __future__ import annotations

try:
    import lyricsgenius as _lyricsgenius_lib
    _LYRICSGENIUS_AVAILABLE = True
except ImportError:
    _lyricsgenius_lib = None
    _LYRICSGENIUS_AVAILABLE = False


def get_lyricsgenius_lib():
    """
    Return the lyricsgenius module if installed, otherwise None.
    Callers should use this instead of importing _lyricsgenius_lib directly.
    """
    return _lyricsgenius_lib if _LYRICSGENIUS_AVAILABLE else None
