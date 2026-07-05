# Author: Tom Sapletta · Part of the ifURI solution.
"""Skill cards — a learned PROCEDURE promoted from successful episodes, as a reusable resource.

A skill card captures "how to do X here": intent patterns, a preferred URI flow, ranked
fallbacks, postconditions, risk, and success stats. Before planning from scratch, the
system searches skills — "I have a known-good path for this; try it, use the LLM only to
adapt." Cards store PROCEDURES (transferable), never one-off answers.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


def _path() -> Path:
    d = Path(os.environ.get("URIRUN_MIND_DIR") or "~/.urirun/mind").expanduser()
    d.mkdir(parents=True, exist_ok=True)
    return d / "skills.json"


def _load() -> dict[str, dict]:
    p = _path()
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _save(cards: dict) -> None:
    _path().write_text(json.dumps(cards, indent=1, default=str), encoding="utf-8")


def create(card: dict) -> dict[str, Any]:
    """Create/replace a skill card. Requires id + preferred_flow."""
    cid = card.get("id")
    if not cid or not card.get("preferred_flow"):
        raise ValueError("skill card needs 'id' and 'preferred_flow'")
    cards = _load()
    existing = cards.get(cid, {})
    cards[cid] = {
        "id": cid,
        "intent_patterns": card.get("intent_patterns") or existing.get("intent_patterns") or [],
        "preconditions": card.get("preconditions") or [],
        "preferred_flow": card["preferred_flow"],
        "fallbacks": card.get("fallbacks") or [],
        "postconditions": card.get("postconditions") or [],
        "risk": card.get("risk") or {"level": "low", "requires_human_approval": False},
        "stats": existing.get("stats") or {"success_count": 0, "failure_count": 0, "last_success": None},
    }
    _save(cards)
    return cards[cid]


def search(intent_or_prompt: str) -> list[dict]:
    """Cards whose id or intent patterns match the intent/prompt, best (most successful) first."""
    q = (intent_or_prompt or "").lower()
    hits = []
    for card in _load().values():
        if card["id"] in q or q in card["id"] or \
           any(p.lower() in q or q in p.lower() for p in card.get("intent_patterns", [])):
            hits.append(card)
    hits.sort(key=lambda c: c["stats"]["success_count"] - c["stats"]["failure_count"], reverse=True)
    return hits


def show(card_id: str) -> dict | None:
    return _load().get(card_id)


def record_outcome(card_id: str, ok: bool, *, clock: float | None = None) -> dict | None:
    """Update a card's success/failure stats after a run (feeds ranking + trust)."""
    cards = _load()
    card = cards.get(card_id)
    if not card:
        return None
    key = "success_count" if ok else "failure_count"
    card["stats"][key] = card["stats"].get(key, 0) + 1
    if ok:
        card["stats"]["last_success"] = clock if clock is not None else time.time()
    _save(cards)
    return card


def deprecate(card_id: str) -> bool:
    cards = _load()
    if card_id in cards:
        cards[card_id]["risk"] = {**cards[card_id].get("risk", {}), "deprecated": True}
        _save(cards)
        return True
    return False
