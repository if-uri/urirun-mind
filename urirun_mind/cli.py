# Author: Tom Sapletta · Part of the ifURI solution.
"""urirun-mind CLI: assess / reflect / skills / gaps over the cognitive memory."""
from __future__ import annotations
import argparse, json
from . import episode_store, skill_cards, strategy_selector, reflection


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="urirun-mind")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("assess"); a.add_argument("prompt"); a.add_argument("--intent", default="")
    a.add_argument("--node", default="host"); a.add_argument("--node-status", default="")
    a.add_argument("--level", type=int, default=3)
    sub.add_parser("skills")
    g = sub.add_parser("reflect"); g.add_argument("--run-json", required=True)
    args = ap.parse_args(argv)
    if args.cmd == "assess":
        env = {"node": args.node, "node_status": args.node_status or None}
        sel = strategy_selector.select(args.intent or args.prompt, prompt=args.prompt, environment=env, level=args.level)
        print(json.dumps(sel, indent=1, default=str)); return 0
    if args.cmd == "skills":
        print(json.dumps(skill_cards.search(""), indent=1, default=str)); return 0
    if args.cmd == "reflect":
        print(json.dumps(reflection.evaluate(json.loads(args.run_json)), indent=1, default=str)); return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
