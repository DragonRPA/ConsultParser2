"""
ui/main_window.py
메인 윈도우: 탭 컨테이너 + 타이틀바
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.tab_settings import SettingsTab
from ui.tab_process import ProcessTab
from ui.widgets import PALETTE, GLOBAL_STYLESHEET


class MainWindow(QMainWindow):
    APP_TITLE   = "ConsultParser2"
    APP_VERSION = "v1.0.0"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{self.APP_TITLE}  —  고객 상담 STT 분석기")
        self.setMinimumSize(820, 720)
        self.resize(940, 800)
        self.setStyleSheet(GLOBAL_STYLESHEET)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── 헤더 배너 ──
        header = QWidget()
        header.setFixedHeight(54)
        header.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a1d23,
                    stop:0.5 #1e2230,
                    stop:1 #1a1d23
                );
                border-bottom: 1px solid {PALETTE['border']};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)

        # 앱 타이틀
        title_lbl = QLabel(self.APP_TITLE)
        title_font = QFont("Malgun Gothic", 15, QFont.Bold)
        title_lbl.setFont(title_font)
        title_lbl.setStyleSheet(f"color: {PALETTE['accent']}; border: none;")

        # 부제목
        sub_lbl = QLabel("고객 상담 STT 자동 분석 시스템")
        sub_lbl.setStyleSheet(f"color: {PALETTE['text_muted']}; font-size: 12px; border: none;")

        # 버전
        ver_lbl = QLabel(self.APP_VERSION)
        ver_lbl.setStyleSheet(f"color: {PALETTE['text_muted']}; font-size: 11px; border: none;")

        header_layout.addWidget(title_lbl)
        header_layout.addSpacing(12)
        header_layout.addWidget(sub_lbl)
        header_layout.addStretch()
        header_layout.addWidget(ver_lbl)
        root.addWidget(header)

        # ── 탭 영역 ──
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(16, 16, 16, 16)

        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(False)

        # 설정 탭 먼저 생성 (처리 탭이 참조)
        self.settings_tab = SettingsTab()
        self.process_tab  = ProcessTab(settings_tab=self.settings_tab)

        self.tab_widget.addTab(self.process_tab,  "  처리  ")
        self.tab_widget.addTab(self.settings_tab, "  설정  ")

        # 설정 저장 시 처리 탭 자동 동기화
        self.settings_tab.config_saved.connect(self._on_config_saved)

        tab_layout.addWidget(self.tab_widget)
        root.addWidget(tab_container)

        # ── 하단 상태바 ──
        status_bar = QWidget()
        status_bar.setFixedHeight(26)
        status_bar.setStyleSheet(f"""
            QWidget {{
                background: {PALETTE['bg_secondary']};
                border-top: 1px solid {PALETTE['border']};
            }}
        """)
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(16, 0, 16, 0)
        status_lbl = QLabel("준비 완료. 처리 탭에서 폴더를 선택하고 분석을 시작하세요.")
        status_lbl.setStyleSheet(f"color: {PALETTE['text_muted']}; font-size: 11px; border: none;")
        status_layout.addWidget(status_lbl)
        root.addWidget(status_bar)

    def _on_config_saved(self):
        folder = self.process_tab.folder_edit.text().strip()
        if folder:
            self.process_tab._refresh_file_stats(folder)
