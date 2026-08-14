# ConsultParser2 Release Notes

## 🚀 Version v1.2.5.Build.1 (배포 일시: 2026-08-14 10:11)

### 📌 주요 신규 기능 및 헌장 준수 개편 사항

1. **[📝 분석 프롬프트 접이식(Collapsible Accordion) UI 개편]**
   - 설정 탭의 거대한 분석 프롬프트 입력창을 **기본 접힘(Hidden) 상태**로 변경하여 UI 공간을 대폭 확보
   - 필요할 때만 `▶ 📝 2단계 기본 분석 프롬프트 보기 / 편집하기` 버튼을 클릭하여 펼쳐보거나 편집 가능하도록 최상의 UX 적용

2. **[🔍 3단계 재분석/분류 전용 프롬프트 정립 및 편집기 신설]**
   - 3단계 미검출 건(증상0/조치0) 2차 재분석 시 적용되는 **`call_type` (REPAIR / INQUIRY / IRRELEVANT) 전용 판별 프롬프트** 추가 정립
   - 설정 탭 내 `▶ 🔍 3단계 재분석/분류 전용 프롬프트 보기 / 편집하기` 접이식 편집기 신설로 사용자 커스텀 수정 완벽 지원

3. **[🎉 Implementation Plan 3단계 & 4단계 완전 집행 완수]**
   - 4,107개 결과 JSON 파일 전수 100% `"call_type": "REPAIR"` 백필 마이그레이션 및 Supabase DB 전처리 (`merged_consults.json`, `supabase_export.json`, `supabase_seed.sql` 4,388개 디테일 레코드) 완전 생성

4. **[💡 타임스탬프 동기화: txt 파일명을 따라 JSON 파일명 1:1 자동 변경]**
   - `stt_texts/` 내 `.txt` 파일과 `result_json/` 내 기존 `.json` 파일의 타임스탬프(`YYYYMMDD_HHMMSS`)가 동일하면 **txt 파일명을 따라 JSON 파일명을 1:1 자동 변경**하여 완료 수량(4,108건)과 잔량(2,168건) 완전 동기화

5. **[🛑 사용자 중간 중지 시 PC 자동 종료 100% 차단 & 🛑 즉시 취소 버튼 신설]**
