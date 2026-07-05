# urirun-mind

The cognitive layer over connectors — **operational self-awareness**. Not human
consciousness: an operating model of self. *I know what I want, what I have, what worked
before, what I can't do, when to build/repair a capability, when to ask a human, and how
to measure real success.*

**Learn procedures, not answers.** Store *"for office tasks on a stale node, go headless
first"* — never *"LibreOffice missing on lenovo"*. Procedures transfer across nodes and tasks.

| module | role |
|---|---|
| `episode_store` | record every task as an episode, keyed by an **environment fingerprint**; retrieve similar (known-good first) |
| `skill_cards` | promote a working flow to a reusable **procedure**; search by intent; track success stats |
| `antipatterns` | learn from counter-examples — routes to **avoid** for an intent/node-status, and what to prefer |
| `capability_graph` | capability → required sub-capabilities + **fallback chains** (no youtube:// ≠ dead end) |
| `autonomy_policy` | **L0 observe → L5 commit**; gate each action; never auto for pay/publish/send/delete/credentials |
| `strategy_selector` | **known-good replay BEFORE the LLM** — skill → episode → fresh, minus antipattern routes, under the autonomy gate |
| `reflection` | after a run: silent-failure check, promote skill, record antipattern, emit **koru tickets** |

## The loop it closes
```
run → reflect → learn → ticket → koru → connector/code → smoke → publish → use
```
Round 1 of a task plans fresh; the failure teaches an antipattern + a procedure lesson.
Round 2 of the same task replays the known-good skill and avoids the failed path — cheaper,
less flaky, and honestly gated by autonomy level.

Part of the ifURI solution · Author: Tom Sapletta · Apache-2.0
