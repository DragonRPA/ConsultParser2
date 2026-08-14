# ConsultParser2 Release Notes

## 🚀 Version v1.2.9.Build.1 (배포 일시: 2026-08-14 15:11)

### 📌 주요 신규 기능 및 개편 사항

1. **[✨ 구글 Gemini 서비스 모델 실시간 조회 & 자동 동기화 구축]**
   - 구글 REST API (`https://generativelanguage.googleapis.com/v1beta/models`) 연동으로 **구글이 현재 실제 서비스 제공 중인 최신 Gemini 모델 목록을 실시간 자동 동기화**
   - **`✨ 최신 Gemini 모델 조회`** 버튼 추가: 사용자가 일일이 홈페이지를 확인할 필요 없이 클릭 한 번으로 구글의 모든 활성 Gemini 모델(`gemini-3.7-flash`, `gemini-2.5-flash` 등)을 수신 받아 드롭다운에 자동 반영 및 저장

2. **[🚀 Google Gemini 3.7 Flash & 2.5 Flash 최신 모델 라인업 전격 탑재]**
   - 최신 **`gemini-3.7-flash`** (3.7세대 초고속 고성능 Flash) 모델 및 2.5세대 Flash 지원

3. **[🐛 분석 시작 시 멈춤(Silent Freeze) 버그 완전 해결]**
   - Gemini API 키 미설정 시 조용히 멈추지 않고 즉시 경고 팝업(`QMessageBox.warning`)으로 원인 안내

4. **[⚡ 1단계 STT 지연 로딩 최적화]**
   - 미변환 음성 잔량이 0개일 때는 무거운 Whisper STTEngine 생성을 건너뛰고 **2단계 LLM 분석으로 즉시 초고속 직행**
