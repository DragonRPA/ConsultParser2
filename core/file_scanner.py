"""
core/file_scanner.py
입력 상위 폴더 및 하위 모든 연도별 서브폴더의 음성(.m4a, .mp3, .wav) 및 .txt 파일을 재귀 스캔하고 출력 폴더로 매핑합니다.
(※ 타임스탬프 유연 매칭 및 txt 파일명 기준 기존 변형 JSON 1:1 자동 변경 동기화 로직 포함)
"""
import os
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Literal, Callable, Optional

from core.stt_parser import STTFilenameParser


@dataclass
class FileItem:
    original_path: Path                               # 원본 파일 경로 (.m4a, .mp3, .wav, 또는 .txt)
    file_type: Literal["audio", "text"]               # "audio" 또는 "text"
    target_txt_path: Path                             # 1단계 출력 TXT 파일 경로 (stt_texts/YYYYMMDD_HHMMSS_고객명.txt)
    target_json_path: Path                            # 2단계 출력 JSON 파일 경로 (result_json/YYYYMMDD_HHMMSS_고객명.json)
    size_bytes: int                                    # 파일 크기(바이트)
    stt_done: bool                                     # 1단계 STT / 정형화 TXT 변환 이미 완료 여부
    json_done: bool                                    # 2단계 LLM JSON 추출 이미 완료 여부
    skipped_small: bool                                # 크기 미달로 스킵 대상이면 True
    parsed_info: dict = None                           # STTFilenameParser 분석 정보


def read_txt_content(filepath: Path) -> str:
    """텍스트 파일 읽기 (UTF-8 우선, 실패 시 CP949 디코딩, 타임스탬프 필터링)"""
    raw = ""
    try:
        raw = filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            raw = filepath.read_text(encoding="cp949")
        except Exception:
            return ""

    lines = raw.splitlines()
    clean_lines = []
    timestamp_pattern = re.compile(
        r"^(?:\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}|\d{1,2}:\d{2}(?::\d{2})?|\[\d{2}:\d{2}(?::\d{2})?\])\s*"
    )
    for line in lines:
        stripped = timestamp_pattern.sub("", line.strip())
        if stripped:
            clean_lines.append(stripped)
    return "\n".join(clean_lines)


def _build_json_timestamp_map(result_json_dir: Path) -> dict[str, Path]:
    """
    result_json/ 폴더 내에 기존 저장된 JSON 파일들의 타임스탬프(YYYYMMDD_HHMMSS) 색인을 생성합니다.
    """
    ts_map = {}
    if not result_json_dir.exists():
        return ts_map

    ts_pattern = re.compile(r"(\d{8}_\d{6})")

    for json_file in result_json_dir.glob("*.json"):
        match = ts_pattern.search(json_file.name)
        if match:
            ts = match.group(1)
            if ts not in ts_map:
                ts_map[ts] = json_file
    return ts_map


