"""
ui/tab_settings.py
설정 탭: Ollama vs Google Gemini 선택, Flash 모델 선택, API 키, 사용량/쿼터 링크, 스레드 수, 접이식(Collapsible) 2단계 및 3단계 분석 프롬프트 편집기
"""
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QSpinBox, QTextEdit,
    QPushButton, QMessageBox, QSizePolicy, QRadioButton,
    QButtonGroup,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices

from core.config_manager import load_config, save_config, get_default_prompt, get_stage3_default_prompt
from core.ollama_client import OllamaClient
from core.gemini_client import GeminiClient
from ui.widgets import PALETTE, make_separator


class ModelFetchThread(QThread):
    """백그라운드에서 Ollama 모델 목록을 가져오는 스레드"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        try:
            client = OllamaClient(self.url)
            models = client.list_models()
            self.finished.emit(models)
        except Exception as e:
            self.error.emit(str(e))


class GeminiModelFetchThread(QThread):
    """백그라운드에서 구글 Generative Language API의 실시간 서비스 Gemini 모델 목록을 가져오는 스레드"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key

    def run(self):
        try:
            client = GeminiClient(self.api_key)
            models = client.list_models()
            self.finished.emit(models)
        except Exception as e:
            self.error.emit(str(e))


class GeminiPingThread(QThread):
    """백그라운드에서 Gemini API 키 유효성을 테스트하는 스레드"""
    finished = pyqtSignal(bool, str)

    def __init__(self, api_key: str, model_name: str = "gemini-3.1-flash-lite"):
        super().__init__()
        self.api_key = api_key
        self.model_name = model_name

    def run(self):
        try:
            client = GeminiClient(self.api_key)
            ok, msg = client.test_connection(self.model_name)
            self.finished.emit(ok, msg)
        except Exception as e:
            self.finished.emit(False, f"❌ 연결 오류: {e}")


