# ConsultParser2 Release Notes

## 🚀 Version v1.2.0.Build.1 (배포 일시: 2026-08-14 09:46)

### 📌 주요 신규 기능 및 헌장 준수 개편 사항

1. **[1단계 + 2단계 프로세스 원스톱 & 파이프라인 분리]**
   - 1단계: `.m4a` / `.mp3` 음성 ➔ OpenAI Whisper 기반 정형화 `.txt` 변환 및 원본 음성 `completed_audio/` 보관
   - 2단계: `.txt` 대화록 ➔ 선택된 LLM 기반 구조화 `.json` 파싱
   - 작업 모드 선택 라벨 간결화 (`🟢 1+2단계`, `🔵 1단계만`, `🟣 2단계만`)로 UI 글자 잘림 완벽 해결

2. **[2줄 독립 분리형 통계 카드 패널]**
   - 1줄: `🎧 [1단계 STT >> txt]` 대상/잔량/완료/스킵/오류 독립 집계
   - 2줄: `🤖 [2단계 txt >> Json]` 대상/잔량/완료/스킵/오류 독립 집계

3. **[현재 작업 중인 파일 용량(MB/KB) 실시간 표출]**
   - 대용량 음성/텍스트 파일 처리 시 로그 및 상태창에 `(14.8 MB)`, `(42.5 KB)` 등 용량을 표시하여 대기 시간 예측 편익 제공

4. **[3단계: 미검출 건(증상0/조치0) 원문 2차 재분석]**
   - 1단계 오디오 STT 재실행 없이 `stt_texts/*.txt` 원문만 직행 읽기
   - 타 고성능 분석 엔진 지정 재분석 및 통화 성격 분류 라벨(`call_type`: `REPAIR`, `INQUIRY`, `IRRELEVANT`) 갱신

5. **[4단계: 전사 100% JSON 스키마 마이그레이션 & Supabase DB 전처리 수출]**
   - 과거/신규 JSON 100% `"call_type": "REPAIR"` 보완 백필 마이그레이션 (`run_schema_migration`)
   - `merged_consults.json`: 전사 100% 병합 단일 통합 JSON
   - `supabase_export.json`: Supabase Table Editor Bulk Import 전용 File
   - `supabase_seed.sql`: Supabase SQL Editor 실행용 멱등성 `INSERT` 쿼리문 (`consult_records` + `consult_items` 2대 관계형 테이블)

6. **[Google Gemma 3 지원 & Gemini 대시보드 링킹]**
   - Ollama `gemma3:12b`, `gemma3:4b`, `gemma3:27b` 표준 추천 모델 탑재
   - Gemini 사용량 대시보드 및 쿼터/결제 관리 direct link 버튼 연결

7. **[PC 자동 종료 옵션]**
   - 모든 지정 작업 완수 시 60초 안내 후 Windows 시스템 자동 셧다운 기능 탑재
