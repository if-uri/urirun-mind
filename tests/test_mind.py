# Author: Tom Sapletta · Part of the ifURI solution.
"""The cognitive layer: episodes remember, skills replay, antipatterns steer away, the
policy gates by autonomy level, and reflection turns a run into learning + tickets."""
import pytest

from urirun_mind import (antipatterns, autonomy_policy, capability_graph,
                         episode_store, reflection, skill_cards, strategy_selector)


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("URIRUN_MIND_DIR", str(tmp_path))


# --- episode store + fingerprint ---
def test_fingerprint_stable_and_env_sensitive():
    a = episode_store.env_fingerprint({"node": "lenovo", "os": "linux", "connectors": {"kvm": "stale"}})
    b = episode_store.env_fingerprint({"node": "lenovo", "os": "linux", "connectors": {"kvm": "stale"}})
    c = episode_store.env_fingerprint({"node": "lenovo", "os": "linux", "connectors": {"kvm": "fresh"}})
    assert a == b and a != c and a.startswith("lenovo:")


def test_record_and_similar_prefers_matching_env():
    env = {"node": "host", "os": "linux"}
    episode_store.record({"intent": "office.document.create", "environment": env,
                          "flow": ["fs://host/file/command/write"], "result": "ok"})
    fp = episode_store.env_fingerprint(env)
    sim = episode_store.similar("office.document.create", fp, result="ok")
    assert sim and sim[0]["fingerprint"] == fp and sim[0]["flow"]


# --- autonomy levels ---
def test_autonomy_gates_by_level():
    assert autonomy_policy.decide("fs://host/file/command/write", level=2)["allowed"]      # local artifact @L2
    assert not autonomy_policy.decide("node://x/connector/command/install", level=2)["allowed"]  # needs L3
    assert autonomy_policy.decide("node://x/connector/command/install", level=3)["allowed"]


def test_autonomy_never_auto_and_approval():
    assert autonomy_policy.decide("email://x/message/command/send", level=5)["needs_approval"]
    assert autonomy_policy.decide("fiverr://x/order/command/pay", level=5)["needs_approval"]
    d = autonomy_policy.decide("secret://x/credential/command/export", level=5)
    assert d["allowed"] is False and "never" in d["reason"]


# --- antipatterns steer away ---
def test_antipattern_avoids_gui_on_stale_node():
    antipatterns.add({"id": "gui-first-office-stale",
                      "trigger": {"intent": "office.document.create", "node_status": "stale"},
                      "avoid": ["app://*/desktop/command/launch"], "prefer": ["fs://host/file/command/write"]})
    matched = antipatterns.match("office.document.create", "stale")
    assert antipatterns.is_avoided("app://lenovo/desktop/command/launch", matched) == "gui-first-office-stale"
    assert antipatterns.is_avoided("fs://host/file/command/write", matched) is None


# --- capability graph fallbacks ---
def test_capability_graph_walks_fallbacks():
    r = capability_graph.resolve("office.document.create", available={"markdown.write"})
    assert r["complete"] and r["satisfied"]["document.write"]["method"] == "markdown.write"
    r2 = capability_graph.resolve("content.linkedin.from_youtube", available={"media.audio.transcribe"})
    assert not r2["complete"]   # only transcript satisfied; others unmet
    assert r2["satisfied"]["transcript.extract"]["method"] == "media.audio.transcribe"


# --- strategy selector: known-good before LLM ---
def test_selector_replays_skill_before_fresh():
    skill_cards.create({"id": "office.document.create.headless",
                        "intent_patterns": ["testuj biuro", "utwórz dokument"],
                        "preferred_flow": ["fs://host/file/command/write", "fs://host/file/query/stat"]})
    sel = strategy_selector.select("office.document.create", prompt="testuj biuro na lenovo",
                                   environment={"node": "lenovo", "node_status": "stale"}, level=3)
    assert sel["source"] == "skill" and sel["flow"] and sel["runnable"]


def test_selector_fresh_when_no_memory():
    sel = strategy_selector.select("brand.new.intent", environment={"node": "host"})
    assert sel["source"] == "fresh" and sel["flow"] == []


# --- reflection closes the loop ---
def test_reflection_promotes_skill_and_records_episode():
    run = {"intent": "office.document.create", "prompt": "testuj biuro", "strategy": "headless",
           "environment": {"node": "host"}, "flow": [{"uri": "fs://host/file/command/write"}],
           "result": "ok", "postcondition_ok": True, "postcondition": {"check": "artifact_exists"}}
    out = reflection.evaluate(run)
    assert out["goal_achieved"] and out["new_skill_candidate"] == "office.document.create.headless"
    assert skill_cards.show("office.document.create.headless")


def test_reflection_detects_silent_failure_and_tickets():
    run = {"intent": "office.document.create", "strategy": "gui_editor", "result": "ok",
           "postcondition_ok": False, "flow": [{"uri": "app://lenovo/desktop/command/launch"}]}
    out = reflection.evaluate(run)
    assert out["silent_failure_detected"] is True
    assert any("Harden postcondition" in t["title"] for t in out["tickets"])


def test_reflection_records_antipattern_and_connector_ticket():
    run = {"intent": "content.linkedin.from_youtube", "strategy": "youtube_direct",
           "result": "failed", "failure_class": "missing_connector", "missing_scheme": "youtube",
           "working_fallback": "media.audio.transcribe",
           "environment": {"node": "host", "node_status": "ready"},
           "flow": [{"uri": "youtube://host/video/query/transcript"}]}
    out = reflection.evaluate(run)
    assert out["antipattern_recorded"] and any("youtube" in t["title"] for t in out["tickets"])
