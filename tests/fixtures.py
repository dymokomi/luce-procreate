"""Writes the brushes luce-procreate's tests read, with Python's plistlib and zipfile.

`tiny.brush` is a small Procreate-style brush of our own making: an NSKeyedArchiver
Brush.archive (a SilicaBrush root with numbers, bools, a UTF-16 name, a built-in grain
path, a $null shape path, a 16-byte color, a large and a negative integer), a stored
Shape.png, a deflated thumbnail and no Grain.png. The others are broken on purpose."""
import plistlib
import struct
import zipfile
import zlib
from pathlib import Path


def png(width, height, value):
    """A tiny grayscale PNG."""
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    rows = b"".join(b"\0" + bytes([value]) * width for _ in range(height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def archive():
    """The Brush.archive of tiny.brush."""
    UID = plistlib.UID
    root = {
        "$class": UID(4), "name": UID(2), "bundledShapePath": UID(0), "bundledGrainPath": UID(3),
        "color": UID(5), "paintSize": 0.25, "plotSpacing": 0.125, "shapeScatter": 0.5,
        "dynamicsPressureSize": 0.75, "textureScale": 2.5, "maxSize": 4, "oriented": True,
        "shapeInverted": False, "stamp": 0, "largeCount": 1 << 40, "offset": -3,
    }
    objects = ["$null", root, "Tiny ✓ brush", "Brush-Preset-Blank.png",
               {"$classes": ["SilicaBrush", "NSObject"], "$classname": "SilicaBrush"}, bytes(16)]
    top = {"$archiver": "NSKeyedArchiver", "$version": 100000, "$top": {"root": UID(1)}, "$objects": objects}
    return plistlib.dumps(top, fmt=plistlib.FMT_BINARY)


def write_fixtures(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(directory / "tiny.brush", "w") as brush:
        brush.writestr(zipfile.ZipInfo("Brush.archive"), archive(), zipfile.ZIP_DEFLATED)
        brush.writestr(zipfile.ZipInfo("QuickLook/Thumbnail.png"), png(16, 8, 200), zipfile.ZIP_DEFLATED)
        brush.writestr(zipfile.ZipInfo("Shape.png"), png(8, 8, 0), zipfile.ZIP_STORED)
    with zipfile.ZipFile(directory / "no-archive.brush", "w") as brush:
        brush.writestr("Shape.png", png(4, 4, 0))
    (directory / "not-a-zip.brush").write_bytes(b"this is not a brush at all, nor a ZIP archive")
    with zipfile.ZipFile(directory / "bad-plist.brush", "w") as brush:
        brush.writestr("Brush.archive", b"bplist00" + bytes(40))
    with zipfile.ZipFile(directory / "not-keyed.brush", "w") as brush:
        brush.writestr("Brush.archive", plistlib.dumps({"name": "plain"}, fmt=plistlib.FMT_BINARY))
    return {"good": [directory / "tiny.brush"],
            "bad": [directory / name for name in ("no-archive.brush", "not-a-zip.brush", "bad-plist.brush", "not-keyed.brush")]}


if __name__ == "__main__":
    import sys
    print(write_fixtures(sys.argv[1] if len(sys.argv) > 1 else "build/fixtures"))
