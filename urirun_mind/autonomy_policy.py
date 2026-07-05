# Author: Tom Sapletta · Part of the ifURI solution.
"""Autonomy levels — self-directed, not uncontrolled. L0 observe … L5 commit.

Each action class needs a minimum autonomy level; the current level gates what runs
without human approval. External/committing actions (send, publish, pay, delete) never
run automatically; credential export and destructive-without-backup are never auto at any
level. This is what makes the system autonomous AND safe.
"""
from __future__ import annotations

from typing import Any

LEVELS = {
    0: "observe",     # only observe/report
    1: "propose",     # propose a plan, execute nothing
    2: "safe-run",    # read-only + local artifacts
    3: "repair",      # install connectors, reconcile/repair a node, rebuild registry
    4: "external",    # create drafts of messages/orders/posts (not sent)
    5: "commit",      # send/publish/pay — only with human approval
}

# action class → minimum level that MAY perform it automatically
_MIN_LEVEL = {
    "query": 0, "propose": 1,
    "local_artifact_create": 2, "connector_smoke": 2, "read_only": 2,
    "connector_generate": 3, "connector_install": 3, "fleet_reconcile_safe": 3,
    "node_restart": 3, "registry_rebuild": 3,
    "mailbox_mutate": 4,   # move-to-Junk etc. — reversible mailbox write, auto at L4
    "draft_message": 4, "draft_order": 4, "repo_publish_public": 4,
}
# always require explicit human approval regardless of level
_APPROVAL_REQUIRED = {"email.send", "linkedin.publish", "fiverr.order", "payment.confirm",
                      "file.delete", "message.send", "post.publish"}
# never automatic at any level
_NEVER_AUTO = {"credential_export", "destructive_without_backup"}

# map a URI verb → action class (for classifying a step)
_VERB_CLASS = [
    ("credential", "credential_export"), ("/command/delete", "file.delete"),
    ("/command/pay", "payment.confirm"), ("/command/publish", "post.publish"),
    ("/command/send", "message.send"), ("/order/command", "fiverr.order"),
    ("/command/move", "mailbox_mutate"),
    ("connector/command/generate", "connector_generate"),
    ("connector/command/install", "connector_install"),
    ("runtime/command/restart", "node_restart"), ("registry/command/rebuild", "registry_rebuild"),
    ("repo/command/publish", "repo_publish_public"),
    ("/command/draft", "draft_message"), ("/command/write", "local_artifact_create"),
    ("/command/create", "local_artifact_create"), ("/query/", "query"),
]


def classify_action(uri: str) -> str:
    u = str(uri)
    for needle, cls in _VERB_CLASS:
        if needle in u:
            return cls
    return "propose"


def decide(uri: str, *, level: int = 3) -> dict[str, Any]:
    """Can this URI run automatically at ``level``? Returns {allowed, needs_approval, reason}."""
    cls = classify_action(uri)
    if cls in _NEVER_AUTO:
        return {"allowed": False, "needs_approval": False, "class": cls,
                "reason": "never automatic (blocked at every level)"}
    if cls in _APPROVAL_REQUIRED:
        return {"allowed": False, "needs_approval": True, "class": cls,
                "reason": "requires explicit human approval"}
    need = _MIN_LEVEL.get(cls, 1)
    if level >= need:
        return {"allowed": True, "needs_approval": False, "class": cls, "reason": f"level {level} >= {need}"}
    return {"allowed": False, "needs_approval": True, "class": cls,
            "reason": f"needs autonomy level {need} ({LEVELS.get(need)}), current {level}"}


def gate_plan(steps: list[dict], *, level: int = 3) -> dict[str, Any]:
    """Classify every step; return which run auto, which need approval, which are forbidden."""
    auto, approval, forbidden = [], [], []
    for s in steps:
        d = decide(s.get("uri", ""), level=level)
        (auto if d["allowed"] else (forbidden if not d["needs_approval"] and not d["allowed"]
                                    and "never" in d["reason"] else approval)).append(
            {"uri": s.get("uri"), **d})
    return {"level": level, "auto": auto, "approval": approval, "forbidden": forbidden,
            "runnable": not forbidden}
