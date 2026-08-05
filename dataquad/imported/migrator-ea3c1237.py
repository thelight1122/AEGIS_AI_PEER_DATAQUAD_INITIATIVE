import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from pydantic import ValidationError
from core.dataquad.tensors import TensorKind
from core.dataquad.records import PEERRecord, PCTRecord, NCTRecord, SPINERecord
from core.dataquad.ledgers import DataQuadStore
from core.migration.legacy_node_dataquad import normalize_record

class DataQuadMigrator:
    def __init__(self, store: DataQuadStore):
        self.store = store

    async def migrate_peer(self, source_json_path: str, peer_id: str) -> dict[str, Any]:
        """
        Loads, translates, validates, and appends a legacy Node.js/Firebase 
        peer-state.json DataQuad to the new python-first JSONL store.
        """
        source_path = Path(source_json_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_json_path}")

        with open(source_path, "r", encoding="utf-8") as f:
            legacy_data = json.load(f)

        tensors_dict = legacy_data.get("records", {})
        
        counts = {
            "PEER": 0,
            "PCT": 0,
            "NCT": 0,
            "SPINE": 0,
            "skipped": 0
        }

        # Iteratively process records list under each tensor
        for tensor_name, records_list in tensors_dict.items():
            if tensor_name not in ["PEER", "PCT", "NCT", "SPINE"]:
                continue

            t_kind = TensorKind(tensor_name)
            for raw_rec in records_list:
                norm_rec = normalize_record(raw_rec)

                try:
                    # Verify schema compliance
                    if t_kind == TensorKind.PEER:
                        record = PEERRecord.model_validate(norm_rec)
                    elif t_kind == TensorKind.PCT:
                        record = PCTRecord.model_validate(norm_rec)
                    elif t_kind == TensorKind.NCT:
                        record = NCTRecord.model_validate(norm_rec)
                    elif t_kind == TensorKind.SPINE:
                        record = SPINERecord.model_validate(norm_rec)
                    else:
                        continue
                except ValidationError:
                    counts["skipped"] += 1
                    continue

                # Append to store
                await self.store.append_record(peer_id, record)
                counts[tensor_name] += 1

        total_migrated = sum(v for k, v in counts.items() if k != "skipped")

        report = {
            "migration_timestamp": datetime.now(timezone.utc).isoformat(),
            "peer_id": peer_id,
            "source_file": str(source_json_path),
            "total_migrated": total_migrated,
            "tensor_counts": counts,
            "status": "success"
        }

        # Write migration report to peers ledgers
        await self.store.append_ledger(peer_id, "migration_report", report)
        return report
