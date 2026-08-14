# ConsultParser2 Release Notes

## 🚀 Version v1.2.8.Build.1 (배포 일시: 2026-08-14 15:08)

### 📌 주요 신규 기능 및 개편 사항

1. **[🚀 Google Gemini 3.7 Flash & 2.5 Flash 최신 모델 라인업 전격 탑재]**
   - 최신 **`gemini-3.7-flash`** (3.7세대 초고속 고성능 Flash) 모델 추가
   - `gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-3.5-flash-lite` 등 최신 Flash 시리즈 풀 라인업 완성
   - **자유 직접 입력(Editable Dropdown) 지원**: 드롭다운에 커스텀 신규 모델명을 언제든지 직접 기입 가능하도록 확장

2. **[🐛 분석 시작 시 멈춤(Silent Freeze) 버그 완전 해결]**
   - Gemini API 키 미설정 시 조용히 멈추지 않고 즉시 경고 팝업(`QMessageBox.warning`)으로 원인 안내
   - Ollama 모델 선택 시 순수 모델 ID만 정밀 추출하여 404 및 무한 대기 원천 차단

3. **[⚡ 1단계 STT 지연 로딩 최적화]**
   - 미변환 음성 잔량이 0개일 때는 무거운 Whisper STTEngine 생성을 건너뛰고 **2단계 LLM 분석으로 즉시 초고속 직행**

4. **[🏆 단일 통합 전사 표준 분석 프롬프트 상향 적용]**
   - 2단계 최초 분석 시점부터 `call_type` (`REPAIR` / `INQUIRY` / `IRRELEVANT`)을 100% 필수 판별하는 단일 통합 전사 표준 프롬프트 적용
