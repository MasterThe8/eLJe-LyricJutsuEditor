"""Deteksi encoding dan helper encode/decode untuk file ``.chart``.

Prinsip yang dipakai modul ini:

1. **BOM dideteksi lebih dulu.** BOM UTF-8/UTF-16/UTF-32 disimpan terpisah dari
   teks, sehingga bisa ditulis kembali persis seperti aslinya.
2. **UTF-8 divalidasi secara ketat sebelum deteksi statistik.** UTF-8 punya
   aturan validasi internal, jadi kalau byte berhasil di-decode sebagai UTF-8,
   hampir pasti itu UTF-8 (atau ASCII).
3. **File ASCII dilaporkan sebagai UTF-8**, bukan ``ascii``. Dengan begitu user
   tetap bisa menambahkan karakter non-ASCII saat menyimpan.
4. **Deteksi legacy memakai chardet + kandidat cadangan.** Chardet sering salah
   menebak file pendek (mis. Shift-JIS terbaca Windows-1252), jadi kandidat
   multi-byte CJK diberi skor tambahan bila hasil decode-nya memang didominasi
   karakter CJK.
5. **Encoding asli disimpan di ChartDocument dan dipakai lagi saat save.**
   Ini yang mencegah file non-UTF-8 berubah encoding tanpa sengaja.
"""
from __future__ import annotations

import codecs
import unicodedata
from dataclasses import dataclass

import chardet


# ─────────────────────────────────────────────────────────────────────────────
#  BOM
# ─────────────────────────────────────────────────────────────────────────────

# Urutan penting: BOM UTF-32 LE diawali byte yang sama dengan UTF-16 LE,
# jadi UTF-32 harus diperiksa lebih dulu.
_BOMS = (
    (codecs.BOM_UTF32_LE, "utf-32-le", "UTF-32 LE"),
    (codecs.BOM_UTF32_BE, "utf-32-be", "UTF-32 BE"),
    (codecs.BOM_UTF8, "utf-8", "UTF-8 BOM"),
    (codecs.BOM_UTF16_LE, "utf-16-le", "UTF-16 LE"),
    (codecs.BOM_UTF16_BE, "utf-16-be", "UTF-16 BE"),
)

_BOM_TO_CODEC = {bom: codec for bom, codec, _label in _BOMS}


# ─────────────────────────────────────────────────────────────────────────────
#  Kandidat encoding legacy
# ─────────────────────────────────────────────────────────────────────────────

_LEGACY_CANDIDATES = (
    "cp1252",
    "latin-1",
    "iso-8859-1",
    "shift_jis",
    "cp932",
    "euc-jp",
    "gb18030",
    "gbk",
    "gb2312",
    "big5",
    "euc-kr",
    "cp949",
    "cp1251",
    "koi8-r",
    "cp1250",
    "iso-8859-2",
)

_DISPLAY_NAMES = {
    "utf-8": "UTF-8",
    "utf-8-sig": "UTF-8 BOM",
    "utf-16": "UTF-16",
    "utf-16-le": "UTF-16 LE",
    "utf-16-be": "UTF-16 BE",
    "utf-32-le": "UTF-32 LE",
    "utf-32-be": "UTF-32 BE",
    "iso8859-1": "ISO-8859-1",
    "iso8859-2": "ISO-8859-2",
    "cp1250": "WINDOWS-1250",
    "cp1251": "WINDOWS-1251",
    "cp1252": "WINDOWS-1252",
    "shift_jis": "SHIFT_JIS",
    "cp932": "CP932",
    "euc_jp": "EUC-JP",
    "euc_kr": "EUC-KR",
    "cp949": "CP949",
    "gbk": "GBK",
    "gb2312": "GB2312",
    "gb18030": "GB18030",
    "big5": "BIG5",
}


@dataclass(frozen=True)
class DecodedText:
    """Hasil decode satu file ``.chart``."""

    text: str
    encoding: str          # codec Python tanpa BOM, mis. "utf-8", "shift_jis"
    bom: bytes             # BOM asli (b"" jika tidak ada)
    confidence: float = 1.0
    label: str = ""        # nama siap tampil, mis. "UTF-8 BOM"
    warning: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
