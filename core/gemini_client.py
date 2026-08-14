"""
gemini_client.py
Google Gemini REST API 클라이언트 (최신 모델 핑 테스트 및 하이브리드 수용)
"""
import json
import time
import requests
from typing import Optional, Callable


class GeminiClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    def _get_clean_key(self) -> str:
        if not self.api_key:
            return ""
        return self.api_key.replace("\n", "").replace("\r", "").replace("\t", "").replace(" ", "").strip()

    def test_connection(self, model: str = "gemini-3.1-flash-lite") -> tuple[bool, str]:
        """API 키 유효성을 선택된 모델 및 최신 모델 순서로 유연하게 테스트합니다."""
        clean_key = self._get_clean_key()
        if not clean_key:
            return False, "❌ API 키가 입력되지 않았습니다."

        clean_selected = model.replace("models/", "").split(" ")[0].strip()
        test_models = [clean_selected, "gemini-3.1-flash-lite", "gemini-flash-latest", "gemini-1.5-flash"]

        # 중복 제거
        seen = set()
        unique_test_models = []
        for m in test_models:
            if m and m not in seen:
                seen.add(m)
                unique_test_models.append(m)

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": clean_key,
        }
        payload = {
            "contents": [{"parts": [{"text": "ping"}]}],
            "generationConfig": {"maxOutputTokens": 5}
        }

        last_err = ""
        for m in unique_test_models:
            url = f"{self.base_url}/{m}:generateContent"
            try:
                resp = requests.post(url, json=payload, headers=headers, timeout=10)
                if resp.status_code == 200:
                    return True, f"✅ Gemini API 연결 성공! ({m})"
                elif resp.status_code == 429:
                    return True, f"✅ Gemini API 연결 성공! ({m} - 분당 한도 도달)"
                else:
                    try:
                        err_data = resp.json()
                        last_err = err_data.get("error", {}).get("message", resp.text)
                    except Exception:
                        last_err = resp.text
            except Exception as e:
                last_err = str(e)

        return False, f"❌ 연결 실패: {last_err}"

    def list_models(self) -> list[str]:
        """
        Google Generative Language REST API를 호출하여
        현재 실시간으로 서비스 제공 중인 Gemini 모델 목록(generateContent 지원 모델)을 반환합니다.
        """
        clean_key = self._get_clean_key()
        if not clean_key:
            return []

        url = f"https://generativelanguage.googleapis.com/v1beta/models"
        headers = {"x-goog-api-key": clean_key}

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                raw_models = data.get("models", [])
                gemini_list = []
                for m in raw_models:
                    methods = m.get("supportedGenerationMethods", [])
                    name = m.get("name", "").replace("models/", "").strip()
                    # generateContent 지원 및 gemini- 로 시작하는 실시간 텍스트/분석 지원 모델 추출
                    if "generateContent" in methods and name.startswith("gemini-"):
                        # 구형 레거시 모델이나 단순 엠베딩(embedding) 모델 제외
                        if not any(sub in name for sub in ["embedding", "bison", "gecko", "imagen"]):
                            gemini_list.append(name)

                # 최신 버전 우선 순 정렬 (3.7 > 3.5 > 3.1 > 2.5 > 2.0 > 1.5 등)
                gemini_list.sort(reverse=True)
                return gemini_list
        except Exception:
            pass
        return []

    def ping(self) -> bool:
        ok, _ = self.test_connection()
        return ok

    def generate(
        self,
        model: str = "gemini-3.1-flash-lite",
        prompt: str = "",
        content: str = "",
        timeout: int = 40,
        max_retries: int = 3,
        status_callback: Optional[Callable[[str, str], None]] = None,
        stop_checker: Optional[Callable[[], bool]] = None,
    ) -> str:
        """
        Gemini API를 호출하고 LLM 응답 텍스트를 반환합니다.
        """
        clean_key = self._get_clean_key()
        if not clean_key:
            raise ValueError("Gemini API 키가 설정되지 않았습니다. [설정] 탭에서 입력해주세요.")

        if "{{CONTENT}}" in prompt:
            full_prompt = prompt.replace("{{CONTENT}}", content)
        else:
            full_prompt = f"{prompt.strip()}\n\n[상담 내용]\n{content}"

        clean_model = model.replace("models/", "").split(" ")[0].strip()
        if not clean_model:
            clean_model = "gemini-3.5-flash-lite"
        url = f"{self.base_url}/{clean_model}:generateContent"

        payload = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": clean_key,
        }

        last_exception = None

        for attempt in range(1, max_retries + 1):
            if stop_checker and stop_checker():
                raise InterruptedError("사용자 중지 요청으로 생성이 취소되었습니다.")

            try:
                if status_callback:
                    if attempt == 1:
                        status_callback(f"📡 Gemini API 요청 전송 중 ({clean_model})...", "#3B82F6")
                    else:
                        status_callback(f"📡 Gemini API 재요청 중... ({attempt}/{max_retries})", "#3B82F6")

                resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
                
                if resp.status_code == 429:
                    last_exception = RuntimeError("구글 1분당 무료 한도 도달 (429 Too Many Requests)")
                    if status_callback:
                        status_callback("⏳ 구글 분당 한도 대기 중 (3초 후 재시도)...", "#F59E0B")
                    
                    for _ in range(6):
                        if stop_checker and stop_checker():
                            raise InterruptedError("사용자 중지 요청으로 생성이 취소되었습니다.")
                        time.sleep(0.5)
                    continue

                if resp.status_code in (500, 502, 503, 504):
                    last_exception = RuntimeError(f"구글 서버 일시적 응답 오류 ({resp.status_code})")
                    if status_callback:
                        status_callback(f"⚠️ 구글 서버 일시 대기 중 (2초 후 재시도)...", "#F59E0B")
                    time.sleep(2)
                    continue

                if resp.status_code != 200:
                    try:
                        err_json = resp.json()
                        err_msg = err_json.get("error", {}).get("message", resp.text)
                    except Exception:
                        err_msg = resp.text
                    raise RuntimeError(f"Gemini API 오류 ({resp.status_code}): {err_msg}")

                data = resp.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    raise RuntimeError("Gemini API 응답에 생성 결과가 없습니다.")

                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    raise RuntimeError("Gemini API 응답 텍스트가 비어 있습니다.")

                if status_callback:
                    status_callback("✅ Gemini 응답 수신 완료", "#10B981")

                return parts[0].get("text", "").strip()

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_exception = e
                if status_callback:
                    status_callback("⚠️ 네트워크 지연 (재시도 중...)", "#EF4444")
                if attempt < max_retries:
                    time.sleep(2)
                else:
                    raise TimeoutError(f"Gemini API {max_retries}회 재시도 실패: {e}")
            except InterruptedError as e:
                raise e
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    time.sleep(1)
                else:
                    raise e

        raise RuntimeError(f"Gemini API 호출 중단: {last_exception}")
