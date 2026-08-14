# ConsultParser2 Release Notes

## 🚀 Version v1.2.4.Build.1 (배포 일시: 2026-08-14 10:10)

### 📌 주요 신규 기능 및 Implementation Plan 실행 완료 사항

1. **[🎉 Implementation Plan 4단계 완전 집행 완료]**
   - **4,107개 결과 JSON 파일 전수 100% 스키마 마이그레이션**: 단 1건의 예외 없이 `"call_type": "REPAIR"` (또는 `"INQUIRY"`) 백필 보완 완전 집행 완료
   - **단일 통합 JSON 병합 (`merged_consults.json`)**: 4,026건의 분석 완료 상담 데이터 단일 파일 병합 완료
   - **Supabase DB 전처리 수출 패키징**: 4,388개 상세 증상/조치 디테일을 대량 임포트할 수 있는 `supabase_export.json` 및 `supabase_seed.sql` 전처리 생성 완수

2. **[🔍 Implementation Plan 3단계 미검출 분석 조사 완료]**
   - 4,026건의 분석 완료 파일 중 **1,976건의 미검출 건(증상0/조치0)** 능동 필터링 추출
   - GUI 내 `[3단계] 미검출 건 타 엔진 재분석` 버튼을 클릭하면 타 분석 엔진으로 2차 정밀 분석 수행 준비 완료

3. **[💡 타임스탬프 동기화: txt 파일명을 따라 JSON 파일명 1:1 자동 변경]**
   - `stt_texts/` 내 `.txt` 파일과 `result_json/` 내 기존 `.json` 파일의 타임스탬프(`YYYYMMDD_HHMMSS`)가 동일하면, **txt 파일명을 따라 JSON 파일명을 1:1 자동 변경**하여 완료 수량(4,108건)과 잔량(2,168건) 완전 동기화

4. **[🛑 사용자 중간 중지 시 PC 자동 종료 100% 차단]**
   - 사용자가 "■ 중지" 버튼 클릭 시 `shutdown /a`를 자동 가동하여 PC 셧다운을 무조건 100% 차단

5. **[🛑 PC 자동 종료 즉시 취소 버튼 (shutdown /a) 신설]**
   - 60초 PC 셧다운 예약 타이머 동작 중 언제든지 클릭 시 즉시 무력화하는 전용 버튼 장착
