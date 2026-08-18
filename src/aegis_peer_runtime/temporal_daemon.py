"""Temporal daemon — time-aware data retrieval operator.

The Temporal daemon watches the temporal ledger and provides time-based
data about observations: when each turn happened, how much time elapsed
between turns, and time-range queries. It reveals temporal data on demand.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from .daemon import BaseDaemon


class TemporalDaemonProcess(BaseDaemon):
    """Long-running operator for temporal observation data."""

    def __init__(
        self,
        socket_path: str | Path,
        state_root: str | Path,
    ) -> None:
        super().__init__("Temporal", socket_path)
        self._state_root = Path(state_root)
        self._observations: list[dict[str, Any]] = []
        self._by_t_time: dict[int, dict[str, Any]] = {}

        self.add_watcher(
            "temporal",
            self._state_root / "derived" / "temporal.jsonl",
        )

    def on_new_records(self, watcher_name: str, records: list[dict[str, Any]]) -> None:
        if watcher_name != "temporal":
            return
        for record in records:
            t_time = record.get("t_time")
            if t_time is not None and t_time not in self._by_t_time:
                self._observations.append(record)
                self._by_t_time[t_time] = record

    def op_get_observation(self, params: dict[str, Any]) -> dict[str, Any] | None:
        """Get a single temporal observation by T-Time."""
        t_time = params.get("t_time")
        if t_time is None:
            raise ValueError("t_time is required")
        return self._by_t_time.get(t_time)

    def op_get_range(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Get temporal observations within a T-Time range."""
        start = params.get("start", 1)
        end = params.get("end", 999999)
        return [
            obs for obs in self._observations
            if start <= obs.get("t_time", 0) <= end
        ]

    def op_get_all(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Get all temporal observations."""
        return list(self._observations)

    def op_get_latest(self, params: dict[str, Any]) -> dict[str, Any] | None:
        """Get the most recent temporal observation."""
        if not self._observations:
            return None
        return self._observations[-1]

    def op_get_elapsed(self, params: dict[str, Any]) -> dict[str, Any]:
        """Get total elapsed time and per-observation breakdown."""
        total_elapsed = sum(obs.get("elapsed_seconds", 0) for obs in self._observations)
        return {
            "total_observations": len(self._observations),
            "total_elapsed_seconds": total_elapsed,
            "first_observed": self._observations[0].get("observed_at") if self._observations else None,
            "last_observed": self._observations[-1].get("observed_at") if self._observations else None,
        }

    def op_time_context(self, params: dict[str, Any]) -> dict[str, Any]:
        """Get time context for a set of T-Times.

        Given a list of t_times, returns their temporal observations
        so the Processor can incorporate time data into relation mapping.
        """
        t_times = params.get("t_times", [])
        results: list[dict[str, Any]] = []
        for t in t_times:
            obs = self._by_t_time.get(t)
            if obs is not None:
                results.append(obs)
        return {
            "requested": len(t_times),
            "found": len(results),
            "observations": results,
        }

    def op_count(self, params: dict[str, Any]) -> dict[str, Any]:
        """Count temporal observations."""
        return {"total": len(self._observations)}

    def op_health(self, params: dict[str, Any]) -> dict[str, Any]:
        return {
            "daemon": self.name,
            "status": "ok",
            "running": self._running,
            "observations": len(self._observations),
            "latest_t_time": self._observations[-1].get("t_time") if self._observations else None,
        }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Temporal daemon — time-aware retrieval operator")
    parser.add_argument("--socket", type=Path, default=Path("/var/lib/aegis-verus-lab/daemons/temporal.sock"))
    parser.add_argument("--state-root", type=Path, default=Path("/var/lib/aegis-verus-lab"))
    args = parser.parse_args()

    daemon = TemporalDaemonProcess(args.socket, args.state_root)
    daemon.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
