#!/usr/bin/env python3
"""Build and run luce-procreate's tests in native and C modes: the property list
reader's test blocks, the inspect driver against Python's reading of generated
brushes, and a Luce caller. `--brushes DIR` also checks every .brush under DIR."""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from check_brushes import check
from fixtures import write_fixtures

EXE = ".exe" if os.name == "nt" else ""
MODES = {"native": ["--native"], "c": ["--backend=c"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=Path(os.environ.get("LUCE_BASE", ROOT.parent / f"luce-base/build/luce-base{EXE}")))
    parser.add_argument("--luce", type=Path, default=Path(os.environ.get("LUCE", ROOT.parent / f"luce/build/luce{EXE}")))
    parser.add_argument("--brushes", type=Path, help="also check every .brush under this folder")
    args = parser.parse_args()
    base, luce = args.base.resolve(), args.luce.resolve()
    env = dict(os.environ, LUCE_BASE=str(base))
    build = ROOT / "build"
    fixtures = write_fixtures(build / "fixtures")

    def run(*command):
        subprocess.run([str(part) for part in command], cwd=ROOT, env=env, check=True, timeout=600)

    for mode, flags in MODES.items():
        print(f"MODE {mode}", flush=True)
        run(base, "test", ROOT / "src/plist_tests.lucb", *flags)
        inspect = build / mode / f"inspect{EXE}"
        inspect.parent.mkdir(parents=True, exist_ok=True)
        run(base, "build", ROOT / "tests/inspect.lucb", *flags, "-o", inspect)
        problems = check(inspect, fixtures["good"], fixtures["bad"], quiet=True)
        if args.brushes:
            problems += check(inspect, sorted(args.brushes.rglob("*.brush")), quiet=True)
        for problem in problems:
            print("PROBLEM", problem)
        if problems:
            sys.exit(1)
        print(f"PASS inspect reads the fixtures{' and ' + str(args.brushes) if args.brushes else ''} as Python does", flush=True)
        smoke = build / mode / f"smoke{EXE}"
        run(luce, "build", ROOT / "tests/luce/smoke.luc", *flags, "-o", smoke)
        run(smoke, fixtures["good"][0])
    print("PASS luce-procreate")


if __name__ == "__main__":
    main()
