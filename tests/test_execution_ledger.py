import json

from aegis_pod.execution_ledger import append_record, build_record, sha256_value


def test_append_record_is_jsonl_and_result_hash_is_stable(tmp_path):
    path = tmp_path / "evidence.jsonl"
    append_record(path, build_record(request_id="r1", result_sha256=sha256_value({"x": 1})))
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["record_type"] == "capability_execution_evidence"
    assert record["request_id"] == "r1"