#  Nama & label
# ─────────────────────────────────────────────────────────────────────────────

def normalise_codec(name: str | None) -> str | None:
    """Kembalikan nama codec kanonik Python, atau ``None`` jika tidak dikenal."""
    if not name:
        return None
    try:
        return codecs.lookup(name).name
    except LookupError:
        return None


def pretty_name(encoding: str) -> str:
    """Nama encoding yang enak dibaca untuk status bar / pesan."""
    codec = normalise_codec(encoding) or encoding
    return _DISPLAY_NAMES.get(codec, codec.replace("_", "-").upper())


def _detect_bom(raw: bytes) -> tuple[bytes, str, str] | None:
    for bom, codec, label in _BOMS:
        if raw.startswith(bom):
            return bom, codec, label
    return None


# ─────────────────────────────────────────────────────────────────────────────
#  Heuristik penilaian kandidat
# ─────────────────────────────────────────────────────────────────────────────

def _is_cjk_codec(codec: str) -> bool:
    return any(
        part in codec
        for part in ("shift_jis", "sjis", "cp932", "euc_jp", "euc_jis",
                     "gbk", "gb2312", "gb18030", "big5", "euc_kr", "cp949",
                     "johab", "uhc")
    )


def _is_cjk_char(ch: str) -> bool:
    cp = ord(ch)
    return (
        0x1100 <= cp <= 0x11FF      # Hangul Jamo
        or 0x2E80 <= cp <= 0x9FFF   # CJK radicals, kana, CJK unified
        or 0xAC00 <= cp <= 0xD7AF   # Hangul syllables
        or 0xF900 <= cp <= 0xFAFF   # CJK compatibility ideographs
        or 0x20000 <= cp <= 0x2FA1F  # CJK extension B+
    )


def _score_candidate(text: str, codec: str, base_confidence: float) -> float:
    """Beri skor hasil decode. Semakin tinggi semakin plausibel.

    * Karakter kontrol / unassigned / private-use = penalti besar.
    * Kandidat CJK diberi bonus bila mayoritas karakter non-ASCII memang CJK.
    * Kandidat single-byte diberi bonus bila karakter non-ASCII berupa huruf,
      dan penalti bila didominasi simbol/ punctuation (tanda mojibake).
    """
    if not text:
        return base_confidence

    total = len(text)
    bad = 0
    for ch in text:
        if ch in "\t\n\r":
            continue
        if unicodedata.category(ch) in ("Cc", "Cs", "Co", "Cn"):
            bad += 1

    score = base_confidence - 10.0 * (bad / total)
    if bad:
        # Karakter kontrol hampir tidak pernah sah di teks lirik. Penalti
        # ekstra ini mencegah ISO-8859-1 menang hanya karena chardet memilihnya,
        # padahal byte 0x80–0x9F sebenarnya CP1252 (mis. kutip “ ”).
        score -= 1.0

    non_ascii = [ch for ch in text if ord(ch) >= 0x80]
    if not non_ascii:
        return score

    count = len(non_ascii)

    if _is_cjk_codec(codec):
        cjk = sum(1 for ch in non_ascii if _is_cjk_char(ch))
        ratio = cjk / count
        # File sangat pendek tetap boleh menang, tapi jangan sampai satu huruf
        # aksen nyasar dianggap CJK.
        coverage = min(1.0, count / 2.0)
        score += ratio * coverage
        if ratio < 0.5:
            score -= 1.5
    else:
        letters = sum(1 for ch in non_ascii if unicodedata.category(ch).startswith("L"))
        weird = sum(
            1 for ch in non_ascii
            if unicodedata.category(ch).startswith(("S", "P"))
        )
        score += (letters / count) * 0.5
        score -= (weird / count) * 0.5

    return score


# ─────────────────────────────────────────────────────────────────────────────
#  Decode
# ─────────────────────────────────────────────────────────────────────────────

