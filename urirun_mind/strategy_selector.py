# Author: Tom Sapletta · Part of the ifURI solution.
"""Strategy selector — known-good replay BEFORE the LLM, gated by autonomy + antipatterns.

Order (cheap → expensive):
  1. retrieve a known-good SKILL for this intent; if env fingerprint matches, replay it
  2. filter out routes an ANTIPATTERN says to avoid for this intent/node status
  3. otherwise fall through to a fresh plan (the reasoner / LLM)
Every chosen plan is gated by the AUTONOMY policy before it is called runnable. This cuts
cost and flakiness and stops the system re-walking failed paths.
"""
from __future__ import annotations

from typing import Any

from . import antipatterns, autonomy_policy, episode_store, skill_cards


def select(intent: str, *, prompt: str = "", environment: dict | None = None,
           level: int = 3) -> dict[str, Any]:
    """Pick how to satisfy an intent. Returns the source (skill|episode|fresh), the flow,
    the autonomy gate verdict, and any antipattern warnings — WITHOUT calling an LLM."""
    env = environment or {}
    fp = episode_store.env_fingerprint(env)
    node_status = env.get("node_status")
    anti = antipatterns.match(intent, node_status)

    # 1. known-good skill for this intent (prefer env match)
    cards = skill_cards.search(prompt or intent)
    for card in cards:
        if card.get("risk", {}).get("deprecated"):
            continue
        flow = [{"uri": u} if isinstance(u, str) else u for u in card["preferred_flow"]]
        flow, warns = _drop_avoided(flow, anti)
        if flow:
            gate = autonomy_policy.gate_plan(flow, level=level)
            return _result("skill", card["id"], flow, gate, anti, warns,
                           note="known-good skill; adapt with LLM only if env differs")

    # 2. a successful past episode with the same fingerprint → replay its flow
    for ep in episode_store.similar(intent, fp, result="ok"):
        if ep.get("flow"):
            flow = [{"uri": u} if isinstance(u, str) else u for u in ep["flow"]]
            flow, warns = _drop_avoided(flow, anti)
            if flow:
                gate = autonomy_policy.gate_plan(flow, level=level)
                return _result("episode", ep["id"], flow, gate, anti, warns,
                               note="replaying a known-good episode (same env fingerprint)")

    # 3. no memory → the caller should plan fresh (reasoner/LLM), still under the gate
    return {"source": "fresh", "intent": intent, "fingerprint": fp, "flow": [],
            "antipatterns": [a["id"] for a in anti], "avoid_routes": _avoid_routes(anti),
            "note": "no known-good path; plan fresh (reasoner/LLM) then gate + record the episode",
            "autonomy_level": level}


def _drop_avoided(flow: list[dict], anti: list[dict]) -> tuple[list[dict], list[str]]:
    kept, warns = [], []
    for step in flow:
        rid = antipatterns.is_avoided(step.get("uri", ""), anti)
        if rid:
            warns.append(f"{step.get('uri')} avoided by antipattern {rid}")
        else:
            kept.append(step)
    return kept, warns


def _avoid_routes(anti: list[dict]) -> list[str]:
    return [g for r in anti for g in r.get("avoid", [])]


def _result(source, ref, flow, gate, anti, warns, note) -> dict:
    return {"source": source, "ref": ref, "flow": flow, "gate": gate,
            "antipatterns": [a["id"] for a in anti], "warnings": warns,
            "runnable": gate["runnable"], "note": note}
