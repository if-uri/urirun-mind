# Author: Tom Sapletta · Part of the ifURI solution.
"""Reflection — after every run, evaluate honestly and turn lessons into action.

Did the goal REALLY hold (postconditions), or was it a silent failure? What worked, what
failed, is there a better strategy next time? Reflection records the episode, promotes a
working fallback to a skill card, records the failed path as an antipattern, and emits
ticket candidates (missing connector, repeated blocker) for koru — closing the loop:

    run → reflect → learn → ticket → koru → connector/code → smoke → publish → use
"""
from __future__ import annotations

from typing import Any

from . import antipatterns, episode_store, skill_cards


def evaluate(run: dict) -> dict[str, Any]:
    """Assess a run record. ``run`` = {intent, prompt, environment, strategy, flow,
    artifacts, result, postcondition_ok, failure_class, working_fallback}."""
    intent = run.get("intent")
    ok = run.get("result") == "ok"
    post_ok = run.get("postcondition_ok")
    silent = bool(ok and post_ok is False)   # claimed success but postcondition failed
    goal_achieved = bool(ok and post_ok is not False)

    # 1. record the episode (with the lesson as a PROCEDURE, not a fact)
    lesson = run.get("lesson") or _derive_lesson(run)
    ep = episode_store.record({**run, "lesson": lesson,
                               "promote_to_skill": goal_achieved and bool(run.get("flow"))})

    out: dict[str, Any] = {
        "episode": ep["id"], "goal_achieved": goal_achieved,
        "silent_failure_detected": silent, "lesson": lesson,
        "what_worked": _worked(run), "what_failed": _failed(run),
        "new_skill_candidate": None, "antipattern_recorded": None, "tickets": [],
    }

    # 2. promote a good flow to a skill card
    if goal_achieved and run.get("flow"):
        skill_id = f"{intent}.{run.get('strategy', 'flow')}"
        skill_cards.create({"id": skill_id, "intent_patterns": [run.get("prompt") or intent],
                            "preferred_flow": [s.get("uri") if isinstance(s, dict) else s for s in run["flow"]],
                            "postconditions": [run.get("postcondition", {}).get("check", "artifact_exists")],
                            "risk": {"level": run.get("risk", "low"), "requires_human_approval": False}})
        out["new_skill_candidate"] = skill_id

    # 3. record the failed GUI/whatever path as an antipattern
    if not goal_achieved and run.get("working_fallback") and run.get("strategy"):
        failed_uris = [s.get("uri") for s in (run.get("flow") or []) if isinstance(s, dict)]
        if failed_uris:
            rid = f"avoid-{run.get('strategy')}-on-{run.get('failure_class', 'fail')}"
            antipatterns.add({"id": rid,
                              "trigger": {"intent": intent,
                                          "node_status": (run.get("environment") or {}).get("node_status")},
                              "avoid": failed_uris, "prefer": [run["working_fallback"]]})
            out["antipattern_recorded"] = rid

    # 4. ticket candidates for koru (missing capability / repeated blocker)
    out["tickets"] = _ticket_candidates(run, silent)
    return out


def _derive_lesson(run: dict) -> str:
    intent = run.get("intent", "task")
    # a claimed-ok run whose postcondition failed is a SILENT FAILURE — never call it "works"
    if run.get("result") == "ok" and run.get("postcondition_ok") is False:
        return (f"For {intent}, strategy '{run.get('strategy')}' reported ok but the postcondition "
                f"({run.get('failure_class', 'unmet')}) FAILED — treat as not done; harden the check.")
    if run.get("result") != "ok" and run.get("working_fallback"):
        return (f"For {intent}, when strategy '{run.get('strategy')}' fails "
                f"({run.get('failure_class', 'blocked')}), prefer '{run.get('working_fallback')}' first.")
    if run.get("result") == "ok" and run.get("postcondition_ok") is not False:
        return f"For {intent}, strategy '{run.get('strategy')}' works in this environment."
    return f"{intent}: {run.get('failure_class', 'unresolved')}."


def _worked(run: dict) -> list[str]:
    w = []
    if run.get("result") == "ok" and run.get("postcondition_ok") is not False:  # not on silent failure
        w.append(run.get("strategy") or "chosen strategy")
    if run.get("working_fallback"):
        w.append(run["working_fallback"])
    return w


def _failed(run: dict) -> list[str]:
    return [f"{run.get('strategy')}: {run.get('failure_class')}"] if run.get("result") != "ok" else []


def _ticket_candidates(run: dict, silent: bool) -> list[dict]:
    tickets = []
    fc = run.get("failure_class")
    if fc in ("missing_connector", "capability_missing") and run.get("missing_scheme"):
        tickets.append({"title": f"Generate {run['missing_scheme']}:// connector",
                        "priority": "high", "reason": f"blocked {run.get('intent')}"})
    if fc in ("node_stale_or_blocked", "node_stale"):
        tickets.append({"title": "Add fleet auto-reconcile before host ask",
                        "priority": "critical", "reason": "node stale caused task failure"})
    if silent:
        tickets.append({"title": f"Harden postcondition for {run.get('intent')}",
                        "priority": "high", "reason": "silent failure: claimed ok but postcondition failed"})
    return tickets
