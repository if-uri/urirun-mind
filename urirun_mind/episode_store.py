# Author: Tom Sapletta · Part of the ifURI solution.
"""Episode memory — the basis of learning. Every task records a full episode.

    intent → context → strategy → URI flow → trace → artifacts → postconditions → result → lesson

Learning here is NOT weight training — it is building a library of proven paths and
antipatterns, keyed by an ENVIRONMENT FINGERPRINT so a lesson only applies where the
environment matches. The lesson is a PROCEDURE ("for office tasks on a stale/blocked node,
go headless first"), never a fact ("LibreOffice missing on lenovo").
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any


def _dir() -> Path:
    d = Path(os.environ.get("URIRUN_MIND_DIR") or "~/.urirun/mind").expanduser()
    d.mkdir(parents=True, exist_ok=True)
    return d


def _path() -> Path:
    return _dir() / "episodes.jsonl"


def env_fingerprint(env: dict) -> str:
    """A stable signature of the RELEVANT environment — os/session/node + connector state —
    so a known-good path is only reused when the environment actually matches."""
    keys = ("node", "os", "session", "display", "runtime", "node_status")
    base = {k: env.get(k) for k in keys if env.get(k) is not None}
    conns = env.get("connectors") or {}
    base["connectors"] = {k: conns[k] for k in sorted(conns)} if isinstance(conns, dict) else conns
    blob = json.dumps(base, sort_keys=True, default=str)
    return env.get("node", "host") + ":" + hashlib.sha256(blob.encode()).hexdigest()[:12]


def record(episode: dict, *, clock: float | None = None) -> dict[str, Any]:
    """Append one episode. Stamps id + fingerprint; returns the stored record."""
    ts = clock if clock is not None else time.time()
    rec = {
        "id": "ep-" + hashlib.sha256(f"{episode.get('intent')}{ts}".encode()).hexdigest()[:10],
        "ts": ts,
        "intent": episode.get("intent"),
        "prompt": episode.get("prompt"),
        "node": (episode.get("environment") or {}).get("node") or episode.get("node"),
        "fingerprint": env_fingerprint(episode.get("environment") or {}),
        "strategy": episode.get("strategy"),
        "flow": episode.get("flow") or [],
        "artifacts": episode.get("artifacts") or [],
        "result": episode.get("result"),                 # ok | failed | degraded | blocked
        "failure_class": episode.get("failure_class"),
        "working_fallback": episode.get("working_fallback"),
        "lesson": episode.get("lesson"),
        "promote_to_skill": bool(episode.get("promote_to_skill")),
    }
    with _path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, default=str) + "\n")
    return rec


def all_episodes(limit: int = 500) -> list[dict]:
    p = _path()
    if not p.is_file():
        return []
    rows = p.read_text(encoding="utf-8").strip().splitlines()[-limit:]
    return [json.loads(r) for r in rows if r]


def similar(intent: str, fingerprint: str | None = None, *, result: str | None = None) -> list[dict]:
    """Episodes for the same intent, best-first: exact-fingerprint matches (same env) rank
    above others. This is the known-good retrieval a strategy selector consults before an LLM."""
    eps = [e for e in all_episodes() if e.get("intent") == intent]
    if result:
        eps = [e for e in eps if e.get("result") == result]
    eps.sort(key=lambda e: (e.get("fingerprint") == fingerprint, e.get("ts") or 0), reverse=True)
    return eps
