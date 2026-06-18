#!/usr/bin/env python3
"""CLI wrapper for mem0 — used by orchestrator in Content Zavod pipeline."""

import sys
import json
import argparse
from pathlib import Path


def load_client():
    config_path = Path.home() / ".mem0" / "config.json"
    if not config_path.exists():
        print(json.dumps({"error": "~/.mem0/config.json not found"}))
        sys.exit(1)
    from mem0 import MemoryClient
    with open(config_path) as f:
        cfg = json.load(f)
    return MemoryClient(api_key=cfg["api_key"])


def cmd_add(args):
    client = load_client()
    client.add(args.text, user_id=args.user_id)
    if args.agent:
        print(json.dumps({"status": "ok"}))
    else:
        print("Added.")


def cmd_search(args):
    client = load_client()
    results = client.search(args.query, filters={"user_id": args.user_id})
    if args.agent:
        print(json.dumps(results))
    else:
        for r in results:
            print(r.get("memory", ""))


def main():
    parser = argparse.ArgumentParser(prog="mem0")
    parser.add_argument("--agent", action="store_true", help="Output clean JSON")
    sub = parser.add_subparsers(dest="cmd")

    p_add = sub.add_parser("add")
    p_add.add_argument("text")
    p_add.add_argument("--user-id", default="content-zavod")
    p_add.add_argument("--agent", action="store_true")

    p_search = sub.add_parser("search")
    p_search.add_argument("query")
    p_search.add_argument("--user-id", default="content-zavod")
    p_search.add_argument("--agent", action="store_true")

    args = parser.parse_args()

    if args.cmd == "add":
        cmd_add(args)
    elif args.cmd == "search":
        cmd_search(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
