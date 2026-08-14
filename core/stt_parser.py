"""
core/stt_parser.py
STT 통화 녹음 / 카카오톡 대화 파일명 정교 파싱 및 연락처 100% 완벽 보호 모듈
목표 포맷: YYYYMMDD_HHMMSS_고객명(또는 연락처)_모델명.txt
"""
import re
import os


class STTFilenameParser:
    """
    통화 녹음 파일명 파싱 클래스
    - 전화번호(01012345678, 010-1234-5678, 02-123-4567 등) 100% 완전 보존 가드 적용
    - 일자시간(YYYYMMDD_HHMMSS), 고객명/상호/연락처, 모델명 정밀 분리
    """

    # 1. 한국 전화번호 정규식 (010, 011, 016~019 및 02, 031~064 등 지역번호)
    PHONE_REGEX = re.compile(
        r'(?:01[016789]|02|0[3-9]\d)[-.\s]?\d{3,4}[-.\s]?\d{4}'
    )

    # 2. 계약일자/날짜 접미사 패턴 (예: 20_06_26, 21_03_22, 23.07.18, 22_01_24 등 - 독립적 날짜)
    CONTRACT_DATE_REGEX = re.compile(
        r'\b\d{2}[._\-]\d{2}[._\-]\d{2}\b'
    )

    # 3. 제거 대상 노이즈 단어 패턴
    NOISE_PATTERNS = [
        r'\b사용자\b', r'\b사무실\b', r'\b반장\b', r'\b대화\s*내용\b',
        r'\b구독(?:_\d+개월)?\b', r'\b\d+개월\b', r'\b\d+대\b'
    ]

    @classmethod
    def parse(cls, filename: str) -> dict:
        """
        파일명에서 (dt_str: YYYYMMDD_HHMMSS, customer_name, model_name)을 정밀 추출합니다.
        전화번호가 포함된 경우 날짜 추출이나 정제 시 단 1자리도 잘리지 않도록 완전히 격리 보호합니다.
        """
        base_name, orig_ext = os.path.splitext(filename)
        target_ext = '.txt'

        # --- 0. 전화번호(연락처) 최우선 격리 및 안전 토큰화 ---
        phone_tokens = []

        def _protect_phone(match):
            token = f"___PHONETOKEN_{len(phone_tokens)}___"
            raw_phone = match.group(0).strip()
            phone_tokens.append(raw_phone)
            return token

        # 가장 먼저 전화번호 텍스트를 락 토큰으로 안전 치환
        protected_text = cls.PHONE_REGEX.sub(_protect_phone, base_name)

        dt_str = None
        header_text = protected_text

        # --- 1. 날짜 / 시간 추출 ---
        # 패턴 A: 카카오톡 대화 내용 내보내기
        kakaotalk_match = re.search(
            r'(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.\s*\([^)]+\)\s*(오전|오후)\s*(\d{1,2})_(\d{1,2})(?:_(\d{1,2}))?',
            protected_text
        )

        if kakaotalk_match:
            year, month, day, ampm, hour, minute, second = kakaotalk_match.groups()
            year, month, day, hour, minute = map(int, [year, month, day, hour, minute])
            second = int(second) if second else 0

            if ampm == '오후' and hour < 12:
                hour += 12
            elif ampm == '오전' and hour == 12:
                hour = 0

            dt_str = f"{year:04d}{month:02d}{day:02d}_{hour:02d}{minute:02d}{second:02d}"

            comma_idx = protected_text.find(',')
            if comma_idx != -1:
                header_text = protected_text[:comma_idx]
            else:
                header_text = protected_text
        else:
            # 패턴 B: 통화 녹음 파일명 (예: 230525_143818 또는 230525_260722_143818)
            rec_match = re.search(
                r'(?:(\d{6})_)?(\d{6})_(\d{6})',
                protected_text
            )
            if rec_match:
                d1, d2, t1 = rec_match.groups()
                date_part = d2 if d2 else d1
                time_part = t1

                if date_part and time_part:
                    yy, mm, dd = int(date_part[:2]), int(date_part[2:4]), int(date_part[4:6])
                    yyyy = 2000 + yy if yy < 80 else 1900 + yy
                    hh, mi, ss = int(time_part[:2]), int(time_part[2:4]), int(time_part[4:6])

                    dt_str = f"{yyyy:04d}{mm:02d}{dd:02d}_{hh:02d}{mi:02d}{ss:02d}"
                    header_text = protected_text[:rec_match.start()]

        if not dt_str:
            dt_str = "00000000_000000"

        # --- 2. 고객명 및 모델명 분리 ---
        clean_header = re.sub(r'^통화\s*녹음\s*', '', header_text, flags=re.IGNORECASE).strip()
        clean_header = cls.CONTRACT_DATE_REGEX.sub('', clean_header).strip()

        # 정규표현식으로 모델 패턴 검색 (예: S12, S3, S7PST, J900-12호)
        model_match = re.search(
            r'\b([A-Za-z][A-Za-z0-9_\-]*(?:호)?(?:\([^)]*\))?)\b',
            clean_header
        )

        model_name = ""
        if model_match:
            candidate = model_match.group(1).strip()
            # 전화번호 토큰이 모델명으로 잘못 잡히지 않도록 차단
            if any(c.isalpha() for c in candidate) and not candidate.startswith("___PHONETOKEN"):
                model_name = candidate
                clean_header = clean_header.replace(candidate, '').strip()

        # 노이즈 패턴 제거
        for p in cls.NOISE_PATTERNS:
            clean_header = re.sub(p, '', clean_header, flags=re.IGNORECASE).strip()

        # 괄호 안 중고 단독 표기 제거
        clean_header = re.sub(r'\(\s*중고\s*\)', '', clean_header).strip()

        # --- 3. 전화번호 토큰 완전 복원 ---
        for idx, phone_val in enumerate(phone_tokens):
            clean_header = clean_header.replace(f"___PHONETOKEN_{idx}___", phone_val)

        # 남아있는 텍스트를 고객명/연락처로 정제
        customer_name = re.sub(r'\s+', ' ', clean_header).strip()

        # 파일명 금지 특수문자 정제 (하이픈 -, 언더바 _ 는 보존)
        customer_name = re.sub(r'[\\/:*?"<>|]', '', customer_name).strip()
        model_name = re.sub(r'[\\/:*?"<>|]', '', model_name).strip()

        # 언더스코어 연속 발생 정리
        customer_name = re.sub(r'_+', '_', customer_name).strip('_')

        if not customer_name:
            customer_name = "미지정고객"

        # 모델명 띄어쓰기 완전 제거
        model_name = model_name.replace(" ", "")

        if model_name:
            new_filename = f"{dt_str}_{customer_name}_{model_name}{target_ext}"
        else:
            new_filename = f"{dt_str}_{customer_name}{target_ext}"

        # 연속 언더바 치환 정제
        new_filename = re.sub(r'_+', '_', new_filename)

        return {
            "original": filename,
            "dt_str": dt_str,
            "customer_name": customer_name,
            "model_name": model_name,
            "new_filename": new_filename
        }
