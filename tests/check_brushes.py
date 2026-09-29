"""Compares tests/inspect's reading of brushes with Python's zipfile and plistlib.

`check(inspect, good, bad)` runs the driver over `good` brushes (each must read the
same as Python reads it) and `bad` ones (each must fail). Run directly with a folder
to check every .brush under it: `python3 tests/check_brushes.py build/inspect DIR`."""
import math
import plistlib
import subprocess
import sys
import zipfile
from pathlib import Path


def expected(path):
    """What the reader should report for `path`, as Python reads it."""
    with zipfile.ZipFile(path) as brush:
        names = set(brush.namelist())
        size = lambda name: len(brush.read(name)) if name in names else 0
        top = plistlib.loads(brush.read("Brush.archive"))
        result = {"SHAPE": size("Shape.png"), "GRAIN": size("Grain.png"),
                  "THUMBNAIL": size("QuickLook/Thumbnail.png")}
    objects = top["$objects"]
    root = objects[top["$top"]["root"].data]

    def resolve(value):
        if isinstance(value, plistlib.UID):
            value = objects[value.data]
            if value == "$null":
                return None
        return value

    settings = {}
    for key, value in root.items():
        value = resolve(value)
        if isinstance(value, dict) and isinstance(value.get("NS.string"), plistlib.UID):
            value = resolve(value["NS.string"])
        if value is None:
            settings[key] = ("NULL",)
        elif isinstance(value, (bool, int, float)):
            settings[key] = ("NUMBER", float(value))
        elif isinstance(value, str) and value:
            settings[key] = ("TEXT", value)
        else:
            settings[key] = ("OTHER",)
    name = settings.get("name", ("",))
    result["NAME"] = name[1] if name[0] == "TEXT" else ""
    result["KEYS"] = settings
    return result


def readings(output):
    """The driver's output as {path: reading} and {path: failure}."""
    read, failed, current = {}, {}, None
    for line in output.splitlines():
        word, _, rest = line.partition(" ")
        if word == "FAIL":
            path, _, message = rest.partition("\t")
            failed[path] = message
        elif word == "BRUSH":
            current = {"KEYS": {}}
            read[rest] = current
        elif word in ("NAME",):
            current[word] = rest
        elif word in ("SHAPE", "GRAIN", "THUMBNAIL", "KEYS"):
            current["COUNT" if word == "KEYS" else word] = int(rest)
        elif word == "NUMBER":
            key, _, number = rest.partition(" ")
            current["KEYS"][key] = ("NUMBER", float(number))
        elif word == "TEXT":
            key, _, text = rest.partition(" ")
            current["KEYS"][key] = ("TEXT", text)
        elif word in ("NULL", "OTHER"):
            current["KEYS"][rest] = (word,)
    return read, failed


def same(got, want):
    if got[0] != want[0]:
        return False
    if got[0] == "NUMBER":
        return math.isclose(got[1], want[1], rel_tol=1e-5, abs_tol=1e-6)
    return got == want


def check(inspect, good, bad=(), quiet=False):
    """Returns the problems found; prints one line per good brush unless quiet."""
    paths = [str(path) for path in [*good, *bad]]
    run = subprocess.run([str(inspect), *paths], capture_output=True, text=True, timeout=600)
    read, failed = readings(run.stdout)
    problems = []
    for path in map(str, good):
        if path in failed:
            problems.append(f"{path}: failed: {failed[path]}")
            continue
        got, want = read.get(path), expected(path)
        if got is None:
            problems.append(f"{path}: no reading")
            continue
        for field in ("NAME", "SHAPE", "GRAIN", "THUMBNAIL"):
            if got.get(field) != want[field]:
                problems.append(f"{path}: {field} {got.get(field)!r} != {want[field]!r}")
        if got.get("COUNT") != len(want["KEYS"]) or set(got["KEYS"]) != set(want["KEYS"]):
            problems.append(f"{path}: keys differ")
        for key, value in want["KEYS"].items():
            if key in got["KEYS"] and not same(got["KEYS"][key], value):
                problems.append(f"{path}: {key} {got['KEYS'][key]} != {value}")
        if not quiet:
            print(f"OK {got.get('NAME')!r} shape={got.get('SHAPE')} grain={got.get('GRAIN')} "
                  f"thumbnail={got.get('THUMBNAIL')} settings={got.get('COUNT')}  {path}")
    for path in map(str, bad):
        if path not in failed:
            problems.append(f"{path}: read, but should have failed")
    return problems


if __name__ == "__main__":
    brushes = sorted(Path(sys.argv[2]).rglob("*.brush"))
    problems = check(Path(sys.argv[1]).resolve(), brushes)
    for problem in problems:
        print("PROBLEM", problem)
    print(f"{len(brushes) - len({p.split(':')[0] for p in problems})}/{len(brushes)} brushes read the same as Python reads them")
    sys.exit(1 if problems else 0)
