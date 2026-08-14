"""
ui/widgets.py
공통 위젯 및 스타일 정의
"""
from PyQt5.QtWidgets import QTextEdit, QLabel, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

# ─────────────────────────────────────────────
# 전역 컬러 팔레트 (다크 테마)
# ─────────────────────────────────────────────
PALETTE = {
    "bg_primary":    "#1a1d23",   # 메인 배경
    "bg_secondary":  "#22262f",   # 카드/패널 배경
    "bg_tertiary":   "#2a2f3a",   # 입력 필드 배경
    "border":        "#383d4a",   # 테두리
    "accent":        "#4f8ef7",   # 강조색 (파랑)
    "accent_hover":  "#3a7ae0",   # 강조 호버
    "danger":        "#e05555",   # 위험/중지
    "danger_hover":  "#c43e3e",
    "success":       "#4caf8a",   # 성공/완료
    "warning":       "#f0a050",   # 경고
    "text_primary":  "#e8eaf0",   # 기본 텍스트
    "text_secondary":"#8b92a5",   # 보조 텍스트
    "text_muted":    "#555c6e",   # 흐린 텍스트
}

GLOBAL_STYLESHEET = f"""
/* ── 기본 앱 배경 ── */
QMainWindow, QWidget {{
    background-color: {PALETTE['bg_primary']};
    color: {PALETTE['text_primary']};
    font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
    font-size: 13px;
}}

/* ── 탭 위젯 ── */
QTabWidget::pane {{
    border: 1px solid {PALETTE['border']};
    border-radius: 6px;
    background: {PALETTE['bg_secondary']};
    top: -1px;
}}
QTabBar::tab {{
    background: {PALETTE['bg_tertiary']};
    color: {PALETTE['text_secondary']};
    padding: 8px 24px;
    border: 1px solid {PALETTE['border']};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 500;
    min-width: 100px;
}}
QTabBar::tab:selected {{
    background: {PALETTE['bg_secondary']};
    color: {PALETTE['text_primary']};
    border-bottom: 2px solid {PALETTE['accent']};
}}
QTabBar::tab:hover:!selected {{
    background: {PALETTE['bg_secondary']};
    color: {PALETTE['text_primary']};
}}

/* ── 버튼: 기본 (강조) ── */
QPushButton {{
    background-color: {PALETTE['accent']};
    color: white;
    border: none;
    border-radius: 5px;
    padding: 7px 18px;
    font-weight: 600;
    font-size: 13px;
    white-space: nowrap;
}}
QPushButton:hover {{
    background-color: {PALETTE['accent_hover']};
}}
QPushButton:pressed {{
    background-color: #2d66cc;
}}
QPushButton:disabled {{
    background-color: {PALETTE['bg_tertiary']};
    color: {PALETTE['text_muted']};
}}

/* ── 버튼: 위험(중지) ── */
QPushButton[class="danger"] {{
    background-color: {PALETTE['danger']};
}}
QPushButton[class="danger"]:hover {{
    background-color: {PALETTE['danger_hover']};
}}
QPushButton[class="danger"]:disabled {{
    background-color: {PALETTE['bg_tertiary']};
    color: {PALETTE['text_muted']};
}}

/* ── 버튼: 보조 (secondary) ── */
QPushButton[class="secondary"] {{
    background-color: {PALETTE['bg_tertiary']};
    color: {PALETTE['text_primary']};
    border: 1px solid {PALETTE['border']};
}}
QPushButton[class="secondary"]:hover {{
    background-color: {PALETTE['border']};
}}

/* ── 텍스트 입력 ── */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {PALETTE['bg_tertiary']};
    color: {PALETTE['text_primary']};
    border: 1px solid {PALETTE['border']};
    border-radius: 5px;
    padding: 6px 10px;
    selection-background-color: {PALETTE['accent']};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid {PALETTE['accent']};
}}

/* ── 콤보박스 ── */
QComboBox {{
    background-color: {PALETTE['bg_tertiary']};
    color: {PALETTE['text_primary']};
    border: 1px solid {PALETTE['border']};
    border-radius: 5px;
    padding: 5px 10px;
    min-width: 160px;
}}
QComboBox:focus {{
    border: 1px solid {PALETTE['accent']};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {PALETTE['text_secondary']};
    margin-right: 6px;
}}
QComboBox QAbstractItemView {{
    background-color: {PALETTE['bg_tertiary']};
    color: {PALETTE['text_primary']};
    border: 1px solid {PALETTE['border']};
    selection-background-color: {PALETTE['accent']};
}}

/* ── 스핀박스 ── */
QSpinBox {{
    background-color: {PALETTE['bg_tertiary']};
    color: {PALETTE['text_primary']};
    border: 1px solid {PALETTE['border']};
    border-radius: 5px;
    padding: 5px 10px;
}}
QSpinBox:focus {{
    border: 1px solid {PALETTE['accent']};
}}
QSpinBox::up-button, QSpinBox::down-button {{
    background: {PALETTE['border']};
    width: 18px;
    border: none;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background: {PALETTE['accent']};
}}

/* ── 프로그레스바 ── */
QProgressBar {{
    background-color: {PALETTE['bg_tertiary']};
    border: 1px solid {PALETTE['border']};
    border-radius: 5px;
    height: 16px;
    text-align: center;
    color: {PALETTE['text_primary']};
    font-size: 11px;
    font-weight: 600;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {PALETTE['accent']}, stop:1 #7ab3ff);
    border-radius: 4px;
}}

/* ── 스크롤바 ── */
QScrollBar:vertical {{
    background: {PALETTE['bg_secondary']};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {PALETTE['border']};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {PALETTE['text_muted']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {PALETTE['bg_secondary']};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {PALETTE['border']};
    border-radius: 4px;
    min-width: 30px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ── 라벨 ── */
QLabel {{
    color: {PALETTE['text_primary']};
    background: transparent;
}}
QLabel[class="section-title"] {{
    color: {PALETTE['text_secondary']};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}}
QLabel[class="muted"] {{
    color: {PALETTE['text_muted']};
    font-size: 12px;
}}

/* ── 구분선 ── */
QFrame[frameShape="4"],  /* HLine */
QFrame[frameShape="5"]   /* VLine */ {{
    color: {PALETTE['border']};
}}

/* ── 툴팁 ── */
QToolTip {{
    background-color: {PALETTE['bg_tertiary']};
    color: {PALETTE['text_primary']};
    border: 1px solid {PALETTE['border']};
    padding: 4px 8px;
    border-radius: 4px;
}}
"""


def make_separator() -> QFrame:
    """수평 구분선 위젯을 반환합니다."""
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    return line


class LogTextEdit(QTextEdit):
    """읽기 전용 로그 텍스트 영역"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 11))
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: #141720;
                color: {PALETTE['text_primary']};
                border: 1px solid {PALETTE['border']};
                border-radius: 5px;
                padding: 8px;
            }}
        """)

    def append_log(self, msg: str, level: str = "info") -> None:
        """레벨에 따라 색상을 달리하여 로그를 추가합니다."""
        color_map = {
            "info":    PALETTE['text_primary'],
            "success": PALETTE['success'],
            "warning": PALETTE['warning'],
            "error":   PALETTE['danger'],
            "muted":   PALETTE['text_muted'],
        }
        color = color_map.get(level, PALETTE['text_primary'])
        self.append(f'<span style="color:{color}">{msg}</span>')
        # 자동 스크롤
        sb = self.verticalScrollBar()
        sb.setValue(sb.maximum())