def decode_bytes(raw: bytes, *, encoding: str | None = None) -> DecodedText:
    """Decode bytes file ``.chart`` dan tentukan encoding yang dipakai.

    Args:
        raw:      Isi file mentah.
        encoding: Jika diisi, paksa encoding ini (tanpa auto-detect).

    Raises:
        ValueError: Jika ``encoding`` tidak dikenal atau decode gagal.
    """
    bom_info = _detect_bom(raw)

    # ── Mode paksa (user memilih encoding) ───────────────────────────────
    if encoding is not None:
        codec = normalise_codec(encoding)
        if codec is None:
            raise ValueError(f"Unknown encoding: {encoding!r}")

        bom = b""
        label = pretty_name(codec)
        body = raw
        if bom_info and bom_info[1] == codec:
            bom, body = bom_info[0], raw[len(bom_info[0]):]
            label = bom_info[2]

        try:
            text = body.decode(codec)
        except UnicodeDecodeError as exc:
            raise ValueError(
                f"File cannot be decoded as {pretty_name(codec)}: {exc}"
            ) from exc

        return DecodedText(text, codec, bom, 1.0, label)

    # ── BOM ──────────────────────────────────────────────────────────────
    if bom_info:
        bom, codec, label = bom_info
        body = raw[len(bom):]
        try:
            text = body.decode(codec)
        except UnicodeDecodeError:
            # BOM rusak / isi tidak sesuai; lanjut ke deteksi biasa.
            pass
        else:
            return DecodedText(text, codec, bom, 1.0, label)

    # ── UTF-8 strict ─────────────────────────────────────────────────────
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
    else:
        return DecodedText(text, "utf-8", b"", 1.0, "UTF-8")

    # ── Deteksi legacy ───────────────────────────────────────────────────
    detection = chardet.detect(raw) or {}
    detected_name = detection.get("encoding")
    confidence = float(detection.get("confidence") or 0.0)
    detected_codec = normalise_codec(detected_name)

    if detected_codec == "ascii":
        detected_codec = "utf-8"

    candidates: list[str] = []
    if detected_codec and detected_codec not in ("utf-8", "utf-8-sig"):
        candidates.append(detected_codec)
    candidates.extend(_LEGACY_CANDIDATES)

    seen: set[str] = set()
    scored: list[tuple[float, str, str]] = []

    for candidate in candidates:
        codec = normalise_codec(candidate)
        if codec is None or codec in seen:
            continue
        seen.add(codec)
        if codec in ("utf-8", "utf-8-sig", "ascii"):
            continue

        try:
            text = raw.decode(codec)
        except (UnicodeDecodeError, LookupError):
            continue

        base = confidence if codec == detected_codec else 0.0
        scored.append((_score_candidate(text, codec, base), codec, text))

    if not scored:
        # latin-1 secara teori selalu berhasil; ini hanya jaring pengaman.
        codec = "iso8859-1"
        text = raw.decode(codec, errors="replace")
        return DecodedText(
            text, codec, b"", 0.0, pretty_name(codec),
            "Encoding could not be detected. Verify the lyrics before saving.",
        )

    _best_score, codec, text = max(scored, key=lambda item: item[0])

    warning = None
    if confidence < 0.5 and (detected_codec is None or codec == detected_codec):
        warning = (
            f"Encoding auto-detection is uncertain ({confidence:.0%}). "
            "Verify the lyrics before saving."
        )

    return DecodedText(
        text, codec, b"", confidence if codec == detected_codec else 0.0,
        pretty_name(codec), warning,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Encode
# ─────────────────────────────────────────────────────────────────────────────

def encode_text(text: str, *, encoding: str, bom: bytes = b"") -> bytes:
    """Encode teks dengan *encoding* dan BOM asli (jika cocok).

    Raises:
        UnicodeEncodeError: Jika teks memuat karakter yang tidak bisa
            direpresentasikan oleh *encoding*.
        ValueError: Jika nama encoding tidak dikenal.
    """
    codec = normalise_codec(encoding)
    if codec is None:
        raise ValueError(f"Unknown encoding: {encoding!r}")

    # ``utf-8-sig`` sudah menulis BOM sendiri; jangan dobel.
    if codec == "utf-8-sig":
        return text.encode("utf-8-sig")

    try:
        body = text.encode(codec)
    except LookupError as exc:
        raise ValueError(f"Unknown encoding: {encoding!r}") from exc

    if bom and _BOM_TO_CODEC.get(bom) == codec:
        return bom + body
    return body
