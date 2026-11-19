"""Template stylesheet (QSS) dan pengisi token warnanya."""
from __future__ import annotations

from ui.theme.tokens import get_active_theme

QSS_TEMPLATE = """
QMainWindow { background: @CHROME@; }
QWidget { color: @TEXT@; }
QToolTip { background: @RAISED@; color: @TEXT@; border: 1px solid @BORDER@; padding: 4px 8px; }

/* ── Menu bar & menu ─────────────────────────── */
QMenuBar { background: @CHROME@; padding: 3px 6px 2px 6px; }
QMenuBar::item { background: transparent; padding: 5px 11px; margin: 0 1px; border-radius: 6px; color: @DIM@; }
QMenuBar::item:selected, QMenuBar::item:pressed { background: @RAISED@; color: @TEXT@; }
QMenu { background: @PANEL@; border: 1px solid @BORDER@; padding: 6px; }
QMenu::item { padding: 7px 30px 7px 12px; border-radius: 5px; color: @TEXT@; }
QMenu::item:selected { background: @RAISED@; }
QMenu::item:disabled { color: @FAINT@; }
QMenu::icon { padding-left: 6px; }
QMenu::separator { height: 1px; background: @BORDER@; margin: 5px 8px; }

/* ── Toolbar ─────────────────────────────────── */
QToolBar { background: @CHROME@; border: none; border-bottom: 1px solid @BORDER@; spacing: 2px; padding: 6px 12px; }
QToolBar::separator { background: @BORDER@; width: 1px; margin: 7px 9px; }
QToolButton { background: transparent; border: none; border-radius: 7px; padding: 7px; color: @DIM@; }
QToolButton:hover { background: @RAISED@; color: @TEXT@; }
QToolButton:pressed { background: @BORDER@; }
QToolButton:checked { background: @ACCENT_SOFT@; color: @ACCENT@; }
QToolButton:disabled { color: @FAINT@; }
QToolButton[chip="true"] { padding: 6px 12px 6px 9px; }

/* ── Dock & splitters ────────────────────────── */
QMainWindow::separator { background: @CHROME@; width: 1px; height: 1px; }
QMainWindow::separator:hover { background: @ACCENT@; }
QSplitter::handle { background: transparent; }
QDockWidget { border: none; }
QFrame#dockLeft { background: @PANEL@; border: none; border-right: 1px solid @BORDER@; }
QFrame#dockRight { background: @PANEL@; border: none; border-left: 1px solid @BORDER@; }
QLabel#panelTitle { font-weight: 600; color: @TEXT@; }
QLabel#panelHint { color: @FAINT@; font-size: 12px; }
QLabel#emptyTitle { font-weight: 600; color: @TEXT@; }
QLabel#emptyText { color: @DIM@; }

/* ── Tabs ────────────────────────────────────── */
QTabWidget { background: @CHROME@; }
QTabWidget::pane { border: none; border-top: 1px solid @BORDER@; background: @EDITOR@; }
QTabWidget::tab-bar { left: 12px; }
QTabBar { background: transparent; }
QTabBar::tab { background: transparent; color: @DIM@; padding: 10px 16px 9px 16px; margin-right: 4px; border-bottom: 2px solid transparent; }
QTabBar::tab:hover { color: @TEXT@; }
QTabBar::tab:selected { color: @TEXT@; border-bottom: 2px solid @ACCENT@; }

/* ── Editor ──────────────────────────────────── */
QPlainTextEdit#plainTextEdit, QTextEdit#richTextEdit {
    background: @EDITOR@; color: @EDITOR_TEXT@; border: none;
    selection-background-color: @SELECTION@; selection-color: @SELECTION_TEXT@; }
QPlainTextEdit#tempText {
    background: @EDITOR@; color: @EDITOR_TEXT@; border: 1px solid @BORDER@; border-radius: 8px;
    padding: 4px; selection-background-color: @SELECTION@; selection-color: @SELECTION_TEXT@; }
QPlainTextEdit#tempText:focus { border-color: @BORDER_HI@; }

/* ── Scrollbar ───────────────────────────────── */
QScrollBar:vertical { background: transparent; width: 12px; margin: 0; }
QScrollBar::handle:vertical { background: @SCROLLBAR@; border-radius: 4px; min-height: 30px; margin: 2px 2px; }
QScrollBar::handle:vertical:hover { background: @SCROLLBAR_HOVER@; }
QScrollBar:horizontal { background: transparent; height: 12px; margin: 0; }
QScrollBar::handle:horizontal { background: @SCROLLBAR@; border-radius: 4px; min-width: 30px; margin: 2px 2px; }
QScrollBar::handle:horizontal:hover { background: @SCROLLBAR_HOVER@; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

/* ── Tree & symbol list ──────────────────────── */
QTreeView { background: transparent; border: none; outline: 0; }
QTreeView::item { padding: 5px 4px; border-radius: 6px; color: @TEXT@; }
QTreeView::item:hover { background: @RAISED@; }
QTreeView::item:selected { background: @ACCENT_SOFT@; color: @TEXT@; }
QListView#symbols { background: transparent; border: none; outline: 0; }
QListView#symbols::item { border-radius: 7px; padding: 4px; color: @TEXT@; }
QListView#symbols::item:hover { background: @RAISED@; }
QListView#symbols::item:selected { background: @ACCENT_SOFT@; color: @ACCENT@; }

/* ── Form controls ───────────────────────────── */
QPushButton { background: @RAISED@; border: 1px solid @BORDER@; border-radius: 7px; padding: 6px 14px; }
QPushButton:hover { border-color: @BORDER_HI@; }
QPushButton:focus { border-color: @ACCENT@; }
QPushButton#primary { background: @ACCENT@; color: @PRIMARY_TEXT@; border: none; font-weight: 600; padding: 7px 16px; }
QPushButton#primary:hover { background: @PRIMARY_HOVER@; }
QComboBox { background: @EDITOR@; border: 1px solid @BORDER@; border-radius: 7px; padding: 5px 10px; }
QComboBox:hover { border-color: @BORDER_HI@; }
QComboBox QAbstractItemView { background: @PANEL@; border: 1px solid @BORDER@; selection-background-color: @RAISED@; outline: 0; }

/* ── Status bar ──────────────────────────────── */
QStatusBar { background: @CHROME@; border-top: 1px solid @BORDER@; color: @DIM@; }
QStatusBar::item { border: none; }
QLabel#statusChip { color: @DIM@; padding: 0 9px; }
QLabel#versionChip { background: @RAISED@; color: @DIM@; border-radius: 9px; padding: 2px 10px; margin: 3px 6px 3px 2px; }

/* ── Dialogs ─────────────────────────────────── */
QDialog { background: @PANEL@; }
QFrame#dialogHeader { background: @CHROME@; border: none; border-bottom: 1px solid @BORDER@; }
QFrame#dialogFooter { background: @CHROME@; border: none; border-top: 1px solid @BORDER@; }
QLabel#dialogTitle { font-size: 17px; font-weight: 600; color: @TEXT@; }
QLabel#dialogSubtitle { color: @DIM@; }
QLabel#fieldLabel { color: @DIM@; }
QLabel#fieldHint { color: @FAINT@; font-size: 12px; }
QLabel#sectionTitle { color: @TEXT@; font-weight: 600; }
QLabel#statusNote { color: @DIM@; }
QLabel#errorNote { color: @DANGER@; }
QLabel#versionPill { background: @RAISED@; color: @DIM@; border-radius: 9px; padding: 2px 10px; }
QFrame#vdivider { background: @BORDER@; border: none; min-width: 1px; max-width: 1px; }
QFrame#hdivider { background: @BORDER@; border: none; min-height: 1px; max-height: 1px; }
QFrame#previewBox { background: @EDITOR@; border: 1px solid @BORDER@; border-radius: 10px; }

QLineEdit, QSpinBox { background: @EDITOR@; color: @EDITOR_TEXT@; border: 1px solid @BORDER@; border-radius: 7px;
    padding: 7px 10px; selection-background-color: @SELECTION@; selection-color: @SELECTION_TEXT@; }
QLineEdit:hover, QSpinBox:hover { border-color: @BORDER_HI@; }
QLineEdit:focus, QSpinBox:focus { border-color: @ACCENT@; }
QLineEdit:disabled { color: @FAINT@; }
QKeySequenceEdit[conflict="true"] QLineEdit { border-color: @DANGER@; }
QCheckBox { spacing: 8px; color: @TEXT@; }
QCheckBox:disabled { color: @FAINT@; }

QPushButton:disabled { color: @FAINT@; background: transparent; border-color: @BORDER@; }
QPushButton#primary:disabled { background: @RAISED@; color: @FAINT@; }
QPushButton#ghost { background: transparent; }
QPushButton#ghost:hover { background: @RAISED@; }
QPushButton#colorField { text-align: left; padding: 6px 14px 6px 10px; }

QListWidget { background: @EDITOR@; border: 1px solid @BORDER@; border-radius: 8px; outline: 0; padding: 4px; }
QListWidget::item { padding: 6px 8px; border-radius: 6px; color: @TEXT@; }
QListWidget::item:hover { background: @RAISED@; }
QListWidget::item:selected { background: @ACCENT_SOFT@; color: @TEXT@; }
QTextBrowser { background: transparent; border: none; selection-background-color: @SELECTION@; }


/* ── Tabel (Batch Jutsu · Lyric Input) ───────── */
QTableWidget { background: @EDITOR@; color: @EDITOR_TEXT@; border: 1px solid @BORDER@; border-radius: 8px;
    gridline-color: @BORDER@; outline: 0; selection-background-color: @ACCENT_SOFT@; selection-color: @TEXT@; }
QTableWidget::item { padding: 4px 8px; }
QTableWidget::item:hover { background: @RAISED@; }
QTableWidget QLineEdit { padding: 2px 6px; border-radius: 4px; }
QHeaderView { background: transparent; }
QHeaderView::section { background: @CHROME@; color: @DIM@; border: none; border-right: 1px solid @BORDER@;
    border-bottom: 1px solid @BORDER@; padding: 6px 10px; }
QTableCornerButton::section { background: @CHROME@; border: none; }

/* ── Jutsu & Symbol ──────────────────────────── */
QPushButton#pill { background: transparent; border: 1px solid @BORDER@; border-radius: 14px; padding: 4px 13px; color: @DIM@; }
QPushButton#pill:hover { color: @TEXT@; border-color: @BORDER_HI@; }
QPushButton#pill:checked { background: @ACCENT_SOFT@; border-color: transparent; color: @ACCENT@; }
QRadioButton { spacing: 9px; color: @DIM@; padding: 4px 0; }
QRadioButton:hover { color: @TEXT@; }
QRadioButton:checked { color: @ACCENT@; font-weight: 600; }
QRadioButton:disabled { color: @FAINT@; }
QLabel:disabled, QLabel#fieldLabel:disabled { color: @FAINT@; }
QLabel#glyphBig { font-size: 30px; color: @TEXT@; }

/* ── Live Lyrics Preview ─────────────────────── */
QMainWindow#liveLyricsPreviewWindow { background: @CHROME@; }
QFrame#previewControls { background: @CHROME@; border: none; border-top: 1px solid @BORDER@; }
QLabel#timeLabel { color: @DIM@; }
QLabel#speedLabel { color: @DIM@; }
QComboBox#speedCombo { padding: 3px 8px; min-width: 52px; }
QLabel#previewNotice { color: @CALLOUT_TEXT@; background: @CALLOUT_BG@; border-top: 1px solid @CALLOUT_BORDER@; padding: 6px 14px; }
QLabel#previewDisclaimer { color: @FAINT@; font-size: 11px; padding: 2px 0; }
QSlider#seekSlider::groove:horizontal { height: 4px; background: @BORDER@; border-radius: 2px; }
QSlider#seekSlider::sub-page:horizontal { background: @ACCENT@; border-radius: 2px; }
QSlider#seekSlider::add-page:horizontal { background: @BORDER@; border-radius: 2px; }
QSlider#seekSlider::handle:horizontal { background: @TEXT@; width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; }
QSlider#seekSlider::handle:horizontal:hover { background: @ACCENT@; }
QSlider#seekSlider::handle:horizontal:disabled { background: @FAINT@; }
QSlider#seekSlider::sub-page:horizontal:disabled { background: @BORDER_HI@; }
QSlider#volumeSlider {
    min-height: 28px;
    background: transparent;
}
QSlider#volumeSlider::groove:horizontal {
    height: 6px;
    background: @BORDER@;
    border-radius: 3px;
}

QSlider#volumeSlider::sub-page:horizontal {
    background: @ACCENT@;
    border-radius: 3px;
}

QSlider#volumeSlider::add-page:horizontal {
    background: @BORDER@;
    border-radius: 3px;
}

QSlider#volumeSlider::handle:horizontal {
    background: @TEXT@;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}

QSlider#volumeSlider::handle:horizontal:hover {
    background: @ACCENT@;
}

QSlider#volumeSlider::handle:horizontal:disabled {
    background: @FAINT@;
}
"""


