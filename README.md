# luce-procreate

A Procreate brush (`.brush`) reader for Luce/Base. A `.brush` is a ZIP holding
`Brush.archive` (an NSKeyedArchiver binary property list whose root SilicaBrush object
carries the settings: `paintSize`, `plotSpacing`, `shapeScatter`,
`dynamicsPressureSize`, `textureScale`, `name`, ...) and, when the brush has its own
images, `Shape.png` (the tip), `Grain.png` (the texture) and `QuickLook/Thumbnail.png`.
A brush using one of Procreate's built-in images names it in `bundledShapePath` /
`bundledGrainPath` instead.

This package reads; turning the settings into a painting engine's brush is the
caller's (luced-2d imports Procreate brushes through it). It depends on luce-std and
luce-compress (the ZIP reader); nothing foreign.

## From Luce

```luce
from luce_procreate.brush import ProcreateBrush

let brush = ProcreateBrush.open("Soft Airbrush.brush")
print(brush.name())                              # "" when the brush has none
let size = brush.number("paintSize", 0.5)        # integer, real or bool (0/1); else the fallback
let spacing = brush.number("plotSpacing", 0.1)
let shape = brush.shape_png()                    # PNG bytes; empty when a built-in shape is used
if shape.length == 0:
    print(brush.text("bundledShapePath"))        # which built-in; "" when absent
brush.close()
```

`ProcreateBrush`:

| Member | Result |
| --- | --- |
| `static open(path: str)` | the brush in that file, read whole (up to 512 MiB) |
| `static from_bytes(data: const u8[])` | the brush in those bytes (copied) |
| `name()` | the archived `name`, or empty |
| `has(key)` | whether the root object has a non-null setting `key` |
| `number(key, fallback = 0.0)` | an integer, real or bool (as 0/1) setting, else `fallback` |
| `text(key)` | a string setting (UIDs followed, archived NSStrings unwrapped), else empty |
| `shape_png()`, `grain_png()`, `thumbnail_png()` | the entry's bytes, empty when absent |
| `key_count()`, `key(index)` | the root object's keys in archive order (`$class` included), for diagnostics |
| `close()` | frees everything; later calls fail with `closed` |

Errors: `invalid` (not a ZIP, no `Brush.archive`, a damaged ZIP or property list,
not a keyed archive), `limit` (over the size, object or nesting limits), `closed`, and
luce-std's file errors from `open`.

## From Base

`import plist` reads any binary property list (`bplist00`): `parse(data, max_objects,
max_depth)` gives a `Plist` of flat `Value`s (null, bool, integer, real, date, data,
string, UID, array, dictionary) borrowing `data`, with UTF-16 strings converted to
UTF-8 and every offset, length and reference checked; cycles and nesting deeper than
the limit are refused. `unarchive(data)` reads an NSKeyedArchiver archive on top of
it: `KeyedArchive.root`, `member(object, key)` (UID followed, `$null` absent),
`resolve(index)` and `text(index)`.

## Tests

```
./test.sh                                        # native and C modes
python3 tests/run.py --brushes ~/Brushes          # also every .brush under a folder
```

`tests/run.py` runs the property list's test blocks (every object kind, damaged and
truncated lists, cycles, nesting and count limits, a keyed archive), writes fixtures
with Python's plistlib and zipfile (`tests/fixtures.py`: a small brush of our own and
four broken ones), checks `tests/inspect.lucb`'s reading of them against Python's,
and builds a Luce caller (`tests/luce/smoke.luc`). No third-party brushes are in the
repository; `--brushes` checks a local collection the same way.
