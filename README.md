<p align="center">
  <img src="src/assets/icons/logo.png" alt="eLJe logo" width="160">
</p>

<h1 align="center">eLJe | LyricJutsu Editor</h1>

<p align="center">
  A lyrics editor for <b>Clone Hero</b> charters — edit the <code>[Events]</code> section of a <code>.chart</code> file as plain text, preview it, and apply "Lyric Jutsu" effects in a few clicks.
</p>

<p align="center">
  <img alt="Version" src="https://img.shields.io/badge/version-v0.8.8%20-B900FF">
  <img alt="Python" src="https://img.shields.io/badge/python-3.11-blue">
  <img alt="Qt for Python" src="https://img.shields.io/badge/GUI-PySide6-41CD52">
</p>

<p align="center">
  <a href="https://masterthe8.github.io/eLJe-LyricJutsuEditor/">Website</a> ·
  <a href="https://masterthe8.github.io/eLJe-LyricJutsuEditor/guide.html">Guide / Tutorials</a> ·
  <a href="https://github.com/MasterThe8/eLJe-LyricJutsuEditor/releases">Releases</a>
</p>

---

## About

eLJe makes it easy to edit lyrics inside Clone Hero chart files (`.chart`). It shows the `[Events]` section of the chart in a PlainText editor with syntax highlighting, shows how the lyrics will look in-game, and manipulates lyrics with what the community calls **Lyric Jutsu** — adding phrases, coloring syllables, converting kanji to romaji, and more.

Everything outside the `[Events]` body (other sections, their order, spacing and line endings) is left untouched when you save, so opening and saving a chart does not "reshuffle" the original file.

## Features

### Editing

| Feature | What it does |
| --- | --- |
| **PlainText Lyrics** | Shows the `[Events]` syntax of the chart with highlighting (position, value, rich-text tag, event name — colors are configurable). |
| **RichText Lyrics** | Overview of how the lyrics will be displayed in Clone Hero, updated as you type. |
| **Rich-text tag shortcuts** | Insert `<b>`, `<i>`, `<color>`, `<br>`, `<voffset>`, `<smallcaps>`, `<lowercase>`, `<uppercase>`, `<mspace>`, `<cspace>`, `<sub>`, `<sup>` around the selection. |
| **Find / Replace** | `Ctrl+F` / `Ctrl+H`. |
| **Song Chart Directory** | Dockable file tree of your song folder; click a `.chart` to open it. |
| **TempText + Symbol Picker** | A scratch-pad (like Notepad) and a clickable symbol list; click a symbol to copy it. |
| **Safe saving** | Only the `[Events]` body is replaced. The original encoding (and BOM) is reused; if a new character can't be encoded, it falls back to UTF-8 and tells you. Unsaved changes are checked on exit. |

### Tools

| Tool | What it does |
| --- | --- |
| **Color Picker** | Pick a color and get its code for `<color=#RRGGBB>`. |
| **Get Symbol** | Symbols that work in Clone Hero lyrics (list comes from `assets/symbols/CH_Lyric_Symbols.txt`). |
| **Weird Text Generator** | Converts text into 26 decorative alphabets (`assets/weird_text/wt1 … wt26`). Edit or add styles by changing those files. |

### Jutsu (lyric effects)

| Jutsu | What it does |
| --- | --- |
| **Add Jutsu** | Basic lyric manipulation: ends the current phrase and starts a new one containing your lyric. |
| **Batch Jutsu** | Add Jutsu for many lines at once — by a single phrase, a list of ticks, or a tick range. |
| **Lyric Color no Jutsu (method 1)** | Colors a whole phrase with a simpler method (one opening and one closing color tag). |
| **Lyric Color no Jutsu (method 2)** | Colors a phrase syllable by syllable by creating a `color` tag for each one. |
| **Kan2Rom no Jutsu** | Like method 2, but the remaining text comes from a line you type (e.g. kanji, Hangeul, or another writing system); syllable counts must match. |
| **Jutsu Editor** | Scans the script for existing Jutsu blocks and lists them as an accordion. Edit each block's lyric values or full script and **Apply** — the main editor is updated in a single undo step. |

### Live Lyrics Preview

A separate window (`Alt+L`) that plays the chart's audio and shows the lyrics in sync, including the "slide-up" phrase transitions.

- The audio file comes from `MusicStream` in the chart's `[Song]` section and is resolved **relative to the chart's folder** (absolute paths, drive letters and `..` are rejected).
- Timing is computed from the `[SyncTrack]` tempo map (120 BPM is assumed if there is none at tick 0).
- Play / Pause / Stop / Seek. Audio is played through Qt Multimedia, so supported formats depend on the codecs available on your system.

### Settings

Appearance (5 themes: **Default Dark, Dracula, Nord, Tokyo Night, AMOLED Black**), Font, Highlight colors, LyricJutsu symbols (closing lyric `-`, hidden lyric `_` by default) and Hotkeys. Settings are saved automatically and invalid values fall back to defaults per key.

## Installation

### Requirements

- **Python 3.11+**
- **Windows** (developed and tested on Windows; Linux/macOS should work but are not officially supported)
- The Python packages in [`requirements.txt`](requirements.txt): `PySide6` and `chardet`

### Run from source

