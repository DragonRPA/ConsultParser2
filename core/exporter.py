"""
core/exporter.py
3단계: 미검출 건(증상0/조치0) 원문 2차 재분석 및 call_type 분류
4단계: 전사 100% JSON 스키마 마이그레이션, merged_consults.json 단일 병합, Supabase RDB 전처리 (supabase_export.json, supabase_seed.sql)
"""
import json
import re
from pathlib import Path
from datetime import datetime


def run_schema_migration(result_json_dir: Path, progress_callback=None) -> tuple[int, int]:
    """
    기존/신규 생성된 모든 JSON 파일에 "call_type" 필드가 포함되도록 100% 스키마 보완 마이그레이션을 집행합니다.
    기본값: "REPAIR"
    Returns: (수정된 파일 수, 전체 파일 수)
    """
    if not result_json_dir.exists():
        return 0, 0

    json_files = list(result_json_dir.glob("*.json"))
    modified_count = 0
    total_len = len(json_files)

    for idx, jf in enumerate(json_files):
        if progress_callback and idx % 50 == 0:
            progress_callback(f"🛠️ [4단계 마이그레이션 진행 중] JSON 스키마 call_type 검사/보완 ({idx+1} / {total_len}건)")

        try:
            content = jf.read_text(encoding="utf-8")
            data = json.loads(content)
            changed = False

            if "call_type" not in data or not data["call_type"]:
                symptoms = data.get("symptoms") or data.get("증상") or []
                actions = data.get("actions") or data.get("조치") or []

                if len(symptoms) == 0 and len(actions) == 0:
                    data["call_type"] = "INQUIRY"  # 미검출 건 초기 판정
                else:
                    data["call_type"] = "REPAIR"
                changed = True

            if changed:
                jf.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                modified_count += 1
        except Exception:
            pass

    return modified_count, total_len


def build_supabase_export(result_json_dir: Path, output_dir: Path, progress_callback=None) -> dict:
    """
     모든 분석 완료 JSON을 읽어:
    1) 단일 병합 JSON (merged_consults.json)
    2) Supabase RDB Table Editor 가져오기용 (supabase_export.json)
    3) Supabase SQL Editor 직접 실행용 (supabase_seed.sql)
    생성
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    json_files = list(result_json_dir.glob("*.json"))

    merged_records = []
    supabase_records = []
    supabase_items = []

    sql_statements = []
    sql_statements.append("-- ========================================================")
    sql_statements.append("-- Supabase ConsultParser2 Bulk Import Seed SQL")
    sql_statements.append(f"-- Generated At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sql_statements.append("-- ========================================================\n")

    sql_statements.append("""
CREATE TABLE IF NOT EXISTS consult_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_name TEXT UNIQUE NOT NULL,
    consult_date TIMESTAMP WITH TIME ZONE,
    site_name TEXT,
    customer_phone TEXT,
    model_name TEXT,
    engine_used TEXT,
    call_type TEXT NOT NULL DEFAULT 'REPAIR',
    symptom_count INT DEFAULT 0,
    action_count INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS consult_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consult_id UUID REFERENCES consult_records(id) ON DELETE CASCADE,
    item_type TEXT CHECK (item_type IN ('SYMPTOM', 'ACTION')),
    content TEXT NOT NULL,
    item_order INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
""")

    total_len = len(json_files)
    for idx, jf in enumerate(json_files):
        if progress_callback and idx % 50 == 0:
            progress_callback(f"📦 [4단계 DB 수출 진행 중] Supabase Seed SQL & JSON 전처리 생성 중 ({idx+1} / {total_len}건)")

        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
            if data.get("processing_status") != "success":
                continue

            file_name = data.get("file_name", jf.stem)
            call_type = data.get("call_type", "REPAIR")
            contact_info = data.get("contact_info", {})
            site_name = contact_info.get("site_name", "")
            model_name = contact_info.get("model", "")
            engine_used = data.get("model_used", "")

            # 전화번호 추출
            phone_match = re.search(r"(01[016789]-?\d{3,4}-?\d{4}|02-?\d{3,4}-?\d{4}|0[3-9]\d-?\d{3,4}-?\d{4})", file_name)
            customer_phone = phone_match.group(1) if phone_match else ""

            symptoms = data.get("symptoms") or data.get("증상") or []
            actions = data.get("actions") or data.get("조치") or []

            merged_records.append(data)

            # Supabase Header Record
            rec_id = f"rec_{idx+1:06d}"
            record_row = {
                "id": rec_id,
                "file_name": file_name,
                "site_name": site_name,
                "customer_phone": customer_phone,
                "model_name": model_name,
                "engine_used": engine_used,
                "call_type": call_type,
                "symptom_count": len(symptoms),
                "action_count": len(actions),
                "analyzed_at": data.get("analyzed_at", "")
            }
            supabase_records.append(record_row)

            # SQL Header Insert
            sql_statements.append(
                f"INSERT INTO consult_records (file_name, site_name, customer_phone, model_name, engine_used, call_type, symptom_count, action_count) "
                f"VALUES ('{_escape_sql(file_name)}', '{_escape_sql(site_name)}', '{_escape_sql(customer_phone)}', '{_escape_sql(model_name)}', '{_escape_sql(engine_used)}', '{call_type}', {len(symptoms)}, {len(actions)}) "
                f"ON CONFLICT (file_name) DO UPDATE SET call_type = EXCLUDED.call_type;"
            )

            # Supabase Items
            for s_idx, sym in enumerate(symptoms):
                item_row = {
                    "record_file_name": file_name,
                    "item_type": "SYMPTOM",
                    "content": str(sym),
                    "item_order": s_idx + 1
                }
                supabase_items.append(item_row)
                sql_statements.append(
                    f"INSERT INTO consult_items (consult_id, item_type, content, item_order) "
                    f"VALUES ((SELECT id FROM consult_records WHERE file_name='{_escape_sql(file_name)}'), 'SYMPTOM', '{_escape_sql(str(sym))}', {s_idx+1});"
                )

            for a_idx, act in enumerate(actions):
                item_row = {
                    "record_file_name": file_name,
                    "item_type": "ACTION",
                    "content": str(act),
                    "item_order": a_idx + 1
                }
                supabase_items.append(item_row)
                sql_statements.append(
                    f"INSERT INTO consult_items (consult_id, item_type, content, item_order) "
                    f"VALUES ((SELECT id FROM consult_records WHERE file_name='{_escape_sql(file_name)}'), 'ACTION', '{_escape_sql(str(act))}', {a_idx+1});"
                )

        except Exception:
            pass

    # 파일 출력 저장
    merged_path = output_dir / "merged_consults.json"
    export_json_path = output_dir / "supabase_export.json"
    seed_sql_path = output_dir / "supabase_seed.sql"

    merged_path.write_text(json.dumps(merged_records, ensure_ascii=False, indent=2), encoding="utf-8")
    export_json_path.write_text(json.dumps({
        "consult_records": supabase_records,
        "consult_items": supabase_items
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    seed_sql_path.write_text("\n".join(sql_statements), encoding="utf-8")

    return {
        "merged_count": len(merged_records),
        "item_count": len(supabase_items),
        "merged_path": str(merged_path),
        "export_json_path": str(export_json_path),
        "seed_sql_path": str(seed_sql_path)
    }


def _escape_sql(text: str) -> str:
    """SQL 싱글 쿼테이션 특수문자 이스케이프"""
    return text.replace("'", "''")