def build_qss() -> str:
    """Isi QSS_TEMPLATE dengan token tema yang sedang aktif (satu template untuk semua tema).
/* ── Jutsu Editor (accordion) ────────────────── */
QListWidget#jutsuList { background: @EDITOR@; padding: 6px; }
QListWidget#jutsuList::item { padding: 0; margin: 0; background: @PANEL@; border: 1px solid @BORDER@; border-radius: 9px; }
QListWidget#jutsuList::item:hover { background: @RAISED@; border-color: @BORDER_HI@; }
QWidget#jutsuItem, QWidget#jutsuBody { background: transparent; }
QLabel#jutsuTitle { background: transparent; color: @TEXT@; }
QLabel#jutsuSectionLabel { background: transparent; color: @DIM@; font-weight: 600; padding-top: 2px; }
QWidget#jutsuTagBar { background: transparent; }
QToolButton#jutsuTagButton {
    background: @PANEL@; color: @DIM@; border: 1px solid @BORDER@; border-radius: 5px;
    padding: 2px 7px; font-size: 11px; font-weight: 600; }
QToolButton#jutsuTagButton:hover { background: @RAISED@; color: @TEXT@; border-color: @BORDER_HI@; }
QToolButton#jutsuTagButton:pressed { background: @BORDER@; color: @TEXT@; }
QToolButton#jutsuTagButton:disabled { background: @PANEL@; color: @FAINT@; border-color: @BORDER@; }
QPushButton#jutsuToggle { background: transparent; border: none; border-radius: 7px; padding: 0; }
QPushButton#jutsuToggle:hover { background: @BORDER@; }
QPlainTextEdit#jutsuText, QTextEdit#jutsuRichText {
    background: @EDITOR@; color: @EDITOR_TEXT@; border: 1px solid @BORDER@; border-radius: 7px; padding: 4px;
    selection-background-color: @SELECTION@; selection-color: @SELECTION_TEXT@; }
QPlainTextEdit#jutsuText:focus, QTextEdit#jutsuRichText:focus { border-color: @ACCENT@; }
"""
    tokens = get_active_theme()
    qss = QSS_TEMPLATE
    for key in sorted(tokens, key=len, reverse=True):   # EDITOR_TEXT sebelum EDITOR
        qss = qss.replace(f"@{key}@", tokens[key])
    return qss
