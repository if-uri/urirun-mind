# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
"""urirun-mind — the cognitive layer over connectors. Operational self-awareness.

Not human consciousness — an operating model of self: I know what I want, what I have,
what worked before, what I can't do, when to build/repair a capability, when to ask a
human, and how to measure real success. Episode memory + skill cards + antipatterns +
capability graph + autonomy levels + strategy selection + reflection — so koru and
connectorgen become elements of a continuous self-improvement loop, not just tools.

Learn PROCEDURES, not answers: store "for office tasks on a stale node, go headless
first", never "LibreOffice missing on lenovo".
"""
from __future__ import annotations

from . import (
    antipatterns, autonomy_policy, capability_graph, episode_store,
    reflection, skill_cards, strategy_selector,
)

__all__ = ["antipatterns", "autonomy_policy", "capability_graph", "episode_store",
           "reflection", "skill_cards", "strategy_selector"]