def scan_folder(
    input_folder: str,
    output_folder: str = "",
    skip_bytes: int = 512,
    process_mode: str = "all",  # "all", "stt_only", "llm_only"
    progress_callback: Optional[Callable[[str, str], None]] = None
) -> list[FileItem]:
    """
    input_folder 및 그 하위 모든 서브폴더(연도별/월별 등)를 재귀 탐색(os.walk)하여 FileItem 목록을 반환합니다.
    - progress_callback(message, type)을 통해 하위 탐색 상황을 실시간 리포트합니다.
    - [임시 동기화 로직]: 타임스탬프(YYYYMMDD_HHMMSS)가 일치하는 txt와 기존 변형 JSON이 발견되면 txt 파일명을 따라 JSON 파일명을 1:1 자동 변경합니다.
    """
    if not input_folder or not Path(input_folder).is_dir():
        return []

    input_path = Path(input_folder).resolve()

    if not output_folder:
        output_path = input_path / "result_output"
    else:
        output_path = Path(output_folder).resolve()

    stt_texts_dir = output_path / "stt_texts"
    result_json_dir = output_path / "result_json"
    completed_audio_dir = output_path / "completed_audio"

    # 기존 result_json 타임스탬프 색인 생성
    json_ts_map = _build_json_timestamp_map(result_json_dir)

    items: list[FileItem] = []

    AUDIO_EXTS = {".m4a", ".mp3", ".wav", ".aac", ".flac"}
    TEXT_EXTS = {".txt"}
    EXCLUDE_DIR_NAMES = {"stt_texts", "result_json", "completed_audio", "result_output"}

    if progress_callback:
        progress_callback(f"🔍 하위 폴더 재귀 탐색 시작: {input_path.name}", "info")

    scanned_folders_count = 0
    detected_audio_count = 0
    detected_text_count = 0
    renamed_json_count = 0

    ts_extractor = re.compile(r"(\d{8}_\d{6})")

    # os.walk를 이용한 세분화된 하위 서브폴더 순회
    for root, dirs, files in os.walk(input_path):
        # 결과 저장 전용 폴더(stt_texts, result_json 등)만 순회 대상에서 능동 제외
        dirs[:] = [d for d in dirs if d.lower() not in EXCLUDE_DIR_NAMES]

        root_path = Path(root).resolve()

        scanned_folders_count += 1
        rel_subfolder = root_path.relative_to(input_path)
        sub_desc = str(rel_subfolder) if str(rel_subfolder) != "." else "[상위 루트]"

        folder_audio_in_dir = 0
        folder_text_in_dir = 0

        for f in files:
            orig_file = root_path / f
            ext = orig_file.suffix.lower()

            if ext not in AUDIO_EXTS and ext not in TEXT_EXTS:
                continue

            is_audio = ext in AUDIO_EXTS
            file_type: Literal["audio", "text"] = "audio" if is_audio else "text"

            if is_audio:
                folder_audio_in_dir += 1
                detected_audio_count += 1
            else:
                folder_text_in_dir += 1
                detected_text_count += 1

            try:
                size = orig_file.stat().st_size
            except OSError:
                size = 0

            # 스마트 파일명 파싱
            parsed = STTFilenameParser.parse(orig_file.name)
            target_txt_filename = parsed["new_filename"]
            stem = Path(target_txt_filename).stem
            target_json_filename = f"{stem}.json"

            target_txt_path = stt_texts_dir / target_txt_filename
            target_json_path = result_json_dir / target_json_filename

            completed_audio_path = completed_audio_dir / orig_file.name
            is_stt_done = target_txt_path.exists() or completed_audio_path.exists() or orig_file.parent == stt_texts_dir

            # ---------------------------------------------------------------
            # 💡 [임시 동기화 로직]: 타임스탬프 기준 기존 변형 JSON 1:1 자동 파일명 변경
            # ---------------------------------------------------------------
            is_json_done = target_json_path.exists()

            if not is_json_done:
                ts_match = ts_extractor.search(target_txt_filename)
                if ts_match:
                    ts = ts_match.group(1)
                    if ts in json_ts_map:
                        old_json_file = json_ts_map[ts]
                        if old_json_file.exists() and old_json_file != target_json_path:
                            try:
                                old_json_file.rename(target_json_path)
                                is_json_done = True
                                renamed_json_count += 1
                                json_ts_map[ts] = target_json_path  # 맵 업데이트
                            except Exception:
                                is_json_done = True  # 파일 이동 오류 시에도 존재 인지
                        elif old_json_file.exists():
                            is_json_done = True

            items.append(FileItem(
                original_path=orig_file,
                file_type=file_type,
                target_txt_path=target_txt_path,
                target_json_path=target_json_path,
                size_bytes=size,
                stt_done=is_stt_done,
                json_done=is_json_done,
                skipped_small=(size <= skip_bytes if not is_audio else False),
                parsed_info=parsed
            ))

        # 하위 서브폴더별 감지 현황 알림
        if progress_callback and (folder_audio_in_dir > 0 or folder_text_in_dir > 0 or scanned_folders_count <= 5):
            progress_callback(
                f"  📂 서브폴더 탐색 중: {sub_desc} (음성: {folder_audio_in_dir}개, txt: {folder_text_in_dir}개 감지)",
                "info"
            )

    if renamed_json_count > 0 and progress_callback:
        progress_callback(
            f"🔄 [임시 마이그레이션 실행] 타임스탬프가 동일한 기존 JSON 파일 {renamed_json_count}개의 파일명을 txt 파일명과 1:1 동일하게 동기화 변경했습니다.",
            "success"
        )

    if progress_callback:
        progress_callback(
            f"✅ [하위 탐색 완료] 총 {scanned_folders_count}개 서브폴더 탐색 완료 | "
            f"음성 파일: {detected_audio_count}개, 텍스트 파일: {detected_text_count}개 감지됨 (총 {len(items)}개)",
            "success" if items else "warning"
        )

    # 파일명 기준 정렬
    items.sort(key=lambda x: x.original_path.name)
    return items
