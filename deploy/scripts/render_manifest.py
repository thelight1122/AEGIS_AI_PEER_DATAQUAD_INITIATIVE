#!/usr/bin/env python3
"""Render a deployment manifest with artifact hashes."""
import argparse, datetime, hashlib, json
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument("--bundle", required=True); p.add_argument("--output", required=True)
p.add_argument("--release", required=True); p.add_argument("--commit", required=True)
a = p.parse_args(); root = Path(a.bundle).resolve(); items = {}
for path in sorted(x for x in root.rglob("*") if x.is_file() and x.name != "manifest.template.json"):
    items[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
doc = json.loads((root / "manifest.template.json").read_text(encoding="utf-8"))
doc.update(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
           source_commit=a.commit, release_id=a.release, artifacts_sha256=items)
out = Path(a.output); out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
