"""Entry point: python run.py [--dry-run] [--verbose]"""

import argparse

try:
    from flik.main import Flik
except ImportError as exc:
    print("flik couldn't start because a required library is missing:")
    print(f"  {exc}")
    print()
    print("Fix: double-click  install.bat  once, then try again.")
    raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="flik",
        description="Dialogue-aware foreground F auto-presser for Genshin Impact.",
    )
    parser.add_argument(
        "-n", "--dry-run", "--observe",
        dest="dry_run",
        action="store_true",
        help="observe only: log detection + what WOULD be pressed, but never "
             "actually press F (use this to verify detection live and safely).",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="log detection telemetry (gold/fill/choice) ~twice a second.",
    )
    args = parser.parse_args()

    Flik(dry_run=args.dry_run, verbose=args.verbose).run()


if __name__ == "__main__":
    main()
