# ConsultParser2 Release Notes

## 🚀 Version v1.2.6.Build.1 (배포 일시: 2026-08-14 10:18)

### 📌 주요 신규 기능 및 헌장 준수 개편 사항

1. **[🏆 단일 통합 전사 표준 분석 프롬프트 상향 적용]**
   - 2단계 최초 분석 시점부터 `call_type` (`REPAIR` / `INQUIRY` / `IRRELEVANT`)을 100% 필수 판별하도록 **단일 통합 전사 표준 분석 프롬프트**로 전격 상향 통합 적용
   - 1차 분석 시점부터 100% 전사 데이터 스키마의 완벽한 일관성과 명확한 성격 라벨링 확보

2. **[📝 분석 프롬프트 접이식(Collapsible Accordion) UI 개편]**
   - 설정 탭의 프롬프트 입력창을 **기본 접힘(Hidden) 상태**로 변경하여 깔끔하고 넓은 UI 구현

3. **[🎉 Implementation Plan 3단계 & 4단계 완전 집행 완료]**
   - 4,107개 결과 JSON 파일 전수 100% 스키마 마이그레이션 및 Supabase DB 전처리 (`merged_consults.json`, `supabase_export.json`, `supabase_seed.sql` 4,388개 디테일 레코드) 완전 생성

4. **[💡 타임스탬프 동기화: txt 파일명을 따라 JSON 파일명 1:1 자동 변경]**
   - 타임스탬프(`YYYYMMDD_HHMMSS`)가 동일하면 **txt 파일명을 따라 JSON 파일명을 1:1 자동 변경**하여 완료 수량(4,108건)과 잔량(2,168건) 완전 동기화

5. **[🛑 사용자 중간 중지 시 PC 자동 종료 100% 차단 & 🛑 즉시 취소 버튼 신설]**
