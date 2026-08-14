"""
core/file_scanner.py
입력 상위 폴더 및 하위 모든 연도별 서브폴더의 음성(.m4a, .mp3, .wav) 및 .txt 파일을 재귀 스캔하고 출력 폴더로 매핑합니다.
(※ 사용자 명시적 '파일명 점검 및 수정' 버튼 지시 시에만 1:1 파일명 동기화 변경 집행)
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


def norm_ts(raw_ts: str) -> str:
    """6자리 연도(YYMMDD_HHMMSS)를 8자리 연도(20YYMMDD_HHMMSS)로 호환 정규화합니다."""
    if not raw_ts:
        return ""
    parts = raw_ts.split("_")
    if len(parts) == 2:
        date_p, time_p = parts[0], parts[1]
        if len(date_p) == 6:
            date_p = "20" + date_p
        return f"{date_p}_{time_p}"
    return raw_ts


# 💡 (00~23시)(00~59분)(00~59초) 엄격 시분초 정밀 타임스탬프 추출 정규식
STRICT_TS_PATTERN = re.compile(
    r"(?:^|[_\s-])((?:20\d{2}|\d{2})(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])_(?:[01]\d|2[0-3])[0-5]\d[0-5]\d)(?:[_\s.-]|$)"
)


def extract_timestamp_from_filename(filename: str, valid_ts_map: Optional[dict] = None) -> str:
    """
    파일명에서 YYYYMMDD_HHMMSS 또는 YYMMDD_HHMMSS 타임스탬프를 100% 무결하게 추출합니다.
    valid_ts_map이 제공될 경우 매칭되는 타임스탬프를 슬라이딩 윈도우 방식으로 최우선 선택합니다.
    """
    candidates = []

    # 1. 8자리_6자리 (YYYYMMDD_HHMMSS)
    for m in re.findall(r"(\d{8}_\d{6})", filename):
        candidates.append(norm_ts(m))

    # 2. 언더바/공백/하이픈 구분 6자리 토큰 슬라이딩 윈도우 (YYMMDD_HHMMSS)
    subparts = re.split(r"[_,\s-]+", Path(filename).stem)
    for i in range(len(subparts) - 1):
        p1, p2 = subparts[i], subparts[i + 1]
        if len(p1) == 6 and len(p2) == 6 and p1.isdigit() and p2.isdigit():
            candidates.append(norm_ts(f"{p1}_{p2}"))

    candidates = list(dict.fromkeys(candidates))

    if valid_ts_map and candidates:
        for c in candidates:
            if c in valid_ts_map:
                return c

    # 3. 엄격 시분초 정규식 fallback
    strict_matches = STRICT_TS_PATTERN.findall(filename)
    if strict_matches:
        for m in reversed(strict_matches):
            ts = norm_ts(m)
            if valid_ts_map and ts in valid_ts_map:
                return ts
        if not candidates:
            return norm_ts(strict_matches[-1])

    return candidates[-1] if candidates else ""


def _build_json_timestamp_map(result_json_dir: Path) -> dict[str, Path]:
    """
    result_json/ 폴더 내에 기존 저장된 JSON 파일들의 타임스탬프(YYYYMMDD_HHMMSS) 색인을 생성합니다.
    """
    ts_map = {}
    if not result_json_dir.exists():
        return ts_map

    for json_file in result_json_dir.glob("*.json"):
        ts = extract_timestamp_from_filename(json_file.name)
        if ts and ts not in ts_map:
            ts_map[ts] = json_file
    return ts_map


def _build_txt_timestamp_map(stt_texts_dir: Path) -> dict[str, Path]:
    """
    stt_texts/ 폴더 내에 기존 변환된 TXT 파일들의 타임스탬프(YYYYMMDD_HHMMSS) 색인을 생성합니다.
    """
    ts_map = {}
    if not stt_texts_dir.exists():
        return ts_map

    for txt_file in stt_texts_dir.glob("*.txt"):
        ts = extract_timestamp_from_filename(txt_file.name)
        if ts and ts not in ts_map:
            ts_map[ts] = txt_file
    return ts_map


def scan_folder(
    input_folder: str,
    output_folder: str = "",
    skip_bytes: int = 512,
    process_mode: str = "all",  # "all", "stt_only", "llm_only"
    progress_callback: Optional[Callable[[str, str], None]] = None
) -> list[FileItem]:
    """
    input_folder 및 그 하위 모든 서브폴더를 재귀 탐색(os.walk)하여 FileItem 목록을 반환합니다.
    (※ 백그라운드 탐색 시에는 파일명을 마음대로 자동 변경하지 않으며 매핑 및 완료 여부만 인지합니다)
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

    txt_ts_map = _build_txt_timestamp_map(stt_texts_dir)
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

    for root, dirs, files in os.walk(input_path):
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

            parsed = STTFilenameParser.parse(orig_file.name)
            target_txt_filename = parsed["new_filename"]
            stem = Path(target_txt_filename).stem
            target_json_filename = f"{stem}.json"

            target_txt_path = stt_texts_dir / target_txt_filename
            target_json_path = result_json_dir / target_json_filename

            ts = extract_timestamp_from_filename(orig_file.name)

            if is_audio and ts and ts in txt_ts_map:
                matched_txt = txt_ts_map[ts]
                target_txt_path = matched_txt
                stem = matched_txt.stem
                target_json_filename = f"{stem}.json"
                target_json_path = result_json_dir / target_json_filename

            completed_audio_path = completed_audio_dir / orig_file.name
            is_stt_done = (
                target_txt_path.exists()
                or completed_audio_path.exists()
                or (ts and ts in txt_ts_map)
                or orig_file.parent == stt_texts_dir
            )

            is_json_done = target_json_path.exists()
            if not is_json_done and ts and ts in json_ts_map:
                is_json_done = True

            items.append(FileItem(
                original_path=orig_file,
                file_type=file_type,
                target_txt_path=target_txt_path,
                target_json_path=target_json_path,
                size_bytes=size,
                stt_done=is_stt_done,
                json_done=is_json_done,
                skipped_small=(size == 0 or size <= skip_bytes if not is_audio else False),
                parsed_info=parsed
            ))

        if progress_callback and (folder_audio_in_dir > 0 or folder_text_in_dir > 0 or scanned_folders_count <= 5):
            progress_callback(
                f"  📂 서브폴더 탐색 중: {sub_desc} (음성: {folder_audio_in_dir}개, txt: {folder_text_in_dir}개 감지)",
                "info"
            )

    if progress_callback:
        progress_callback(
            f"✅ [하위 탐색 완료] 총 {scanned_folders_count}개 서브폴더 탐색 완료 | "
            f"음성 파일: {detected_audio_count}개, 텍스트 파일: {detected_text_count}개 감지됨 (총 {len(items)}개)",
            "success" if items else "warning"
        )

    items.sort(key=lambda x: x.original_path.name)
    return items


