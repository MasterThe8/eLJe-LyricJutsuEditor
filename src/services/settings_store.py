"""Penyimpanan setting persisten: pembungkus ``QSettings`` yang toleran terhadap data rusak.

Satu-satunya modul yang menyentuh ``QSettings``. Skema (kunci, nilai bawaan, validasi) ada di ``services.settings``.

Aturan yang dijaga di sini, karena penyimpanan ini hidup di luar kendali aplikasi (registry / file .conf yang bisa
diedit tangan, rusak, atau dikunci):

* MEMBACA tidak pernah melempar error: nilai hilang / rusak / bertipe salah → nilai bawaan dari pemanggil.
* MENULIS tidak pernah melempar error: kegagalan dicatat ke log dan dilaporkan lewat nilai kembalian (``False``),
  jadi aplikasi tetap berjalan dengan nilai yang sedang aktif di memori.
* Tipe dipulihkan secara manual, bukan lewat ``QSettings.value(type=...)``: backend INI (macOS/Linux) mengembalikan
  semuanya sebagai string, dan string berisi koma bisa kembali sebagai list; registry Windows berbeda lagi.

``backend`` bisa diganti (mis. dict palsu pada tes); apa pun yang punya ``value / setValue / remove / sync`` cocok.
"""
from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any, Protocol

SETTINGS_ORG = "MasterThe8"
SETTINGS_APP = "eLJe"

log = logging.getLogger(__name__)

_TRUE = {"true", "1", "yes", "on"}
_FALSE = {"false", "0", "no", "off"}


class Backend(Protocol):
    """Subset API ``QSettings`` yang dipakai di sini."""

    def value(self, key: str, default: Any = None) -> Any: ...
    def setValue(self, key: str, value: Any) -> None: ...  # noqa: N802  (nama mengikuti QSettings)
    def remove(self, key: str) -> None: ...
    def sync(self) -> None: ...


def _open_qsettings() -> Backend:
    from PySide6.QtCore import QSettings        # impor lambat: modul ini bisa dipakai/diuji tanpa PySide6
    return QSettings(SETTINGS_ORG, SETTINGS_APP)


def _backend_ok(backend: Backend) -> bool:
    """``QSettings.status()`` bukan NoError setelah gagal menulis (izin, disk penuh, file terkunci)."""
    status = getattr(backend, "status", None)
    if status is None:
        return True
    try:
        state = status()
        return getattr(state, "name", state) in ("NoError", 0)
    except Exception:                                       # noqa: BLE001
        return True


class SettingsStore:
    """Baca/tulis nilai bertipe dengan kunci bergaya ``grup/nama``."""

    def __init__(self, backend: Backend | None = None):
        self._backend = backend
        self._read_warned = False                           # penyimpanan rusak: satu peringatan, bukan satu per kunci

    # -- backend (dibuat saat pertama dipakai) ---------------------------------------------------
    @property
    def backend(self) -> Backend:
        if self._backend is None:
            self._backend = _open_qsettings()
        return self._backend

    def _raw(self, key: str) -> Any:
        try:
            return self.backend.value(key, None)
        except Exception as exc:                            # noqa: BLE001  (penyimpanan korup / tak terbaca)
            if not self._read_warned:
                self._read_warned = True
                log.warning("Could not read settings (%s); using defaults: %s", key, exc)
            return None

    # -- membaca ---------------------------------------------------------------------------------
    def get_str(self, key: str, default: str, *, max_len: int | None = None) -> str:
        value = self._raw(key)
        if value is None:
            return default
        if isinstance(value, (list, tuple)):                # INI memecah "a,b" menjadi list
            value = ",".join(str(part) for part in value)
        text = str(value)
        if max_len is not None and len(text) > max_len:
            return default
        return text

    def get_int(self, key: str, default: int, lo: int, hi: int) -> int:
        """Bilangan bulat dijepit ke ``[lo, hi]``; bukan angka → ``default``."""
        value = self._raw(key)
        if isinstance(value, bool) or value is None:
            return default
        try:
            number = int(str(value).strip())
        except ValueError:
            return default
        return max(lo, min(hi, number))

    def get_bool(self, key: str, default: bool) -> bool:
        value = self._raw(key)
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        text = str(value).strip().lower()
        if text in _TRUE:
            return True
        if text in _FALSE:
            return False
        return default

    # -- menulis ---------------------------------------------------------------------------------
    def set_many(self, items: Mapping[str, Any]) -> bool:
        """Tulis beberapa nilai sekaligus lalu ``sync()`` satu kali. ``False`` bila gagal (sudah dicatat di log)."""
        try:
            backend = self.backend
            for key, value in items.items():
                backend.setValue(key, value)
            backend.sync()
            if not _backend_ok(backend):
                log.warning("Settings store reported an error while saving %s", ", ".join(items))
                return False
            return True
        except Exception as exc:                            # noqa: BLE001
            log.warning("Could not save settings (%s): %s", ", ".join(items), exc)
            return False

    def set(self, key: str, value: Any) -> bool:
        return self.set_many({key: value})


_default_store: SettingsStore | None = None


def default_store() -> SettingsStore:
    """Penyimpanan bersama milik aplikasi (``QSettings(MasterThe8, eLJe)``)."""
    global _default_store
    if _default_store is None:
        _default_store = SettingsStore()
    return _default_store
