import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
DEPLOY = ROOT / "deploy"
PEERS = ("lumin", "claude", "gemini", "grok")

def test_required_artifacts_exist():
    for rel in ("bin/aegis-ai-peer-unseated", "systemd/aegis-ai-peer@.service",
                "scripts/install.sh", "scripts/health.sh", "scripts/upgrade.sh",
                "scripts/rollback.sh", "scripts/render_manifest.py",
                "manifest.template.json"):
        assert (DEPLOY / rel).is_file(), rel

def test_four_unique_loopback_envs_are_unseated():
    ports = set()
    for peer in PEERS:
        text = (DEPLOY / "env" / f"{peer}.env").read_text()
        assert "AEGIS_BIND=127.0.0.1" in text
        assert "AEGIS_MODE=UNSEATED" in text
        assert "AEGIS_PROMOTION=DISABLED" in text
        assert "AEGIS_LIVE_CREDENTIALS=FORBIDDEN" in text
        assert not any(term in text.upper() for term in ("TOKEN=", "KEY=", "TUMBLER="))
        ports.add(next(x.split("=", 1)[1] for x in text.splitlines()
                       if x.startswith("AEGIS_PORT=")))
    assert len(ports) == 4

def test_service_is_hardened_and_resource_bounded():
    text = (DEPLOY / "systemd" / "aegis-ai-peer@.service").read_text()
    for item in ("NoNewPrivileges=yes", "ProtectSystem=strict",
                 "MemoryMax=256M", "CPUQuota=25%", "TasksMax=64",
                 "ReadWritePaths=/var/lib/aegis-ai-peers/%i",
                 "User=aegis-ai-peer-%i", "Group=aegis-ai-peer-%i"):
        assert item in text

def test_unseated_runtime_fails_closed_if_promotion_policy_is_absent():
    text = (DEPLOY / "bin" / "aegis-ai-peer-unseated").read_text()
    assert 'os.environ.get("AEGIS_PROMOTION") != "DISABLED"' in text
    assert 'os.environ.get("AEGIS_LIVE_CREDENTIALS") != "FORBIDDEN"' in text
    assert '"claim": "record_preservation_only"' in text
    assert '"continuity_claimed": False' in text
    assert '"self_claimed": False' in text

def test_installer_creates_distinct_peer_identities():
    text = (DEPLOY / "scripts" / "install.sh").read_text()
    assert 'identity="aegis-ai-peer-$peer"' in text
    assert 'install -d -o "$identity" -g "$identity" -m 0700' in text
    assert '[[ "$RELEASE_ID" =~ ^[A-Za-z0-9]' in text

def test_upgrade_failure_rolls_back_and_rollback_verifies_health():
    upgrade = (DEPLOY / "scripts" / "upgrade.sh").read_text()
    rollback = (DEPLOY / "scripts" / "rollback.sh").read_text()
    assert "trap rollback_on_error ERR" in upgrade
    assert '"$BUNDLE_ROOT/scripts/rollback.sh"' in upgrade
    assert 'health.sh"' in rollback
    assert 'mode"]=="UNSEATED"' in (DEPLOY / "scripts" / "health.sh").read_text()

def test_manifest_is_unseated_and_has_all_state_roots():
    doc = json.loads((DEPLOY / "manifest.template.json").read_text())
    assert doc["mode"] == "UNSEATED" and doc["live_source"] is False
    assert doc["claim"] == "record_preservation_only"
    assert doc["continuity_claimed"] is False and doc["self_claimed"] is False
    assert doc["promotion"] == "DISABLED" and doc["live_credentials"] == "FORBIDDEN"
    assert set(doc["state_roots"]) == set(PEERS)
    for peer in PEERS:
        assert doc["state_roots"][peer] == f"/var/lib/aegis-ai-peers/{peer}"

def test_scripts_contain_no_disk_or_state_deletion_operations():
    forbidden = ("az disk", "detach", "mkfs", "fdisk", "wipefs",
                 "rm -rf /var/lib/aegis-ai-peers")
    text = "\n".join(p.read_text().lower() for p in
                     (DEPLOY / "scripts").iterdir() if p.is_file())
    for term in forbidden:
        assert term not in text

def test_runbook_names_protected_artifacts_and_limits_rollback_to_unseated_release():
    runbook = (ROOT / "docs" / "runbooks" / "AI-PEER-VM-DEPLOYMENT.md").read_text()
    for artifact in (
        "vm-cyberpeer-core-os-repair-copy",
        "vm-cyberpeer-core_OsDisk_1_f79b5c49e4f94a9792b038ccb685615b",
        "vm-cyberpeer-core-os-snap-20260802",
    ):
        assert artifact in runbook
    assert "Rollback target must itself be an UNSEATED release" in runbook
    assert "does not change peer state or any VM disk" in runbook