def _get_unique_path(target_path: Path) -> Path:
    """동일 경로에 이미 파일이 존재할 경우 파일명_1, 파일명_2로 고유 경로를 생성합니다."""
    if not target_path.exists():
        return target_path
    parent = target_path.parent
    stem = target_path.stem
    ext = target_path.suffix
    counter = 1
    while True:
        new_path = parent / f"{stem}_{counter}{ext}"
        if not new_path.exists():
            return new_path
        counter += 1


def sync_filenames_by_timestamp(
    input_folder: str,
    output_folder: str = "",
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> tuple[int, int]:
    """
    사용자가 '🛠️ 파일명 점검 및 수정' 버튼을 클릭했을 때 명시적으로 집행되는 정형화 동기화 함수입니다.
    - txt 파일명 기준으로 동일 타임스탬프를 가진 음성(.m4a) 및 JSON(.json) 파일명을 1:1로 리네임 수정합니다.
    - progress_callback: (done_count, total_targets, status_message) 수신
    - Returns: (수정 완료된 총 파일 수, 검색된 전체 변경 대상 수)
    """
    if not input_folder or not Path(input_folder).is_dir():
        return 0, 0

    input_path = Path(input_folder).resolve()
    output_path = Path(output_folder).resolve() if output_folder else (input_path / "result_output")

    stt_texts_dir = output_path / "stt_texts"
    result_json_dir = output_path / "result_json"

    txt_ts_map = _build_txt_timestamp_map(stt_texts_dir)
    json_ts_map = _build_json_timestamp_map(result_json_dir)

    AUDIO_EXTS = {".m4a", ".mp3", ".wav", ".aac", ".flac"}
    EXCLUDE_DIR_NAMES = {"stt_texts", "result_json", "result_output"}

    # 1. 변경 대상 작업 수집
    rename_tasks: list[tuple[Path, Path]] = []  # (old_file_path, new_file_path)

    # 1-A. input_folder 원본 폴더 내 음성 파일 수집
    for root, dirs, files in os.walk(input_path):
        dirs[:] = [d for d in dirs if d.lower() not in EXCLUDE_DIR_NAMES]
        root_path = Path(root).resolve()

        for f in files:
            orig_file = root_path / f
            ext = orig_file.suffix.lower()

            if ext not in AUDIO_EXTS:
                continue

            ts = extract_timestamp_from_filename(orig_file.name, valid_ts_map=txt_ts_map)
            if ts and ts in txt_ts_map:
                matched_txt = txt_ts_map[ts]
                clean_stem = matched_txt.stem.replace(" ", "_")
                clean_stem = re.sub(r"_+", "_", clean_stem)
                expected_audio_name = f"{clean_stem}{ext}"

                # 이미 완벽 일치하거나 중복 번호(_1, _2 등)가 부여된 경우 핑퐁 반복 차단!
                is_already_synced = (
                    orig_file.name == expected_audio_name
                    or re.match(r"^" + re.escape(clean_stem) + r"_\d+" + re.escape(ext) + r"$", orig_file.name)
                )
                if not is_already_synced:
                    target_path = _get_unique_path(root_path / expected_audio_name)
                    if orig_file != target_path:
                        rename_tasks.append((orig_file, target_path))

    # 1-B. completed_audio 출력 보관 폴더 내 음성 파일 전수 수집 및 동기화
    completed_audio_dir = output_path / "completed_audio"
    if completed_audio_dir.exists():
        for audio_file in completed_audio_dir.glob("*.*"):
            ext = audio_file.suffix.lower()
            if ext in AUDIO_EXTS:
                ts = extract_timestamp_from_filename(audio_file.name, valid_ts_map=txt_ts_map)
                if ts and ts in txt_ts_map:
                    matched_txt = txt_ts_map[ts]
                    clean_stem = matched_txt.stem.replace(" ", "_")
                    clean_stem = re.sub(r"_+", "_", clean_stem)
                    expected_audio_name = f"{clean_stem}{ext}"

                    is_already_synced = (
                        audio_file.name == expected_audio_name
                        or re.match(r"^" + re.escape(clean_stem) + r"_\d+" + re.escape(ext) + r"$", audio_file.name)
                    )
                    if not is_already_synced:
                        target_path = _get_unique_path(completed_audio_dir / expected_audio_name)
                        if audio_file != target_path:
                            rename_tasks.append((audio_file, target_path))

    # 1-C. JSON 파일 변경 대상 수집
    if result_json_dir.exists():
        for json_file in result_json_dir.glob("*.json"):
            ts = extract_timestamp_from_filename(json_file.name, valid_ts_map=txt_ts_map)
            if ts and ts in txt_ts_map:
                matched_txt = txt_ts_map[ts]
                clean_stem = matched_txt.stem.replace(" ", "_")
                clean_stem = re.sub(r"_+", "_", clean_stem)
                expected_json_name = f"{clean_stem}.json"

                is_already_synced = (
                    json_file.name == expected_json_name
                    or re.match(r"^" + re.escape(clean_stem) + r"_\d+\.json$", json_file.name)
                )
                if not is_already_synced:
                    target_json_path = _get_unique_path(result_json_dir / expected_json_name)
                    if json_file != target_json_path:
                        rename_tasks.append((json_file, target_json_path))

    total_targets = len(rename_tasks)
    if total_targets == 0:
        if progress_callback:
            progress_callback(0, 0, "✅ 모든 음성/JSON 파일명이 txt 기준 100% 정형화 동기화되어 있습니다. 수정할 파일이 없습니다.")
        return 0, 0

    # 2. 프로그레스 콜백 연동 리네임 집행
    completed_count = 0
    for idx, (old_path, new_path) in enumerate(rename_tasks, start=1):
        try:
            old_path.rename(new_path)
            completed_count += 1
            if progress_callback:
                progress_callback(idx, total_targets, f"🔄 [동기화 리네임 중] {old_path.name} ➔ {new_path.name}")
        except Exception as e:
            if progress_callback:
                progress_callback(idx, total_targets, f"⚠️ 리네임 실패 ({old_path.name}): {e}")

    return completed_count, total_targets