```bash
git clone https://github.com/MasterThe8/eLJe-LyricJutsuChartEditor.git
cd eLJe-LyricJutsuChartEditor

python -m venv .venv

# Windows (PowerShell) — use .venv\Scripts\activate.bat for cmd.exe
.venv\Scripts\Activate.ps1

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
python src/app.py
```

> Run `python src/app.py` **from the repository root**. Running `python -m src` is not supported yet, because the modules inside `src/` use absolute imports (for example `from services.constants import ...`).

### Build a Windows executable

The repository ships a PyInstaller spec ([`eLJe.spec`](eLJe.spec)) that bundles the app icon and the `src/assets` folder (symbols, Weird Text alphabets, logo).

```bash
pip install -r requirements.txt pyinstaller
pyinstaller --clean --noconfirm eLJe.spec
```

The result is `dist/eLJe/eLJe.exe` (one folder, recommended for Qt apps).

To build a single-file executable instead:

```powershell
# PowerShell
$env:ELJE_ONEFILE = "1"
pyinstaller --clean --noconfirm eLJe.spec
```

```bat
:: cmd.exe
set ELJE_ONEFILE=1
pyinstaller --clean --noconfirm eLJe.spec
```

The single file is written to `dist/eLJe.exe`. It starts slower because the Qt runtime is unpacked on every launch.

Settings are stored by Qt in the registry under `HKEY_CURRENT_USER\Software\MasterThe8\eLJe`.

## Quick start

1. **Open** a chart: `File → Open` (`Ctrl+O`) or click it in the *Song Chart Directory* panel. The `[Events]` body appears in the **PlainText Lyrics** tab.
2. Edit the events, or use the **Jutsu** menu in the toolbar (`Alt+1` … `Alt+5`).
3. Check the result in **RichText Lyrics**, the **Jutsu Editor** (`Alt+J`) or **Live Preview** (`Alt+L`).
4. **Save** with `Ctrl+S`.

An `[Events]` body looks like this:

```
768 = E "phrase_start"
768 = E "lyric Hold"
864 = E "lyric the"
960 = E "lyric <color=#FF5E9C>light</color>"
1152 = E "phrase_end"
```

### Default shortcuts

All of the following can be changed in `Setting → Hotkey`.

| Action | Shortcut | Action | Shortcut |
| --- | --- | --- | --- |
| Jutsu Editor | `Alt+J` | Add Jutsu | `Alt+1` |
| Live Preview | `Alt+L` | Batch Jutsu | `Alt+2` |
| RichText Lyrics panel | `Alt+D` | Lyric Color (method 1) | `Alt+3` |
| Directory panel | `Alt+Q` | Lyric Color (method 2) | `Alt+4` |
| TempText panel | `Alt+E` | Kan2Rom | `Alt+5` |
| Color Picker | `Alt+A` | Bold / Italic | `Ctrl+B` / `Ctrl+I` |
| Get Symbol | `Alt+S` | `<color>` tag | `Ctrl+L` |
| Weird Text Generator | `Alt+W` | `<br>` tag | `Ctrl+K` |

Open / Save / Find / Replace are `Ctrl+O` / `Ctrl+S` / `Ctrl+F` / `Ctrl+H`; zoom is `Ctrl+=` and `Ctrl+-`.

## Project structure

```
src/
├── app.py                  # entry point (QApplication, settings, theme, main window)
├── assets/
│   ├── icons/              # app logo: logo.png + 32/64/128/256 .ico
│   ├── symbols/            # CH_Lyric_Symbols.txt (Get Symbol / Symbol Picker)
│   ├── weird_text/         # wt1 … wt26 (Weird Text Generator alphabets)
│   └── ascii/              # misc.txt (text-face snippets; not loaded by the app yet)
├── core/                   # pure Python, no GUI imports
│   ├── chart/              # .chart parser, writer, document model, event utilities, encoding detection
│   ├── lyrics/             # lyric event parser, rich-text tags, HTML renderer, Jutsu model
│   ├── operations/         # Add / Batch / Lyric Color 1 & 2 / Kan2Rom, Jutsu scanner
│   ├── preview/            # Live Preview logic: audio resolver, timing engine, transitions, controller
│   └── text_tools/         # symbol list + Weird Text readers
├── services/               # constants, defaults, persistent settings (QSettings), asset paths
├── ui/                     # PySide6 GUI: main window, dialogs, widgets, theme system, Live Preview window font, unsaved changes)
```

The app is intentionally split in two: `core` holds all the logic and can be tested without Qt, while `ui` is a thin layer on top of it. New themes are added in `src/ui/theme/themes/` and registered in that package's `__init__.py`.

## Credits

Special thanks to:

- **[oriOta](https://www.youtube.com/@oriOta)** — the first Charter to discover a unique trick on the lyrics.
- **[Ismaya Melasrana](https://www.youtube.com/@Ismayamelasrana2)** — Charter and beta tester who provided many references for features.
- **[RDYD](https://github.com/rdyd/intro-no-jutsu)** — developer of *intro-no-jutsu*, referenced during Live Lyrics Preview development.
- …and many others.

## License

Released under the [MIT License](LICENSE) — Copyright © MasterThe8.

eLJe depends on third-party packages that are installed separately and keep their own licenses (for example PySide6 and chardet); please review them if you redistribute a built executable.

---

<p align="center">A simple software developed by <b>MasterThe8</b></p>
