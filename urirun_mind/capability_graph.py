# Author: Tom Sapletta · Part of the ifURI solution.
"""Capability graph — not a flat list of connectors, but requires + fallbacks.

A high-level capability (``content.linkedin.from_youtube``) requires sub-capabilities,
each with an ordered fallback chain (youtube.transcript → media.audio.transcribe →
browser.copy_transcript). So "no youtube connector" never stops the system — it walks the
fallback chain. resolve() returns, for a capability, which sub-capabilities are satisfiable
given what's available and the fallback that satisfies each.
"""
from __future__ import annotations

from typing import Any

# capability → {requires: [sub-cap], fallbacks: {sub-cap: [ordered alternatives]}}
GRAPH: dict[str, dict] = {
    "content.linkedin.from_youtube": {
        "requires": ["video.source", "transcript.extract", "clip.create", "post.write", "linkedin.draft"],
        "fallbacks": {
            "transcript.extract": ["youtube.transcript", "media.audio.transcribe", "browser.copy_transcript"],
            "linkedin.draft": ["linkedin.api", "browser.linkedin", "artifact.markdown"],
            "clip.create": ["media.video.clip", "artifact.timestamp_list"],
        },
    },
    "office.document.create": {
        "requires": ["document.write"],
        "fallbacks": {"document.write": ["document.create", "sheet.write", "markdown.write",
                                         "host.generate_and_sync", "browser.document_edit", "gui.editor"]},
    },
    "procurement.fiverr.pcb": {
        "requires": ["project.find", "brief.write", "vendor.search", "order.draft"],
        "fallbacks": {
            "vendor.search": ["fiverr.search", "browser.fiverr", "artifact.vendor_list"],
            "order.draft": ["fiverr.order.draft", "artifact.order_brief"],
        },
    },
}


def resolve(capability: str, available: set[str]) -> dict[str, Any]:
    """For a capability, resolve each required sub-capability to the first available
    fallback. Returns satisfiable subs (+ chosen method) and the unmet ones."""
    node = GRAPH.get(capability)
    if not node:
        return {"known": False, "capability": capability}
    satisfied, unmet = {}, []
    for sub in node["requires"]:
        chain = node.get("fallbacks", {}).get(sub, [sub])
        pick = next((m for m in chain if m in available), None)
        if pick:
            satisfied[sub] = {"method": pick, "chain": chain}
        else:
            unmet.append({"sub": sub, "chain": chain})
    return {"known": True, "capability": capability, "satisfied": satisfied,
            "unmet": unmet, "complete": not unmet}


def fallbacks(capability: str, sub: str) -> list[str]:
    return (GRAPH.get(capability, {}).get("fallbacks", {}) or {}).get(sub, [sub])


def update(capability: str, spec: dict) -> dict:
    """Add/extend a capability node in the graph (learning new decompositions)."""
    GRAPH[capability] = {"requires": spec.get("requires") or [],
                         "fallbacks": spec.get("fallbacks") or {}}
    return GRAPH[capability]
