"""
core/stt_engine.py
OpenAI Whisper 오디오 STT 음성 인식 및 타임스탬프 대화록 텍스트 생성 엔진
"""
import os
import re
import json
import logging
import tempfile
import threading
from datetime import timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("STTEngine")

# static_ffmpeg & imageio_ffmpeg 바이너리 경로 자동 탐색 및 환경변수 설정
FFMPEG_EXE_PATH = "ffmpeg"
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass

try:
    import imageio_ffmpeg
    FFMPEG_EXE_PATH = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_dir = os.path.dirname(FFMPEG_EXE_PATH)
    if ffmpeg_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = ffmpeg_dir + os.path.pathsep + os.environ.get("PATH", "")
    logger.info(f"FFmpeg binary path: {FFMPEG_EXE_PATH}")
except Exception:
    pass


class STTEngine:
    """
    OpenAI Whisper 전용 오디오 STT 음성 인식 엔진 (스레드 세이프 싱글톤 지원)
    """

    def __init__(self, whisper_model: str = "base", device_setting: str = "auto", use_fp16: bool = False):
        self.whisper_model_name = whisper_model or "base"
        self.device_setting = device_setting or "auto"
        self.use_fp16 = use_fp16
        self.beam_size = 1

        self._whisper_model = None
        self._loaded_model_name = None
        self._loaded_device = None
        self._transcribe_lock = threading.Lock()

    @staticmethod
    def get_gpu_info() -> dict:
        """시스템 GPU 및 CUDA 상태 감지"""
        try:
            import torch
            has_cuda = torch.cuda.is_available()
            if has_cuda:
                name = torch.cuda.get_device_name(0)
                vram_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 1)
                return {"available": True, "name": name, "vram_gb": vram_gb, "count": torch.cuda.device_count()}
        except Exception:
            pass
        return {"available": False, "name": "CPU 전용 모드", "vram_gb": 0, "count": 0}

    @staticmethod
    def format_timestamp(seconds: float) -> str:
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def check_dependencies(self) -> dict:
        status = {"whisper": False, "torch": False}
        try:
            import torch
            status["torch"] = True
        except ImportError:
            pass
        try:
            import whisper
            status["whisper"] = True
        except ImportError:
            pass
        return status

    def load_models_once(self, progress_callback=None):
        """Whisper AI 모델을 메모리에 1회 싱글톤 로드 (스레드 세이프)"""
        import torch

        with self._transcribe_lock:
            if self.device_setting == "cuda" and torch.cuda.is_available():
                target_device = "cuda"
            elif self.device_setting == "cpu":
                target_device = "cpu"
            else:
                target_device = "cuda" if torch.cuda.is_available() else "cpu"

            if self._whisper_model is not None and self._loaded_model_name == self.whisper_model_name and self._loaded_device == target_device:
                return target_device

            import whisper

            if progress_callback:
                progress_callback(10, f"Whisper [{self.whisper_model_name}] 모델 로드 중 ({target_device.upper()})...")

            try:
                self._whisper_model = whisper.load_model(self.whisper_model_name, device=target_device)
            except Exception as e:
                logger.warning(f"GPU 로드 실패 ({e}), CPU 모드로 전환")
                target_device = "cpu"
                self._whisper_model = whisper.load_model(self.whisper_model_name, device="cpu")

            self._loaded_model_name = self.whisper_model_name
            self._loaded_device = target_device
            return target_device

    def process_audio(self, audio_path: str, progress_callback=None) -> str:
        """
        .m4a, .mp3, .wav 등 오디오 파일의 Whisper STT 음성 인식 및 타임스탬프 텍스트 반환
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")

        deps = self.check_dependencies()
        if not deps["whisper"]:
            raise RuntimeError("OpenAI Whisper 패키지가 미설치되어 있습니다. (pip install openai-whisper)")

        target_device = self.load_models_once(progress_callback=progress_callback)
        fp16_active = self.use_fp16 and (target_device == "cuda")

        if progress_callback:
            progress_callback(30, "Whisper 음성 인식 연산 중...")

        # 텐서 연산 멀티스레드 세이프 락 보호
        with self._transcribe_lock:
            try:
                stt_result = self._whisper_model.transcribe(
                    audio_path,
                    language="ko",
                    fp16=fp16_active,
                    beam_size=self.beam_size
                )
            except Exception as e:
                if target_device == "cuda":
                    logger.warning(f"CUDA 연산 예외 ({e}), CPU 모드로 재시도")
                    import whisper
                    self._whisper_model = whisper.load_model(self.whisper_model_name, device="cpu")
                    stt_result = self._whisper_model.transcribe(audio_path, language="ko", fp16=False, beam_size=self.beam_size)
                else:
                    raise e

        segments = stt_result.get("segments", [])

        if progress_callback:
            progress_callback(90, "타임스탬프 대화록 텍스트 생성 중...")

        lines = []
        for seg in segments:
            seg_start = seg["start"]
            text = seg["text"].strip()
            if not text:
                continue

            time_str = self.format_timestamp(seg_start)
            lines.append(f"[{time_str}] {text}")

        if progress_callback:
            progress_callback(100, "STT 변환 완료")

        return "\n".join(lines)
