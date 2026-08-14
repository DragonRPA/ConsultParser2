# ConsultParser2 개발 임시 요구사항 및 완료 이력

## 📌 현재 반영 완료된 요구사항 (v1.2.9.Build.1)
- [x] 구글 Gemini API 실시간 서비스 모델 자동 동기화 (`list_models()` 및 `✨ 최신 Gemini 모델 조회` 버튼)
- [x] Google Gemini 3.7 Flash (`gemini-3.7-flash`), 2.5 Flash 최신 모델 라인업 전격 탑재 및 자유 직접 입력 Editable 드롭다운 지원
- [x] 분석 시작 시 멈춤(Silent Freeze) 버그 완전 해결 (사전 검증 팝업 및 순수 모델명 파싱)
- [x] 1단계 STT 미변환 잔량 0건 시 Whisper STTEngine 지연 로딩 최적화
- [x] 2단계/3단계 단일 통합 전사 표준 분석 프롬프트 (call_type 상향 포함) 전격 적용
- [x] 분석 프롬프트 접이식(Collapsible Accordion) UI 개편 (보고 싶을 때만 펼쳐보기)
- [x] 3단계 재분석 전용 프롬프트 정립 및 편집기 신설 (call_type REPAIR/INQUIRY/IRRELEVANT 전용 판별)
- [x] Implementation Plan 4단계 완전 집행 완료 (4,107개 전수 call_type 백필, merged_consults.json, supabase_export.json, supabase_seed.sql 4,388건 디테일 생성)
- [x] Implementation Plan 3단계 미검출 분석 조사 완료 (1,976건 미검출 대상 추출)
- [x] 타임스탬프 일치 시 txt 파일명 기준으로 JSON 파일명 1:1 자동 변경 동기화 임시 로직
- [x] 사용자 중간 중지 시 PC 자동 종료 100% 차단 로직 (is_user_stopped 감지 및 shutdown /a 자동실행)
- [x] PC 자동 종료 즉시 무력화 버튼 신설 (`🛑 종료 예약 취소 (shutdown /a)`)
- [x] Gemini 사용량 및 쿼터 관리 대시보드 링크 연결
- [x] STT_sample 핵심 파서 포팅: 전화번호 100% 보존 토큰 격리 정규식 파서
- [x] m4a 음성 파일 수십 연도 재귀 폴더 탐색 (scan_folder) 및 completed_audio 이관
- [x] 1단계(음성STT) / 2단계(LLM JSON) 파이프라인 모드 분리
- [x] 작업 처리 중인 파일 용량(MB/KB) 실시간 표시
- [x] 2줄 독립 분리 통계 카드 패널 (1단계/2단계 카운터 분리)
- [x] 라디오 버튼 라벨 간결화 (글자 잘림 완전 해소)
- [x] PC 작업 완료 시 자동 종료 체크박스 (shutdown /s /t 60)
- [x] Google Gemma 3 (`gemma3:12b`, `gemma3:4b`, `gemma3:27b`) 추천 모델 탑재
