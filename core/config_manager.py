"""
config_manager.py
설정을 config.json 파일로 저장/로드합니다.
"""
import json
import os
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "config.json"

DEFAULT_PROMPT = """다음은 산업용 청소기(습식/건식 바닥청소기) 고객 AS 상담 전화의 STT 전사 텍스트입니다.
대화는 고객(현장 관리자/사용자)과 상담사 간의 대화이며, 음성인식 오류나 맥락이 불분명한 부분이 있을 수 있습니다.

아래 엄격한 작성 규칙에 따라 상담 분석 결과를 오직 순수 JSON 형식으로만 응답하세요.
다른 설명이나 마크다운 코드블록(```)을 절대 포함하지 마세요.

[작성 규칙 - 필수 준수]
1. 100% 순수 한글(한국어)만 사용:
   - 영어 단어(예: mobile number, video, analysis, overtime 등), 한자, 외래어 영문 표기를 일체 금지합니다.
   - 영문 단어는 반드시 완전히 자연스러운 한국어(한글)로 의역/번역하여 작성하세요.
     (예: mobile number → 휴대폰 번호, video → 동영상, analysis → 분석)
2. 줄바꿈 문장 금지:
   - 텍스트 값 내부에 줄바꿈(\\n)을 절대 넣지 말고 매끄러운 한 줄 문장으로 작성하세요.
3. 원문 대화 내용(content)이나 불필요한 단어는 결과 JSON에 포함하지 마세요.

[분석 항목]
- 증상: 분류(예: 흡입불량, 누수, 소음, 부품파손, 전원불량 등), 증상(세부 설명 요약)
- 조치: 유형(예: 원격안내, 사진/동영상요청, 방문예약, 해결완료 등), 조치내용, 결과

증상이나 조치 내용이 없는 경우 빈 배열([])로 작성하세요.

[출력 형식 예시]
{
  "증상": [
    {
      "분류": "흡입불량",
      "증상": "청소기 모터는 작동하지만 바닥의 먼지와 물을 빨아들이지 못함"
    }
  ],
  "조치": [
    {
      "유형": "사진/동영상요청",
      "조치내용": "현장 상태 확인을 위해 증상 동영상 촬영 후 담당자 휴대폰으로 전송 요청",
      "결과": "동영상 확인 후 재통화하여 서비스 안내 예정"
    }
  ]
}"""

DEFAULT_CONFIG = {
    "engine_type": "ollama",            # "ollama" 또는 "gemini"
    "ollama_url": "http://localhost:11434",
    "model": "gemma3:12b",
    "model_list": [],
    "gemini_api_key": "",
    "gemini_model": "gemini-3.5-flash-lite",
    "whisper_model": "base",              # base, small, medium, large-v3
    "whisper_device": "auto",             # auto, cpu, cuda
    "process_mode": "all",                # "all" (1+2단계), "stt_only" (1단계만), "llm_only" (2단계만)
    "threads": 1,
    "skip_bytes": 512,
    "prompt": DEFAULT_PROMPT,
    "last_input_folder": "",
    "last_output_folder": "",
}


def load_config() -> dict:
    """config.json을 읽어 설정 딕셔너리를 반환합니다. 없으면 기본값을 반환합니다."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 새 키가 추가됐을 때 기본값으로 병합
            merged = {**DEFAULT_CONFIG, **data}
            return merged
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)


def save_config(config: dict) -> None:
    """설정 딕셔너리를 config.json에 저장합니다."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


STAGE3_DEFAULT_PROMPT = """다음은 산업용 청소기(습식/건식 바닥청소기) 고객 상담 전화의 STT 전사 텍스트입니다.
대화 내용을 정밀 분석하여 다음 3가지 카테고리 중 하나로 call_type을 판별하고, 증상 및 조치 사항을 순수 JSON 형식으로만 응답하세요.
다른 설명이나 마크다운 코드블록(```)을 절대 포함하지 마세요.

[call_type 분류 기준 - 필수 판별]
1. "REPAIR": 장비 고장, 이상 증상, AS 신청, 수리 및 부품 교체 조치 관련 통화
2. "INQUIRY": 단순 렌탈 단가, 임대료, 견적, 위치, 사무실 연락 등 단순 문의 통화 (장비 고장 없음)
3. "IRRELEVANT": 사적 통화, 개인 잡담, 잘못 걸려온 전화 등 업무 무관 통화

[작성 규칙]
1. 100% 순수 한글(한국어)만 사용: 영문 단어는 반드시 완전히 자연스러운 한글로 의역/번역하여 작성하세요.
2. 텍스트 값 내부에 줄바꿈(\\n)을 넣지 말고 매끄러운 한 줄 문장으로 작성하세요.

[응답 JSON 스키마 예시]
{
  "call_type": "REPAIR",
  "증상": [
    {
      "분류": "흡입불량",
      "증상": "바닥 흡입력이 약해 먼지를 빨아들이지 못함"
    }
  ],
  "조치": [
    {
      "유형": "원격안내",
      "조치내용": "스퀴지 고무 노후 여부 확인 및 세척 안내",
      "결과": "소모품 세척 후 경과 관찰 예정"
    }
  ],
  "summary": "바닥 흡입력 약화 건으로 스퀴지 세척 안내 조치."
}"""


def get_default_prompt() -> str:
    return DEFAULT_PROMPT


def get_stage3_default_prompt() -> str:
    return STAGE3_DEFAULT_PROMPT
