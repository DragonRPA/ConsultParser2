"""
ollama_client.py
Ollama REST API와 통신하여 텍스트 분석을 요청합니다.
"""
import json
import requests
from typing import Optional


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")

    def list_models(self) -> list[str]:
        """Ollama에 설치된 모델 목록을 반환합니다."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Ollama 서버에 연결할 수 없습니다: {self.base_url}")
        except Exception as e:
            raise RuntimeError(f"모델 목록 조회 실패: {e}")

    def generate(
        self,
        model: str,
        prompt: str,
        content: str,
        timeout: int = 35,
    ) -> str:
        """
        Ollama generate API를 호출하고 LLM 응답 텍스트를 반환합니다.

        Args:
            model: 사용할 Ollama 모델명 (예: 'gemma3:12b')
            prompt: 프롬프트 템플릿 ({{CONTENT}} 치환자 포함)
            content: {{CONTENT}}에 삽입할 실제 텍스트
            timeout: 요청 타임아웃(초) - 기본값 35초로 90초 대기 방지

        Returns:
            LLM이 생성한 텍스트 문자열

        Raises:
            ConnectionError: 서버 연결 불가
            RuntimeError: API 오류
        """
        if "{{CONTENT}}" in prompt:
            full_prompt = prompt.replace("{{CONTENT}}", content)
        else:
            full_prompt = f"{prompt.strip()}\n\n[상담 내용]\n{content}"

        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,   # 분석 목적이므로 낮은 온도
                "num_predict": 768,   # JSON 생성용 적정 토큰 제한 (90초 헛생성 방지)
            },
        }

        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()

        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Ollama 서버에 연결할 수 없습니다: {self.base_url}")
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Ollama 응답 시간 초과 ({timeout}초)")
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"Ollama API 오류: {e}")
        except Exception as e:
            raise RuntimeError(f"예상치 못한 오류: {e}")

    def ping(self) -> bool:
        """Ollama 서버가 응답하는지 확인합니다."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False
