# ConsultParser2 개발 임시 요구사항 및 완료 이력

## 📌 현재 반영 완료된 요구사항 (v1.2.3.Build.1)
- [x] 타임스탬프 일치 시 txt 파일명 기준으로 JSON 파일명 1:1 자동 변경 동기화 임시 로직
- [x] 사용자 중간 중지 시 PC 자동 종료 100% 차단 로직 (is_user_stopped 감지 및 shutdown /a 자동실행)
- [x] PC 자동 종료 즉시 무력화 버튼 신설 (`🛑 종료 예약 취소 (shutdown /a)`)
- [x] Gemini 사용량 및 쿼터 관리 대시보드 링크 연결
- [x] STT_sample 핵심 파서 포팅: 전화번호 100% 보존 토큰 격리 정규식 파서
- [x] m4a 음성 파일 수십 연도 재귀 폴더 탐색 (scan_folder) 및 completed_audio 이관
- [x] 1단계(음성STT) / 2단계(LLM JSON) 파이프라인 모드 분리
- [x] 지연 폴더 생성 (스캔 시점 폴더 미생성, 작업 실행 시점 생성)
- [x] 입력 폴더와 출력 폴더 동일 시 스캔 무한 루프 방지 (EXCLUDE_DIR_NAMES)
- [x] 작업 처리 중인 파일 용량(MB/KB) 실시간 표시
- [x] 2줄 독립 분리 통계 카드 패널 (1단계/2단계 카운터 분리)
- [x] 라디오 버튼 라벨 간결화 (글자 잘림 완전 해소)
- [x] PC 작업 완료 시 자동 종료 체크박스 (shutdown /s /t 60)
- [x] 3단계: 미검출 건(증상0/조치0) stt_texts/ 원문 2차 재분석 및 call_type 분류
- [x] 4단계: 전사 100% JSON call_type 스키마 백필 마이그레이션 및 Supabase DB 전처리 수출 (merged_consults.json, supabase_export.json, supabase_seed.sql)
- [x] Google Gemma 3 (`gemma3:12b`, `gemma3:4b`, `gemma3:27b`) 추천 모델 탑재
