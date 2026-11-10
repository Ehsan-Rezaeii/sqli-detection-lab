"""Explicit study stages; server startup never invokes these stages."""

import argparse
from pathlib import Path

from .artifacts import audit
from .data import acquire, prepare
from .experiment import development, final, freeze, run_limited


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=["acquire", "prepare", "development", "freeze", "final", "audit", "smoke"],
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--offline", type=Path)
    parser.add_argument("--require-final", action="store_true")
    args = parser.parse_args()
    raw = args.root / "data/raw/payload_full.csv"
    if args.command == "acquire":
        acquire(raw, offline=args.offline)
    elif args.command == "prepare":
        prepare(raw, args.root / "results")
    elif args.command == "development":
        run_limited(development, raw, args.root)
    elif args.command == "freeze":
        freeze(args.root)
    elif args.command == "final":
        run_limited(final, raw, args.root)
    elif args.command == "audit":
        print(audit(args.root, require_final=args.require_final))
    else:
        from .smoke import smoke

        print(run_limited(smoke))
