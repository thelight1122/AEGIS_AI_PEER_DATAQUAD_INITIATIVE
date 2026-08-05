def normalize_record(raw: dict) -> dict:
    """
    Normalizes legacy camelCase keys from Node/Firebase DataQuad schema
    to snake_case keys used by our Python Pydantic models.
    """
    normalized = {}
    for k, v in raw.items():
        if k == "sessionId":
            normalized["session_id"] = v
        elif k == "presentState":
            normalized["present_state"] = v
        elif k == "workingContext":
            normalized["working_context"] = v
        elif k == "retrievedRecordIds":
            normalized["retrieved_record_ids"] = v
        elif k == "rlsSessionId":
            normalized["rls_session_id"] = v
        elif k == "pressureState":
            normalized["pressure_state"] = v
        elif k == "distilledSummary":
            normalized["distilled_summary"] = v
        elif k == "essenceMemory":
            normalized["essence_memory"] = v
        elif k == "sourceRecordIds":
            normalized["source_record_ids"] = v
        elif k == "natureAspectRefs":
            normalized["nature_aspect_refs"] = v
        elif k == "clock" and isinstance(v, dict):
            clock_norm = {}
            for ck, cv in v.items():
                if ck == "advancedAt":
                    clock_norm["last_advanced_at"] = cv
                elif ck == "lastAdvancedAt":
                    clock_norm["last_advanced_at"] = cv
                elif ck == "startedAt":
                    clock_norm["started_at"] = cv
                else:
                    clock_norm[ck] = cv
            
            # Ensure started_at and last_advanced_at exist
            if "started_at" not in clock_norm:
                clock_norm["started_at"] = clock_norm.get("last_advanced_at", raw.get("timestamp", ""))
            if "last_advanced_at" not in clock_norm:
                clock_norm["last_advanced_at"] = clock_norm.get("started_at", raw.get("timestamp", ""))
            normalized["clock"] = clock_norm
        elif k == "provenance" and isinstance(v, dict):
            prov_norm = {}
            for pk, pv in v.items():
                if pk == "assignmentSource":
                    prov_norm["assignment_source"] = pv
                elif pk == "inheritedFrom":
                    prov_norm["inherited_from"] = pv
                elif pk == "recognitionStatus":
                    prov_norm["recognition_status"] = pv
                elif pk == "declaredBy":
                    prov_norm["declared_by"] = pv
                else:
                    prov_norm[pk] = pv
            normalized["provenance"] = prov_norm
        else:
            normalized[k] = v
    return normalized