class SettingsTab(QWidget):
    config_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = load_config()
        self._fetch_thread: ModelFetchThread | None = None
        self._gemini_fetch_thread: GeminiModelFetchThread | None = None
        self._ping_thread: GeminiPingThread | None = None
        self._build_ui()
        self._load_values()

    # ──────────────────────────────────────────
    # UI 구성
    # ──────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(0)

        # ── 엔진 선택 섹션 ──
        root.addWidget(self._section_label("분석 엔진 선택"))
        root.addSpacing(8)

        engine_box = QHBoxLayout()
        self.engine_group = QButtonGroup(self)

        self.radio_ollama = QRadioButton("🦙 Ollama (로컬 LLM)")
        self.radio_gemini = QRadioButton("✨ Google Gemini (Flash 계열 고성능/비용절감 API)")

        self.radio_ollama.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {PALETTE['text_primary']};")
        self.radio_gemini.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {PALETTE['accent']};")

        self.engine_group.addButton(self.radio_ollama, 1)
        self.engine_group.addButton(self.radio_gemini, 2)

        engine_box.addWidget(self.radio_ollama)
        engine_box.addSpacing(24)
        engine_box.addWidget(self.radio_gemini)
        engine_box.addStretch()
        root.addLayout(engine_box)
        root.addSpacing(16)

        self.radio_ollama.toggled.connect(self._on_engine_changed)

        root.addWidget(make_separator())
        root.addSpacing(16)

        # ── Ollama 설정 섹션 ──
        self.ollama_widget = QWidget()
        ollama_layout = QVBoxLayout(self.ollama_widget)
        ollama_layout.setContentsMargins(0, 0, 0, 0)
        ollama_layout.setSpacing(0)

        ollama_layout.addWidget(self._section_label("Ollama 서버 설정"))
        ollama_layout.addSpacing(8)

        ollama_layout.addWidget(self._field_label("서버 URL"))
        url_row = QHBoxLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("http://localhost:11434")
        url_row.addWidget(self.url_edit)
        ollama_layout.addLayout(url_row)
        ollama_layout.addSpacing(12)

        ollama_layout.addWidget(self._field_label("Ollama 모델 선택"))
        model_row = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(220)
        self.model_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        model_row.addWidget(self.model_combo)
        self.refresh_btn = QPushButton("모델 목록 새로고침")
        self.refresh_btn.setProperty("class", "secondary")
        self.refresh_btn.setFixedWidth(160)
        self.refresh_btn.clicked.connect(self._fetch_models)
        model_row.addWidget(self.refresh_btn)
        ollama_layout.addLayout(model_row)

        self.model_status_label = QLabel("")
        self.model_status_label.setProperty("class", "muted")
        ollama_layout.addWidget(self.model_status_label)

        root.addWidget(self.ollama_widget)

        # ── Gemini 설정 섹션 ──
        self.gemini_widget = QWidget()
        gemini_layout = QVBoxLayout(self.gemini_widget)
        gemini_layout.setContentsMargins(0, 0, 0, 0)
        gemini_layout.setSpacing(0)

        gemini_header_row = QHBoxLayout()
        gemini_header_row.addWidget(self._section_label("Google Gemini API 설정 (Flash 전용)"))
        gemini_header_row.addStretch()

        self.btn_open_usage = QPushButton("📊 Gemini 사용량 대시보드 ↗")
        self.btn_open_usage.setProperty("class", "secondary")
        self.btn_open_usage.setStyleSheet(f"""
            QPushButton {{
                color: {PALETTE['accent']};
                border: 1px solid {PALETTE['accent']};
                font-weight: 600;
                font-size: 12px;
                padding: 4px 10px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {PALETTE['bg_tertiary']};
            }}
        """)
        self.btn_open_usage.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://aistudio.google.com/app/usage")))

        self.btn_open_quota = QPushButton("💳 쿼터/결제 관리 ↗")
        self.btn_open_quota.setProperty("class", "secondary")
        self.btn_open_quota.setStyleSheet(f"""
            QPushButton {{
                color: {PALETTE['text_secondary']};
                border: 1px solid {PALETTE['border']};
                font-weight: 600;
                font-size: 12px;
                padding: 4px 10px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {PALETTE['bg_tertiary']};
            }}
        """)
        self.btn_open_quota.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://aistudio.google.com/app/plan_information")))

        gemini_header_row.addWidget(self.btn_open_usage)
        gemini_header_row.addSpacing(6)
        gemini_header_row.addWidget(self.btn_open_quota)

        gemini_layout.addLayout(gemini_header_row)
        gemini_layout.addSpacing(8)

        gemini_layout.addWidget(self._field_label("Gemini API 키 (Google AI Studio 발급)"))
        key_row = QHBoxLayout()
        self.gemini_key_edit = QLineEdit()
        self.gemini_key_edit.setEchoMode(QLineEdit.Password)
        self.gemini_key_edit.setPlaceholderText("AQ.Ab...")
        key_row.addWidget(self.gemini_key_edit)

        self.toggle_key_btn = QPushButton("👁 보이기")
        self.toggle_key_btn.setProperty("class", "secondary")
        self.toggle_key_btn.setFixedWidth(90)
        self.toggle_key_btn.clicked.connect(self._toggle_key_visibility)
        key_row.addWidget(self.toggle_key_btn)

        self.test_key_btn = QPushButton("API 키 테스트")
        self.test_key_btn.setProperty("class", "secondary")
        self.test_key_btn.setFixedWidth(110)
        self.test_key_btn.clicked.connect(self._test_gemini_key)
        key_row.addWidget(self.test_key_btn)

        gemini_layout.addLayout(key_row)
        self.gemini_status_label = QLabel("")
        self.gemini_status_label.setProperty("class", "muted")
        gemini_layout.addWidget(self.gemini_status_label)
        gemini_layout.addSpacing(12)

        gemini_model_header = QHBoxLayout()
        gemini_model_header.addWidget(self._field_label("Gemini 모델 선택 (구글 실시간 서비스 모델 자동 동기화)"))
        gemini_model_header.addStretch()

        self.btn_fetch_gemini = QPushButton("✨ 최신 Gemini 모델 조회")
        self.btn_fetch_gemini.setProperty("class", "secondary")
        self.btn_fetch_gemini.setStyleSheet(f"""
            QPushButton {{
                color: {PALETTE['accent']};
                border: 1px solid {PALETTE['accent']};
                font-weight: 700;
                font-size: 12px;
                padding: 3px 10px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {PALETTE['bg_tertiary']};
            }}
        """)
        self.btn_fetch_gemini.clicked.connect(self._fetch_gemini_models)
        gemini_model_header.addWidget(self.btn_fetch_gemini)
        gemini_layout.addLayout(gemini_model_header)

        self.gemini_model_combo = QComboBox()
        self.gemini_model_combo.setEditable(True)  # 자유 모델명 직접 입력 허용!
        self.gemini_model_combo.addItems([
            "gemini-3.7-flash (🚀 3.7세대 Flash / 최신 초고속 고성능 추천)",
            "gemini-3.5-flash-lite (✨ 3.5세대 Flash Lite / 최신 최저비용 추천)",
            "gemini-3.1-flash-lite (✨ 3.1세대 Flash Lite)",
            "gemini-2.5-flash (⚡ 2.5세대 Flash)",
            "gemini-2.5-flash-lite (⚡ 2.5세대 Flash Lite)",
            "gemini-2.0-flash (⚡ 2.0세대 Flash / 초고속)",
            "gemini-1.5-flash (⚡ 1.5세대 Flash / 표준)",
        ])
        gemini_layout.addWidget(self.gemini_model_combo)

        root.addWidget(self.gemini_widget)
        root.addSpacing(16)

        root.addWidget(make_separator())
        root.addSpacing(14)

        # ── 1단계 Whisper STT 설정 섹션 ──
        root.addWidget(self._section_label("1단계 Whisper STT 음성인식 설정"))
        root.addSpacing(8)

        whisper_row = QHBoxLayout()
        whisper_row.setSpacing(16)

        v_box1 = QVBoxLayout()
        v_box1.setSpacing(4)
        v_box1.addWidget(self._field_label("Whisper 모델 사이즈"))
        self.whisper_model_combo = QComboBox()
        self.whisper_model_combo.addItems([
            "base (⚡ 빠른 속도 / 추천)",
            "small (⚖ 균형형)",
            "medium (🎯 고정밀)",
            "large-v3 (🏆 최고 정확도)",
        ])
        v_box1.addWidget(self.whisper_model_combo)
        whisper_row.addLayout(v_box1)

        v_box2 = QVBoxLayout()
        v_box2.setSpacing(4)
        v_box2.addWidget(self._field_label("연산 가속 디바이스"))
        self.whisper_device_combo = QComboBox()
        self.whisper_device_combo.addItems([
            "auto (자동 - CUDA GPU 우선)",
            "cuda (NVIDIA GPU 가속)",
            "cpu (CPU 전용 모드)",
        ])
        v_box2.addWidget(self.whisper_device_combo)
        whisper_row.addLayout(v_box2)

        root.addLayout(whisper_row)
        root.addSpacing(16)

        root.addWidget(make_separator())
        root.addSpacing(14)

        # ── 공통 설정 (스킵 용량, 스레드) ──
        root.addWidget(self._field_label("스킵 기준 최소 파일 용량 (바이트)"))
        skip_row = QHBoxLayout()
        self.skip_spin = QSpinBox()
        self.skip_spin.setMinimum(0)
        self.skip_spin.setMaximum(1048576)
        self.skip_spin.setSingleStep(64)
        self.skip_spin.setFixedWidth(110)
        skip_hint = QLabel("이 용량 이하의 파일은 '내용 부족'으로 스킵합니다. (예: 512 B ≒ 0.5 KB)")
        skip_hint.setProperty("class", "muted")
        skip_row.addWidget(self.skip_spin)
        skip_row.addWidget(skip_hint)
        skip_row.addStretch()
        root.addLayout(skip_row)
        root.addSpacing(12)

        root.addWidget(self._field_label("동시 처리 스레드 수"))
        thread_row = QHBoxLayout()
        self.thread_spin = QSpinBox()
        self.thread_spin.setMinimum(1)
        self.thread_spin.setMaximum(8)
        self.thread_spin.setFixedWidth(80)
        hint = QLabel("권장: 1 (유료/무료 부하 고려)")
        hint.setProperty("class", "muted")
        thread_row.addWidget(self.thread_spin)
        thread_row.addWidget(hint)
        thread_row.addStretch()
        root.addLayout(thread_row)
        root.addSpacing(16)

        root.addWidget(make_separator())
        root.addSpacing(14)

        # ── [접이식 패널 1] 2단계 기본 분석 프롬프트 ──
        self.btn_toggle_prompt = QPushButton("▶  📝 2단계 기본 분석 프롬프트 보기 / 편집하기 (클릭하여 펼치기)")
        self.btn_toggle_prompt.setProperty("class", "secondary")
        self.btn_toggle_prompt.setStyleSheet(f"""
            QPushButton {{
                color: {PALETTE['text_primary']};
                background-color: {PALETTE['bg_secondary']};
                border: 1px solid {PALETTE['border']};
                font-weight: 700;
                font-size: 13px;
                padding: 10px 14px;
                border-radius: 6px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {PALETTE['bg_tertiary']};
                border: 1px solid {PALETTE['accent']};
            }}
        """)
        self.btn_toggle_prompt.clicked.connect(self._toggle_prompt_panel)
        root.addWidget(self.btn_toggle_prompt)
        root.addSpacing(8)

        # 2단계 프롬프트 팝업/접이식 컨테이너
        self.prompt_container_widget = QWidget()
        prompt_box_layout = QVBoxLayout(self.prompt_container_widget)
        prompt_box_layout.setContentsMargins(0, 0, 0, 0)
        prompt_box_layout.setSpacing(6)

        prompt_hint = QLabel("상담 텍스트(STT)는 분석 시 프롬프트 하단에 자동으로 결합되어 전달됩니다.")
        prompt_hint.setProperty("class", "muted")
        prompt_box_layout.addWidget(prompt_hint)

        self.prompt_edit = QTextEdit()
        self.prompt_edit.setMinimumHeight(200)
        self.prompt_edit.setPlaceholderText("2단계 분석 프롬프트를 입력하세요...")
        prompt_box_layout.addWidget(self.prompt_edit)

        # 기본값 초기화 버튼
        self.reset_btn = QPushButton("2단계 기본 프롬프트로 초기화")
        self.reset_btn.setProperty("class", "secondary")
        self.reset_btn.setFixedWidth(200)
        self.reset_btn.clicked.connect(self._reset_prompt)
        prompt_box_layout.addWidget(self.reset_btn)

        self.prompt_container_widget.setVisible(False)  # 초기 상태: 접힘 (Hidden)
        root.addWidget(self.prompt_container_widget)
        root.addSpacing(12)

        # ── [접이식 패널 2] 3단계 재분석 및 call_type 분류 전용 프롬프트 ──
        self.btn_toggle_stage3 = QPushButton("▶  🔍 3단계 재분석/분류 전용 프롬프트 보기 / 편집하기 (클릭하여 펼치기)")
        self.btn_toggle_stage3.setProperty("class", "secondary")
        self.btn_toggle_stage3.setStyleSheet(f"""
            QPushButton {{
                color: #F59E0B;
                background-color: {PALETTE['bg_secondary']};
                border: 1px solid #F59E0B;
                font-weight: 700;
                font-size: 13px;
                padding: 10px 14px;
                border-radius: 6px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {PALETTE['bg_tertiary']};
            }}
        """)
        self.btn_toggle_stage3.clicked.connect(self._toggle_stage3_prompt_panel)
        root.addWidget(self.btn_toggle_stage3)
        root.addSpacing(8)

        # 3단계 프롬프트 팝업/접이식 컨테이너
        self.stage3_container_widget = QWidget()
        stage3_box_layout = QVBoxLayout(self.stage3_container_widget)
        stage3_box_layout.setContentsMargins(0, 0, 0, 0)
        stage3_box_layout.setSpacing(6)

        stage3_hint = QLabel("3단계 수행 시 미검출(증상0/조치0) 건에 대해 call_type(REPAIR/INQUIRY/IRRELEVANT)을 정밀 판별하는 전용 프롬프트입니다.")
        stage3_hint.setProperty("class", "muted")
        stage3_box_layout.addWidget(stage3_hint)

        self.stage3_prompt_edit = QTextEdit()
        self.stage3_prompt_edit.setMinimumHeight(200)
        self.stage3_prompt_edit.setPlaceholderText("3단계 재분석 전용 프롬프트를 입력하세요...")
        stage3_box_layout.addWidget(self.stage3_prompt_edit)

        self.reset_stage3_btn = QPushButton("3단계 기본 프롬프트로 초기화")
        self.reset_stage3_btn.setProperty("class", "secondary")
        self.reset_stage3_btn.setFixedWidth(200)
        self.reset_stage3_btn.clicked.connect(self._reset_stage3_prompt)
        stage3_box_layout.addWidget(self.reset_stage3_btn)

        self.stage3_container_widget.setVisible(False)  # 초기 상태: 접힘 (Hidden)
        root.addWidget(self.stage3_container_widget)
        root.addSpacing(16)

        # ── 하단 설정 저장 버튼 ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.save_btn = QPushButton("설정 저장")
        self.save_btn.setFixedWidth(140)
        self.save_btn.setMinimumHeight(36)
        self.save_btn.clicked.connect(self._save_settings)
        btn_row.addWidget(self.save_btn)
        root.addLayout(btn_row)

    # ──────────────────────────────────────────
    # 내부 메서드 & 접이식 핸들러
    # ──────────────────────────────────────────
    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(text.upper())
        lbl.setProperty("class", "section-title")
        return lbl

    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {PALETTE['text_secondary']}; font-size: 12px; margin-bottom: 2px; white-space: nowrap;")
        return lbl

    def _toggle_prompt_panel(self):
        """2단계 프롬프트 접기/펼치기 토글"""
        is_visible = self.prompt_container_widget.isVisible()
        self.prompt_container_widget.setVisible(not is_visible)
        if not is_visible:
            self.btn_toggle_prompt.setText("▼  📝 2단계 기본 분석 프롬프트 접기")
        else:
            self.btn_toggle_prompt.setText("▶  📝 2단계 기본 분석 프롬프트 보기 / 편집하기 (클릭하여 펼치기)")

    def _toggle_stage3_prompt_panel(self):
        """3단계 프롬프트 접기/펼치기 토글"""
        is_visible = self.stage3_container_widget.isVisible()
        self.stage3_container_widget.setVisible(not is_visible)
        if not is_visible:
            self.btn_toggle_stage3.setText("▼  🔍 3단계 재분석/분류 전용 프롬프트 접기")
        else:
            self.btn_toggle_stage3.setText("▶  🔍 3단계 재분석/분류 전용 프롬프트 보기 / 편집하기 (클릭하여 펼치기)")

    def _on_engine_changed(self):
        is_ollama = self.radio_ollama.isChecked()
        self.ollama_widget.setVisible(is_ollama)
        self.gemini_widget.setVisible(not is_ollama)

    def _toggle_key_visibility(self):
        if self.gemini_key_edit.echoMode() == QLineEdit.Password:
            self.gemini_key_edit.setEchoMode(QLineEdit.Normal)
            self.toggle_key_btn.setText("🔒 숨기기")
        else:
            self.gemini_key_edit.setEchoMode(QLineEdit.Password)
            self.toggle_key_btn.setText("👁 보이기")

    def _test_gemini_key(self):
        key = self.gemini_key_edit.text().strip()
        if not key:
            QMessageBox.warning(self, "입력 오류", "Gemini API 키를 입력해주세요.")
            return
        selected_model_raw = self.gemini_model_combo.currentText()
        selected_model = selected_model_raw.split(" ")[0].strip()

        self.test_key_btn.setEnabled(False)
        self.gemini_status_label.setText("Gemini API 키 테스트 중...")
        self._ping_thread = GeminiPingThread(key, selected_model)
        self._ping_thread.finished.connect(self._on_gemini_ping_finished)
        self._ping_thread.start()

    def _on_gemini_ping_finished(self, success: bool, msg: str):
        self.test_key_btn.setEnabled(True)
        self.gemini_status_label.setText(msg)

    def _load_values(self):
        engine = self.config.get("engine_type", "ollama")
        if engine == "gemini":
            self.radio_gemini.setChecked(True)
        else:
            self.radio_ollama.setChecked(True)
        self._on_engine_changed()

        self.url_edit.setText(self.config.get("ollama_url", "http://localhost:11434"))
        self.gemini_key_edit.setText(self.config.get("gemini_api_key", ""))

        saved_g_model = self.config.get("gemini_model", "gemini-3.5-flash-lite")
        found = False
        for i in range(self.gemini_model_combo.count()):
            if saved_g_model in self.gemini_model_combo.itemText(i):
                self.gemini_model_combo.setCurrentIndex(i)
                found = True
                break
        if not found:
            self.gemini_model_combo.setCurrentIndex(0)

        saved_w_model = self.config.get("whisper_model", "base")
        for i in range(self.whisper_model_combo.count()):
            if saved_w_model in self.whisper_model_combo.itemText(i):
                self.whisper_model_combo.setCurrentIndex(i)
                break

        saved_w_device = self.config.get("whisper_device", "auto")
        for i in range(self.whisper_device_combo.count()):
            if saved_w_device in self.whisper_device_combo.itemText(i):
                self.whisper_device_combo.setCurrentIndex(i)
                break

        self.skip_spin.setValue(self.config.get("skip_bytes", 512))
        self.thread_spin.setValue(self.config.get("threads", 1))
        self.prompt_edit.setPlainText(self.config.get("prompt", get_default_prompt()))
        self.stage3_prompt_edit.setPlainText(self.config.get("stage3_prompt", get_stage3_default_prompt()))

        # 저장된 Ollama 모델 목록 로드 및 Gemma 3 / Qwen 3 표준 추천 목록
        saved_list = self.config.get("model_list", [])
        saved_model = self.config.get("model", "gemma3:12b")

        default_recommendations = [
            "gemma3:12b (✨ Google Gemma 3 12B / 한국어 요약 최적 추천)",
            "gemma3:4b (⚡ Google Gemma 3 4B / 초경량 초고속)",
            "gemma3:27b (🏆 Google Gemma 3 27B / 고성능)",
            "qwen3:8b (🦙 Qwen 3 8B / JSON 스키마 구조화 추천)",
            "qwen3:30b (🧠 Qwen 3 30B / 대형 모델)",
        ]

        self.model_combo.clear()
        if saved_list:
            self.model_combo.addItems(saved_list)
            if saved_model in saved_list:
                self.model_combo.setCurrentText(saved_model)
            elif saved_model:
                self.model_combo.addItem(saved_model)
                self.model_combo.setCurrentText(saved_model)
            self.model_status_label.setText(f"✅ 저장된 {len(saved_list)}개 모델 로드됨")
        else:
            self.model_combo.addItems(default_recommendations)
            self.model_combo.setCurrentIndex(0)
            self.model_status_label.setText("💡 추천 로컬 모델 목록 (새로고침 버튼으로 실제 Ollama 모델 동기화 가능)")

    def _fetch_gemini_models(self):
        key = self.gemini_key_edit.text().strip()
        if not key:
            QMessageBox.warning(self, "입력 오류", "Google Gemini API 키를 먼저 입력해주세요.")
            return
        self.btn_fetch_gemini.setEnabled(False)
        self.gemini_status_label.setText("구글 서버에서 실시간 서비스 모델 목록을 조회하는 중...")
        self._gemini_fetch_thread = GeminiModelFetchThread(key)
        self._gemini_fetch_thread.finished.connect(self._on_gemini_models_loaded)
        self._gemini_fetch_thread.error.connect(self._on_gemini_models_error)
        self._gemini_fetch_thread.start()

    def _on_gemini_models_loaded(self, models: list[str]):
        self.btn_fetch_gemini.setEnabled(True)
        if not models:
            self.gemini_status_label.setText("⚠️ 조회된 실시간 서비스 모델이 없습니다. API 키를 확인하세요.")
            return
        curr = self.gemini_model_combo.currentText().split(" ")[0].strip()
        self.gemini_model_combo.clear()
        self.gemini_model_combo.addItems(models)
        if curr in models:
            self.gemini_model_combo.setCurrentText(curr)
        self.gemini_status_label.setText(f"✅ 구글 실시간 서비스 제공 중인 {len(models)}개 Gemini 모델 동기화 완료")

    def _on_gemini_models_error(self, err_msg: str):
        self.btn_fetch_gemini.setEnabled(True)
        self.gemini_status_label.setText(f"⚠ 구글 모델 조회 실패: {err_msg}")

    def _fetch_models(self):
        url = self.url_edit.text().strip() or "http://localhost:11434"
        self.refresh_btn.setEnabled(False)
        self.model_status_label.setText("Ollama 서버에서 모델 목록을 가져오는 중...")
        self._fetch_thread = ModelFetchThread(url)
        self._fetch_thread.finished.connect(self._on_models_loaded)
        self._fetch_thread.error.connect(self._on_models_error)
        self._fetch_thread.start()

    def _on_models_loaded(self, models: list[str]):
        self.refresh_btn.setEnabled(True)
        if not models:
            self.model_status_label.setText("설치된 모델이 없습니다.")
            return
        saved_model = self.config.get("model", "")
        self.model_combo.clear()
        self.model_combo.addItems(models)
        if saved_model in models:
            self.model_combo.setCurrentText(saved_model)
        self.model_status_label.setText(f"✅ {len(models)}개 모델 로드 완료")

    def _on_models_error(self, error_msg: str):
        self.refresh_btn.setEnabled(True)
        self.model_status_label.setText(f"⚠ 연결 실패: {error_msg}")

    def _reset_prompt(self):
        reply = QMessageBox.question(
            self, "초기화 확인",
            "2단계 프롬프트를 기본값으로 초기화하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.prompt_edit.setPlainText(get_default_prompt())

    def _reset_stage3_prompt(self):
        reply = QMessageBox.question(
            self, "초기화 확인",
            "3단계 재분석 전용 프롬프트를 기본값으로 초기화하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.stage3_prompt_edit.setPlainText(get_stage3_default_prompt())

    def _save_settings(self):
        engine_type = "gemini" if self.radio_gemini.isChecked() else "ollama"
        url = self.url_edit.text().strip()
        model = self.model_combo.currentText()
        gemini_key = self.gemini_key_edit.text().strip()
        
        gemini_model_raw = self.gemini_model_combo.currentText()
        gemini_model = gemini_model_raw.split(" ")[0].strip()

        skip_bytes = self.skip_spin.value()
        threads = self.thread_spin.value()
        prompt = self.prompt_edit.toPlainText().strip()
        stage3_prompt = self.stage3_prompt_edit.toPlainText().strip()

        if engine_type == "ollama" and not url:
            QMessageBox.warning(self, "입력 오류", "Ollama 서버 URL을 입력해주세요.")
            return
        if engine_type == "gemini" and not gemini_key:
            QMessageBox.warning(self, "입력 오류", "Google Gemini API 키를 입력해주세요.")
            return
        if not prompt:
            QMessageBox.warning(self, "입력 오류", "2단계 프롬프트를 입력해주세요.")
            return

        w_model_raw = self.whisper_model_combo.currentText()
        whisper_model = w_model_raw.split(" ")[0].strip()
        w_device_raw = self.whisper_device_combo.currentText()
        whisper_device = w_device_raw.split(" ")[0].strip()

        current_models = [
            self.model_combo.itemText(i)
            for i in range(self.model_combo.count())
            if not self.model_combo.itemText(i).startswith("──")
        ]

        self.config.update({
            "engine_type": engine_type,
            "ollama_url": url,
            "model": model,
            "model_list": current_models,
            "gemini_api_key": gemini_key,
            "gemini_model": gemini_model,
            "whisper_model": whisper_model,
            "whisper_device": whisper_device,
            "skip_bytes": skip_bytes,
            "threads": threads,
            "prompt": prompt,
            "stage3_prompt": stage3_prompt,
        })
        save_config(self.config)
        self.config_saved.emit()

        self.save_btn.setText("✅ 저장됨")
        self.save_btn.setEnabled(False)
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(2000, self._restore_save_btn)

    def _restore_save_btn(self):
        self.save_btn.setText("설정 저장")
        self.save_btn.setEnabled(True)

    def get_current_config(self) -> dict:
        engine_type = "gemini" if self.radio_gemini.isChecked() else "ollama"
        gemini_model_raw = self.gemini_model_combo.currentText()
        gemini_model = gemini_model_raw.split(" ")[0].strip()
        w_model_raw = self.whisper_model_combo.currentText()
        whisper_model = w_model_raw.split(" ")[0].strip()
        w_device_raw = self.whisper_device_combo.currentText()
        whisper_device = w_device_raw.split(" ")[0].strip()
        return {
            "engine_type": engine_type,
            "ollama_url": self.url_edit.text().strip(),
            "model": self.model_combo.currentText(),
            "gemini_api_key": self.gemini_key_edit.text().strip(),
            "gemini_model": gemini_model,
            "whisper_model": whisper_model,
            "whisper_device": whisper_device,
            "skip_bytes": self.skip_spin.value(),
            "threads": self.thread_spin.value(),
            "prompt": self.prompt_edit.toPlainText().strip(),
            "stage3_prompt": self.stage3_prompt_edit.toPlainText().strip(),
        }
