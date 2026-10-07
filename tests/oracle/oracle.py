#!/usr/bin/env python3
"""Write the generated brushes into DIRECTORY and check that INSPECT reads each the way
Python's zipfile and plistlib do, and refuses the broken ones.

Usage: oracle.py INSPECT DIRECTORY [BRUSHES]   (BRUSHES: also every .brush under it)"""
from pathlib import Path
import sys

from check_brushes import check
from fixtures import write_fixtures

fixtures = write_fixtures(Path(sys.argv[2]))
problems = check(Path(sys.argv[1]).resolve(), fixtures["good"], fixtures["bad"], quiet=True)
if len(sys.argv) > 3:
    problems += check(Path(sys.argv[1]).resolve(), sorted(Path(sys.argv[3]).rglob("*.brush")), quiet=True)
for problem in problems:
    print("PROBLEM", problem)
sys.exit(1 if problems else 0)
