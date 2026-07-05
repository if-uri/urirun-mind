# Author: Tom Sapletta · Part of the ifURI solution.
"""Antipatterns — learning from counter-examples, not just successes.

"For office tasks on a stale/blocked node, do NOT reach for the GUI editor; prefer
headless." An antipattern has a trigger (intent + node status) and lists routes to AVOID
and routes to PREFER. The strategy selector consults these so the system does not walk
into the same failed path three times.
"""
from __future__ import annotations

import fnmatch
import json
import os
from pathlib import Path
from typing import Any


def _path() -> Path:
    d = Path(os.environ.get("URIRUN_MIND_DIR") or "~/.urirun/mind").expanduser()
    d.mkdir(parents=True, exist_ok=True)
    return d / "antipatterns.json"


def _load() -> dict[str, dict]:
    p = _path()
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def add(rule: dict) -> dict[str, Any]:
    """Add/replace an antipattern. Needs id + trigger; avoid/prefer are route globs."""
    rid = rule.get("id")
    if not rid or not rule.get("trigger"):
        raise ValueError("antipattern needs 'id' and 'trigger'")
    rules = _load()
    rules[rid] = {"id": rid, "trigger": rule["trigger"],
                  "avoid": rule.get("avoid") or [], "prefer": rule.get("prefer") or []}
    _path().write_text(json.dumps(rules, indent=1), encoding="utf-8")
    return rules[rid]


def match(intent: str, node_status: str | None = None) -> list[dict]:
    """Antipatterns whose trigger matches this intent (+ optional node status)."""
    out = []
    for r in _load().values():
        t = r.get("trigger") or {}
        if t.get("intent") and t["intent"] != intent:
            continue
        if t.get("node_status") and node_status and t["node_status"] != node_status:
            continue
        out.append(r)
    return out


def is_avoided(uri: str, matched: list[dict]) -> str | None:
    """If ``uri`` matches an AVOID glob of any matched antipattern, return that rule id."""
    path = uri.split("://", 1)[-1]
    for r in matched:
        for glob in r.get("avoid", []):
            g = glob.split("://", 1)[-1]
            if fnmatch.fnmatch(uri, glob) or fnmatch.fnmatch(path, g):
                return r["id"]
    return None
