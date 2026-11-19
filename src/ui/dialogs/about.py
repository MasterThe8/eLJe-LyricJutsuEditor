"""Dialog About."""
from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFrame, QLabel, QTextBrowser, QVBoxLayout

from services.constants import APP_NAME, APP_VERSION
from ui.dialogs.base import BaseDialog
from ui.html_helpers import gradient_html
from ui.theme import Theme, brand_pixmap_hidpi
from ui.widgets.common import make_button


class AboutDialog(BaseDialog):
    WEBSITE = "https://masterthe8.github.io/eLJe-LyricJutsuEditor/"

    def __init__(self, parent=None, app_name: str = APP_NAME, version: str = APP_VERSION):
        super().__init__("About", icon_name="info", parent=parent, header=False)
        self.setMinimumSize(580, 640)
        self.resize(600, 680)
        self.body.setContentsMargins(0, 0, 0, 0)
        self.body.setSpacing(0)

        hero = QFrame()
        hero.setObjectName("dialogHeader")
        hl = QVBoxLayout(hero)
        hl.setContentsMargins(24, 26, 24, 22)
        hl.setSpacing(6)
        hl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        logo = QLabel()
        logo.setPixmap(brand_pixmap_hidpi(96, self.devicePixelRatioF()))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel(app_name)
        title.setObjectName("dialogTitle")
        title.setStyleSheet("font-size: 21px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pill = QLabel(version)
        pill.setObjectName("versionPill")
        byline = QLabel("A simple software developed by "
                        + gradient_html("MasterThe8", ["#FF3B5C", "#FF3DB4", "#B94DFF", "#6E7BFF", "#4DA3FF"]))
        byline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(logo, 0, Qt.AlignmentFlag.AlignHCenter)
        hl.addSpacing(6)
        hl.addWidget(title)
        hl.addWidget(pill, 0, Qt.AlignmentFlag.AlignHCenter)
        hl.addSpacing(4)
        hl.addWidget(byline)
        self.body.addWidget(hero)

        # Isi (teks asli dari about.py)
        accent = Theme.ACCENT
        n = lambda s: f"<b style='color:{accent}'>{s}</b>"   # noqa: E731
        ismaya = gradient_html("Ismaya Melasrana", ["#00e9ff", "#4bf388", "#a1ff00"])
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setFrameShape(QFrame.Shape.NoFrame)
        self.browser.document().setDocumentMargin(24)
        self.browser.document().setDefaultStyleSheet(
            f"p {{ margin: 0 0 12px 0; }} a {{ color: {accent}; }}")
        self.browser.setHtml(f"""
            <p>This software makes it easy for Clone Hero Charters to edit lyrics from chart files
            (.chart) with a PlainText-based display, and to manipulate lyrics with what is for now
            called “Lyric Jutsu”. It shows the “Events” section of the chart file and highlights
            the syntax of the code, which makes editing and getting creative with lyrics easier.
            Additional features for Lyric Jutsu include “Add Jutsu”, “Batch Jutsu”, “Lyric Color (method 1)”,
            “Lyric Color (method 2)”, and “Kan2Rom”.</p>
            <p><b>Special thanks to</b></p>
            <p>• {n('oriOta')} — the first Charter to discover a unique trick on the lyrics.<br>
               • {ismaya} — Charter and beta tester who provided many references for features.<br>
               • {n('RDYD')} — Developer of intro-no-jutsu, referenced during Live Lyrics Preview development.<br>
               And others.</p>""")
        self.body.addWidget(self.browser, 1)

        self.web_btn = make_button("Website", "ghost")
        self.close_btn = make_button("Close", "primary")
        self.close_btn.setDefault(True)
        self.footer.addWidget(self.web_btn)
        self.footer.addStretch(1)
        self.footer.addWidget(self.close_btn)
        self.web_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.WEBSITE)))
        self.close_btn.clicked.connect(self.accept)
