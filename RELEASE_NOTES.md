# ConsultParser2 Release Notes

## 🚀 Version v1.2.7.Build.1 (배포 일시: 2026-08-14 15:06)

### 📌 주요 버그 수정 및 최적화 개편 사항

1. **[🐛 분석 시작 시 멈춤(Silent Freeze) 버그 완전 해결]**
   - **사전 점검 팝업 표출**: Gemini API 키가 비어있거나 Ollama 서버 연결 실패 시 조용히 멈추지 않고 즉시 경고 팝업(`QMessageBox.warning`)으로 원인을 직관적 안내
   - **순수 모델명 자동 정제**: Ollama 모델 선택 문자열(`gemma3:12b (...)`)에서 순수 모델 ID만 정밀 추출하여 API 404/대기 차단

2. **[⚡ 1단계 STT 지연 로딩 최적화]**
   - 미변환 음성 잔량이 0개일 때는 무거운 Whisper STTEngine 생성을 건너뛰고 **2단계 LLM 분석으로 즉시 초고속 직행**

3. **[🏆 단일 통합 전사 표준 분석 프롬프트 상향 적용]**
   - 2단계 최초 분석 시점부터 `call_type` (`REPAIR` / `INQUIRY` / `IRRELEVANT`)을 100% 필수 판별하도록 **단일 통합 전사 표준 분석 프롬프트** 적용

4. **[📝 분석 프롬프트 접이식(Collapsible Accordion) UI 개편]**
   - 설정 탭의 프롬프트 입력창을 **기본 접힘(Hidden) 상태**로 변경하여 깔끔하고 넓은 UI 구현

5. **[🎉 Implementation Plan 3단계 & 4단계 완전 집행 완료]**
   - 4,107개 결과 JSON 파일 전수 100% 스키마 마이그레이션 및 Supabase DB 전처리 (`merged_consults.json`, `supabase_export.json`, `supabase_seed.sql` 4,388개 디테일 레코드) 완전 생성

6. **[💡 타임스탬프 동기화: txt 파일명을 따라 JSON 파일명 1:1 자동 변경]**
   - 타임스탬프(`YYYYMMDD_HHMMSS`)가 동일하면 **txt 파일명을 따라 JSON 파일명을 1:1 자동 변경**하여 수량 동기화
