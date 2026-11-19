"""TransitionTimeline — adegan lirik (phrase sekarang / berikutnya / transisi) sebagai fungsi waktu.

Murni Python (tanpa GUI). ``scene_at(t)`` stateless seperti scheduler: seek, pause, dan loop otomatis
benar karena adegan selalu dihitung dari waktu, tidak pernah diakumulasi.

Transisi dipicu oleh EVENT pada tick-nya, bukan oleh "phrase selesai" (penjelasan pengguna + frame
animasi Clone Hero):

* ``phrase_start`` saat layar lirik SEDANG AKTIF (phrase sebelumnya belum ditutup ``phrase_end``)
  → SLIDE UP "kincir air": baris sekarang berubah putih lalu memudar sambil naik; baris berikutnya naik
  dan membesar ke slot sekarang; baris setelahnya muncul dari bawah.
* ``phrase_start`` saat layar KOSONG (sebelum phrase pertama, atau setelah ``phrase_end``)
  → hanya FADE IN (phrase sekarang dan baris berikutnya muncul di tempatnya; tanpa gerak).
* ``phrase_end`` → hanya FADE OUT, lalu layar kosong (instrumental: tidak ada lirik di layar).
* Phrase terakhir tanpa ``phrase_end`` tetap tampil.

Durasi tiap transisi = ``min(batas, jarak dari tick pemicu ke event BERIKUTNYA)``:
``phrase_start`` → lirik pertama phrase itu; ``phrase_end`` → ``phrase_start`` berikutnya (batas penuh bila
tidak ada). Batas: Slide Up 0.18 s (``SLIDE_S`` pada implementasi preview Intro No Jutsu; konsisten dengan
6 frame gerak pada rekaman pengguna), Fade In/Out 1.0 s (``END_FADE_S``). Semakin mepet tick-nya, semakin
cepat sampai tak terlihat (jarak 0 = seketika). Itulah dasar opsi Jutsu "No SlideUp Transition":
``lyric -`` di 768, ``phrase_start`` di 769, lirik di 770 → Slide Up hanya berlangsung 1 tick.

Preview baris BERIKUTNYA hanya tampil bila phrase itu tidak datang "dari keheningan": phrase sebelumnya
punya ``phrase_end`` DAN lirik pertama phrase berikutnya berjarak >= ``silence_gap`` (10 s, ``IDLE_FADE_S`` pada
preview Intro No Jutsu) setelah ``phrase_end`` itu. Pada jeda instrumental sepanjang itu lirik akan memudar,
jadi baris berikutnya tidak boleh sudah terlihat. Phrase sebelumnya tanpa ``phrase_end`` selalu menyambung.

Syarat yang SUDAH terukur dari frame: skala/opasitas baris berikutnya, gerak seragam satu slot,
baris keluar berubah putih lalu transparan penuh di ≈65% transisi, baris masuk ≈1.25× lebih cepat.
BELUM terverifikasi: warna baris yang memudar pada Fade Out (di sini sama dengan Slide Up: putih),
panel latar ikut memudar bersama teks, dan sorotan suku kata dianggap seketika (tanpa animasi warna).
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass
from enum import Enum

from core.preview.lyrics_parser import PreviewPhrase
from core.preview.scheduler import LyricScheduler


class Role(str, Enum):
    CURRENT = "current"
    NEXT = "next"
    EXITING = "exiting"          # baris sekarang yang keluar saat Slide Up (naik + memudar)
    PROMOTING = "promoting"      # baris berikutnya yang naik/membesar ke slot sekarang
    ENTERING = "entering"        # baris baru yang muncul dari bawah sebagai "berikutnya"


class Kind(str, Enum):
    FADE_IN = "fade_in"
    SLIDE_UP = "slide_up"
    FADE_OUT = "fade_out"


_EASINGS = {
    "linear": lambda p: p,
    "ease_in_out": lambda p: p * p * (3.0 - 2.0 * p),
}


@dataclass(frozen=True)
class SceneStyle:
    next_scale: float = 0.50           # terukur: lebar teks 'berikutnya' / 'sekarang' (0.495 pd ambang terendah yg andal)
    next_alpha: float = 0.55           # terukur ≈ 0.5–0.55 (setara abu #9d9d9d pada referensi)
    slide_duration: float = 0.18       # detik; SLIDE_S pada preview Intro No Jutsu
    fade_duration: float = 1.0         # detik; END_FADE_S pada preview Intro No Jutsu (dan batas dari pengguna)
    silence_gap: float | None = 10.0   # jarak (detik) phrase_end → lirik pertama berikutnya yang dianggap jeda instrumental:
                                       # baris berikutnya TIDAK ditampilkan. None = selalu tampilkan.
    idle_threshold: float | None = None   # None = aturan pengguna: phrase_end SELALU Fade Out.
                                          # 10.0 = perilaku referensi (IDLE_FADE_S): bila lirik pertama phrase berikutnya datang
                                          # < 10 s setelah phrase_end, tidak ada Fade Out; phrase berikutnya Slide Up saat phrase_end.
    exit_fade_end: float = 0.65        # fraksi Slide Up saat baris keluar sudah transparan (terukur)
    enter_speed: float = 1.25          # baris yang masuk dari bawah bergerak lebih cepat dari slot (terukur kasar)
    easing: str = "linear"


@dataclass(frozen=True, slots=True)
class SceneItem:
    phrase: PreviewPhrase
    role: Role
    slot: float          # 0 = slot sekarang, 1 = slot berikutnya, <0 di atas (keluar), >1 di bawah (masuk)
    scale: float         # 1.0 = ukuran baris sekarang
    alpha: float
    sung: int            # jumlah suku kata berwarna highlight (0 = semua warna dasar)


@dataclass(frozen=True)
class Scene:
    time: float
    items: tuple[SceneItem, ...]
    progress: float | None = None       # 0..1 selama transisi (mentah, sebelum easing); None = statis
    kind: Kind | None = None            # jenis transisi yang sedang berjalan
    transition: int | None = None       # indeks phrase pemicu transisi
    visibility: float = 1.0             # 0..1: seberapa terlihat layar lirik (panel latar memudar mengikuti ini)
    next_visibility: float = 1.0        # 0..1: panel baris-berikutnya relatif terhadap panelnya sendiri (0 = tak ada baris
                                        # berikutnya). Fade seluruh layar sudah di ``visibility``; JANGAN dikalikan dua kali.

    @property
    def animating(self) -> bool:
        return self.progress is not None

    @property
    def key(self) -> tuple | None:
        """Identitas tampilan statis: UI hanya perlu menggambar ulang bila berubah. None saat animasi."""
        if self.animating:
            return None
        return tuple((it.phrase.phrase_id, it.role.value, it.sung) for it in self.items)

    @property
    def current(self) -> SceneItem | None:
        return next((it for it in self.items if it.role in (Role.CURRENT, Role.PROMOTING)), None)


@dataclass(frozen=True, slots=True)
class _Event:
    time: float
    kind: Kind
    index: int           # indeks phrase (di daftar phrase non-kosong) yang memicu
    duration: float


class TransitionTimeline:
    """Daftar event transisi atas ``LyricScheduler.phrases`` (phrase kosong sudah dibuang di sana)."""

    def __init__(self, scheduler: LyricScheduler, style: SceneStyle = SceneStyle()) -> None:
        if style.easing not in _EASINGS:
            raise ValueError(f"unknown easing: {style.easing!r} (choices: {sorted(_EASINGS)})")
        self.style = style
        self._ease = _EASINGS[style.easing]
        self._phrases: list[PreviewPhrase] = list(scheduler.phrases)
        self._times: list[list[float]] = [[l.timestamp for l in p.lyrics] for p in self._phrases]

        phrases, n = self._phrases, len(self._phrases)
        # Urutan event pada tick sama: per phrase (START_i lalu END_i), jadi END_{i-1} selalu mendahului START_i
        # dan phrase yang mulai & berakhir di tick yang sama tetap START → END.
        events: list[tuple[float, int, int, _Event]] = []     # (waktu, indeks phrase, 0=START/1=END, event)

        def has_end(k: int) -> bool:
            return phrases[k].end_explicit and phrases[k].end_time is not None

        def from_silence(k: int) -> bool:
            """Phrase k muncul setelah jeda instrumental → tidak boleh jadi preview saat phrase sebelumnya tampil."""
            if k == 0:
                return True
            if style.silence_gap is None or not has_end(k - 1):
                return False
            return phrases[k].lyrics[0].timestamp - phrases[k - 1].end_time >= style.silence_gap

        self._preview: list[bool] = [not from_silence(k) for k in range(n)]

        def continuous(k: int) -> bool:
            """Perilaku opsional (idle_threshold): phrase k langsung menyambung phrase sebelumnya."""
            if style.idle_threshold is None or k == 0 or not has_end(k - 1):
                return False
            return phrases[k].lyrics[0].timestamp - phrases[k - 1].end_time < style.idle_threshold

        for i, p in enumerate(phrases):
            start, first_lyric = p.start_time, p.lyrics[0].timestamp
            if continuous(i):                                   # Slide Up di waktu phrase_end sebelumnya
                at = phrases[i - 1].end_time
                events.append((at, i, 0, _Event(at, Kind.SLIDE_UP, i, min(style.slide_duration, max(0.0, first_lyric - at)))))
            else:
                kind = Kind.SLIDE_UP if (i > 0 and not has_end(i - 1)) else Kind.FADE_IN
                limit = style.slide_duration if kind is Kind.SLIDE_UP else style.fade_duration
                events.append((start, i, 0, _Event(start, kind, i, min(limit, max(0.0, first_lyric - start)))))

            if has_end(i) and not (i + 1 < n and continuous(i + 1)):     # tanpa Fade Out bila langsung disambung
                following = phrases[i + 1].start_time if i + 1 < n else None
                out = style.fade_duration if following is None else \
                    min(style.fade_duration, max(0.0, following - p.end_time))
                events.append((p.end_time, i, 1, _Event(p.end_time, Kind.FADE_OUT, i, out)))
        events.sort(key=lambda e: (e[0], e[1], e[2]))
        self._events: list[_Event] = [e[3] for e in events]
        self._event_times: list[float] = [e.time for e in self._events]

    # ── info ─────────────────────────────────────────────────────────────
    def __len__(self) -> int:
        return len(self._phrases)

    @property
    def transitions(self) -> tuple[tuple[float, str, int, float], ...]:
        """((waktu, jenis, indeks phrase, durasi) per event) — untuk tes dan debugging."""
        return tuple((e.time, e.kind.value, e.index, e.duration) for e in self._events)

    # ── query ────────────────────────────────────────────────────────────
    def scene_at(self, t: float) -> Scene:
        k = bisect_right(self._event_times, t) - 1            # event terakhir yang sudah terjadi
        if k < 0:
            return Scene(t, (), visibility=0.0)
        ev = self._events[k]
        if ev.duration > 0 and t < ev.time + ev.duration:
            return self._animating(t, ev, (t - ev.time) / ev.duration)
        if ev.kind is Kind.FADE_OUT:
            return Scene(t, (), visibility=0.0)
        return self._static(t, ev.index)

    # ── internal ─────────────────────────────────────────────────────────
    def _sung(self, index: int, t: float) -> int:
        return bisect_right(self._times[index], t)

    def _scale(self, slot: float) -> float:
        ns = self.style.next_scale
        if slot <= 0.0:
            return 1.0
        if slot >= 1.0:
            return ns
        return 1.0 + (ns - 1.0) * slot

    def _current(self, index: int, t: float, alpha: float = 1.0, sung: int | None = None) -> SceneItem:
        return SceneItem(self._phrases[index], Role.CURRENT, 0.0, 1.0, alpha,
                         self._sung(index, t) if sung is None else sung)

    def _next(self, index: int, alpha: float) -> SceneItem:
        return SceneItem(self._phrases[index], Role.NEXT, 1.0, self.style.next_scale, alpha, 0)

    def _has_preview(self, index: int) -> bool:
        return index < len(self._phrases) and self._preview[index]

    def _static(self, t: float, index: int) -> Scene:
        items = [self._current(index, t)]
        has_next = self._has_preview(index + 1)
        if has_next:
            items.append(self._next(index + 1, self.style.next_alpha))
        return Scene(t, tuple(items), next_visibility=1.0 if has_next else 0.0)

    def _animating(self, t: float, ev: _Event, p: float) -> Scene:
        n, i, st, e = len(self._phrases), ev.index, self.style, self._ease(p)

        if ev.kind is Kind.FADE_IN:                                   # layar kosong → lirik muncul di tempatnya
            items = [self._current(i, t, alpha=e)]
            has_next = self._has_preview(i + 1)
            if has_next:
                items.append(self._next(i + 1, st.next_alpha * e))
            return Scene(t, tuple(items), p, ev.kind, i, visibility=e, next_visibility=1.0 if has_next else 0.0)

        if ev.kind is Kind.FADE_OUT:                                  # phrase_end → semua memudar, tanpa gerak
            items = [self._current(i, t, alpha=1.0 - e, sung=0)]      # keluar = warna dasar (seperti Slide Up)
            has_next = self._has_preview(i + 1)
            if has_next:
                items.append(self._next(i + 1, st.next_alpha * (1.0 - e)))
            return Scene(t, tuple(items), p, ev.kind, i, visibility=1.0 - e, next_visibility=1.0 if has_next else 0.0)

        # SLIDE_UP: baris phrase i-1 keluar, phrase i naik ke slot sekarang, phrase i+1 masuk dari bawah
        items = [SceneItem(self._phrases[i - 1], Role.EXITING, -e, 1.0,
                           max(0.0, 1.0 - e / st.exit_fade_end), 0)]  # keluar: semua warna dasar (putih, terukur)
        slot = 1.0 - e
        items.append(SceneItem(self._phrases[i], Role.PROMOTING, slot, self._scale(slot),
                               st.next_alpha + (1.0 - st.next_alpha) * e, self._sung(i, t)))
        has_next = self._has_preview(i + 1)
        if has_next:
            rush = min(1.0, st.enter_speed * e)                       # sampai di slot "berikutnya" sebelum transisi selesai
            items.append(SceneItem(self._phrases[i + 1], Role.ENTERING, 2.0 - rush, st.next_scale,
                                   st.next_alpha * rush, 0))
        # tanpa baris masuk, panel baris-berikutnya ikut memudar saat baris naik meninggalkannya
        return Scene(t, tuple(items), p, ev.kind, i, visibility=1.0, next_visibility=1.0 if has_next else 1.0 - e)
