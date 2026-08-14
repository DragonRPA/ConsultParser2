"""
parser.py
LLM 응답 텍스트를 파싱하여 구조화된 딕셔너리로 변환합니다.
"""
import json
import re
from datetime import datetime
from pathlib import Path


def parse_llm_response(
    raw_response: str,
    file_path: Path,
    model_name: str,
) -> dict:
    """
    LLM 응답을 파싱하여 최종 저장용 딕셔너리를 반환합니다.

    Args:
        raw_response: Ollama에서 받은 원본 텍스트
        file_path: 원본 .txt 파일 경로
        model_name: 사용된 모델명

    Returns:
        저장할 JSON 데이터 딕셔너리
    """
    # 파일명에서 메타데이터 추출
    stem = file_path.stem  # 예: F0001-20260506_090340_광양프런티어밸리7차관리사무실_S7PST
    site_name, model_code = _extract_meta_from_filename(stem)

    base_meta = {
        "file_name": stem,
        "analyzed_at": datetime.now().isoformat(timespec="seconds"),
        "model_used": model_name,
        "contact_info": {
            "site_name": site_name,
            "model": model_code,
        },
    }

    # JSON 파싱 시도
    parsed = _try_parse_json(raw_response)

    if parsed is not None:
        # 원문 대화 내용(content) 관련 키 제거 보장
        for key in ["content", "Content", "CONTENT", "상담내용", "원문", "대화내용"]:
            parsed.pop(key, None)

        # 텍스트 내 불필요한 줄바꿈(\\n) 및 다중 공백 자동 정돈
        parsed = _clean_text_values(parsed)
        result = {**base_meta, **parsed, "processing_status": "success"}
    else:
        # 파싱 실패 시 원본 응답 보존
        result = {
            **base_meta,
            "symptoms": [],
            "actions": [],
            "summary": "",
            "raw_response": raw_response,
            "processing_status": "parse_error",
        }

    return result


def _clean_text_values(data):
    """딕셔너리/리스트 내의 문자열 항목에서 줄바꿈(\\n)을 제거하고 깔끔한 한 줄 텍스트로 정돈합니다."""
    if isinstance(data, dict):
        return {k: _clean_text_values(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_clean_text_values(elem) for elem in data]
    elif isinstance(data, str):
        # 줄바꿈을 공백으로 바꾸고 연달은 공백 정리
        cleaned = re.sub(r"\s+", " ", data).strip()
        return cleaned
    return data


def _try_parse_json(text: str) -> dict | None:
    """텍스트에서 JSON을 추출합니다. 실패하면 None을 반환합니다."""
    # 1차 시도: 전체 텍스트를 그대로 파싱
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2차 시도: 코드블록(``` ```) 제거 후 파싱
    code_block = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if code_block:
        try:
            return json.loads(code_block.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 3차 시도: 첫 번째 { ... } 블록 추출
    match = re.search(r"(\{[\s\S]*\})", text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    return None


def _extract_meta_from_filename(stem: str) -> tuple[str, str]:
    """
    파일명에서 현장명과 모델코드를 추출합니다.
    예: F0001-20260506_090340_광양프런티어밸리7차관리사무실_S7PST
     → site_name="광양프런티어밸리7차관리사무실", model="S7PST"

    파일명 패턴: F####-YYYYMMDD_HHMMSS_현장명_모델코드
    """
    try:
        # F####- 와 날짜시간 제거
        parts = stem.split("_", 2)  # ['F0001-20260506', '090340', '광양프런티어밸리7차관리사무실_S7PST']
        if len(parts) >= 3:
            remainder = parts[2]  # '광양프런티어밸리7차관리사무실_S7PST'
            # 마지막 _ 기준으로 현장명과 모델코드 분리
            last_under = remainder.rfind("_")
            if last_under != -1:
                site_name = remainder[:last_under]
                model_code = remainder[last_under + 1:]
            else:
                site_name = remainder
                model_code = ""
        else:
            site_name = stem
            model_code = ""
    except Exception:
        site_name = stem
        model_code = ""

    return site_name, model_code
