"""Logika pengecekan versi terbaru (GitHub Releases) — murni Python, tanpa GUI dan tanpa jaringan.

Permintaan HTTP-nya sendiri dilakukan di ``ui/update_actions.py`` (QtNetwork); modul ini hanya membandingkan versi
dan membaca respons API, sehingga bisa diuji tanpa PySide6.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from services.constants import GITHUB_OWNER, GITHUB_REPO, URL_RELEASE

NOTES_MAX_CHARS = 1500                                              # catatan rilis yang ditampilkan dipangkas
_TRUSTED_URL_PREFIX = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/"
_VERSION_RE = re.compile(r"^[vV]?(\d+(?:\.\d+)*)(?:-([0-9A-Za-z.-]+))?$")


class UpdateCheckError(Exception):
    """Pengecekan gagal; ``str(exc)`` adalah pesan yang siap ditampilkan ke pengguna."""


@dataclass(frozen=True)
class ReleaseInfo:
    tag: str            # mis. "v0.9.0"
    name: str           # judul rilis (jatuh ke tag bila kosong)
    url: str            # halaman rilis di GitHub (selalu tautan github.com/<owner>/<repo>/…)
    notes: str          # isi catatan rilis, sudah dipangkas; bisa kosong


def parse_version(text: str) -> tuple[tuple[int, ...], str] | None:
    """``"v0.8.8"`` → ``((0, 8, 8), "")``; ``"v0.9.0-beta.1"`` → ``((0, 9), "beta.1")``; tak dikenali → ``None``.

    Angka nol di ekor dibuang supaya ``v1.0`` dan ``v1.0.0`` dianggap sama. Metadata build (``+...``) diabaikan."""
    m = _VERSION_RE.match(text.strip().split("+", 1)[0])
    if not m:
        return None
    nums = [int(part) for part in m.group(1).split(".")]
    while len(nums) > 1 and nums[-1] == 0:
        nums.pop()
    return tuple(nums), m.group(2) or ""


def is_newer(latest: str, current: str) -> bool:
    """True bila ``latest`` lebih baru dari ``current``.

    Beda dengan ``!=``: build lokal yang LEBIH baru dari rilis terakhir (mis. versi dev) tidak dianggap perlu update.
    Rilis final dianggap lebih baru dari pra-rilis dengan angka sama (``v1.0.0`` > ``v1.0.0-beta``).
    Bila salah satu tag tidak bisa dibaca, jatuh ke perbandingan teks biasa."""
    a, b = parse_version(latest), parse_version(current)
    if a is None or b is None:
        return latest.strip() != current.strip()
    if a[0] != b[0]:
        return a[0] > b[0]
    if a[1] == b[1]:
        return False
    if not a[1]:
        return True
    if not b[1]:
        return False
    return a[1] > b[1]


def describe_http_error(status: int) -> str:
    if status == 404:
        return "No release has been published yet."
    if status in (403, 429):
        return "GitHub is limiting requests right now. Please try again later."
    return f"GitHub responded with an unexpected error (HTTP {status})."


def parse_release(payload: bytes | str) -> ReleaseInfo:
    """Baca JSON ``/releases/latest``. Melempar :class:`UpdateCheckError` bila isinya tak bisa dipakai."""
    try:
        data = json.loads(payload)
    except (ValueError, TypeError) as exc:
        raise UpdateCheckError("GitHub returned a response that could not be read.") from exc
    tag = data.get("tag_name") if isinstance(data, dict) else None
    if not isinstance(tag, str) or not tag.strip():
        raise UpdateCheckError("GitHub's response did not include a version number.")
    tag = tag.strip()

    # Data dari jaringan: hanya tautan ke repo ini yang dibuka; selain itu jatuh ke halaman Releases.
    url = data.get("html_url")
    if not isinstance(url, str) or not url.startswith(_TRUSTED_URL_PREFIX):
        url = URL_RELEASE

    name = data.get("name")
    name = name.strip() if isinstance(name, str) and name.strip() else tag
    notes = data.get("body")
    notes = notes.strip() if isinstance(notes, str) else ""
    if len(notes) > NOTES_MAX_CHARS:
        notes = notes[:NOTES_MAX_CHARS].rstrip() + "…"
    return ReleaseInfo(tag=tag, name=name, url=url, notes=notes)
