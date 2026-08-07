"""Splat (3D Gaussian) parser — SPZ decoding, PLY parsing, binary conversion for Godot.

The 3D Gaussian Splatting PLY format stores per-vertex:
  - x, y, z (float32): position
  - f_dc_0, f_dc_1, f_dc_2 (float32): SH DC coefficients (0.5 + SH_C0 * val gives linear RGB)
  - opacity (float32): alpha
  - scale_0..2 (float32): covariance scaling
  - rot_0..3 (float32): covariance rotation (quaternion)

CORRECTION (2026-07-30): .spz files are NOT gzip-compressed PLY. Real Niantic
SPZ (both legacy v1-3 and current v4) uses its own packed binary attribute
layout (24-bit fixed-point positions, 8-bit log-encoded scales, quantized
quaternion rotations, quantized SH) — confirmed against the official format
spec at github.com/nianticlabs/spz. The previous version of this file did
`gzip.open(path)` and fed the raw bytes straight into the PLY parser, which
only works if you happen to be handed a file that's literally gzip(PLY) —
not a real .spz file from Niantic's spec (Scaniverse, World Labs/Marble,
etc.). Real .spz now goes through Niantic's official Python library instead
of a hand-rolled decoder — see `_load_gaussian_cloud_via_spz_lib()` below.

Also: v4 files start with a plaintext "NGSP" magic header and split data
across parallel ZSTD streams — a single `gzip.open()` call would fail
outright on these (wrong magic bytes), not just misparse them.
"""

import logging
import math
import os
import struct
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger("godot-mcp.splat")

SH_C0 = 0.28209479177387814

# Compact binary format for bridge transfer:
#   [N: uint32] [x:f32 y:f32 z:f32 r:u8 g:u8 b:u8 a:u8] x N
_STRUCT_HEADER = struct.Struct("<I")
_STRUCT_SPLAT = struct.Struct("<fffBBBB")
_STRUCT_SPLAT_FULL = struct.Struct("<fffBBBBfff")


def _sh_dc_to_rgb_byte(v: float) -> int:
    """Convert an SH DC coefficient to a 0-255 RGB byte (shared by PLY and SPZ paths)."""
    return int(max(0.0, min(1.0, 0.5 + SH_C0 * v)) * 255)


def _load_gaussian_cloud_via_spz_lib(path: str) -> dict[str, Any]:
    """Load a real .spz file via Niantic's official `spz` Python bindings.

    HONESTY NOTE: the exact Python binding function/attribute names could
    not be independently confirmed in this session — GitHub blocked fetching
    `src/python/README.md` (not a prior search/fetch result), so only the
    documented C++ API (`loadSpz` / `GaussianCloud`) and the byte-level
    format spec were confirmed against the official README. This function
    tries the conventional nanobind naming and FAILS LOUDLY with the actual
    installed attribute list if it doesn't match, rather than silently
    guessing wrong and returning bad data. If this fires, check
    `import spz; dir(spz)` on the actual installed package and update the
    attribute names below — don't just suppress the error.
    """
    try:
        import spz  # type: ignore[import-not-found]
    except ImportError:
        return {
            "success": False,
            "error": (
                "Python 'spz' package not installed. Install with: "
                "pip install git+https://github.com/nianticlabs/spz.git "
                "(requires a C++ toolchain — MSVC Build Tools on Windows — "
                "since it's a nanobind/C++ extension, not pure Python). "
                "Or: uv sync --extra splat"
            ),
        }

    load_fn = getattr(spz, "load_spz", None) or getattr(spz, "loadSpz", None)
    if load_fn is None:
        available = [a for a in dir(spz) if not a.startswith("_")]
        return {
            "success": False,
            "error": (
                "Installed 'spz' package doesn't expose a load_spz/loadSpz "
                f"function this code recognizes. Available attributes: {available}. "
                "Update _load_gaussian_cloud_via_spz_lib() in splat_import.py "
                "to match the actual installed API — do not guess."
            ),
        }

    try:
        cloud = load_fn(path)
    except Exception as e:
        return {"success": False, "error": f"spz library failed to load {path}: {e}"}

    # GaussianCloud fields per the official C++/Swift API: positions (flat
    # xyz*N), scales (log-scale xyz*N), colors (SH DC xyz*N), alphas (N).
    # Access defensively — same honesty reasoning as above.
    positions_flat = getattr(cloud, "positions", None)
    scales_flat = getattr(cloud, "scales", None)
    colors_flat = getattr(cloud, "colors", None)
    if positions_flat is None or colors_flat is None:
        available = [a for a in dir(cloud) if not a.startswith("_")]
        return {
            "success": False,
            "error": (
                "Loaded GaussianCloud object is missing expected "
                f"positions/colors attributes. Available: {available}. "
                "Update the field names in _load_gaussian_cloud_via_spz_lib()."
            ),
        }

    n = len(positions_flat) // 3
    positions = [tuple(positions_flat[i * 3 : i * 3 + 3]) for i in range(n)]
    colors = [
        (
            _sh_dc_to_rgb_byte(colors_flat[i * 3]),
            _sh_dc_to_rgb_byte(colors_flat[i * 3 + 1]),
            _sh_dc_to_rgb_byte(colors_flat[i * 3 + 2]),
        )
        for i in range(n)
    ]
    if scales_flat is not None and len(scales_flat) == n * 3:
        scales_3d = [
            (
                max(0.001, math.exp(scales_flat[i * 3])),
                max(0.001, math.exp(scales_flat[i * 3 + 1])),
                max(0.001, math.exp(scales_flat[i * 3 + 2])),
            )
            for i in range(n)
        ]
    else:
        scales_3d = [(0.05, 0.05, 0.05)] * n

    return {"success": True, "count": n, "positions": positions, "colors": colors, "scales_3d": scales_3d}


def parse_ply_header(path: str) -> tuple[list[dict], int, str]:
    """Parse a PLY file header, return (elements, total_vertex_count, format)."""
    with open(path, "rb") as f:
        header_bytes = b""
        while True:
            line = f.readline()
            header_bytes += line
            if line.strip() == b"end_header":
                break

    header_text = header_bytes.decode("ascii")
    fmt = "ascii"
    elements = []
    current_element: dict[str, Any] = {}
    vertex_count = 0

    for line in header_text.splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        if parts[0] == "format":
            fmt = parts[1]
        elif parts[0] == "element":
            if current_element and current_element.get("name") == "vertex":
                vertex_count = current_element["count"]
            current_element = {"name": parts[1], "count": int(parts[2]), "properties": []}
            elements.append(current_element)
        elif parts[0] == "property" and current_element:
            dtype = parts[1]
            name = parts[2]
            current_element["properties"].append({"name": name, "type": dtype})

    if current_element and current_element.get("name") == "vertex":
        vertex_count = current_element["count"]

    return elements, vertex_count, fmt


def _read_ply_value(file, dtype: str) -> float | int:
    """Read a single PLY property value from a binary file."""
    type_map = {
        "float": ("f", 4),
        "float32": ("f", 4),
        "double": ("d", 8),
        "uchar": ("B", 1),
        "uint8": ("B", 1),
        "int": ("i", 4),
        "int32": ("i", 4),
        "uint": ("I", 4),
        "uint32": ("I", 4),
        "short": ("h", 2),
        "int16": ("h", 2),
        "ushort": ("H", 2),
    }
    fmt_char, size = type_map.get(dtype, ("f", 4))
    data = file.read(size)
    return struct.unpack("<" + fmt_char, data)[0]


def parse_splat_ply(
    path: str,
    max_splats: int = 200000,
    pos_scale: float = 1.0,
) -> dict[str, Any]:
    """Parse a 3D Gaussian Splatting PLY file (binary_little_endian).

    Returns positions (list of xyz triples) and colors (list of rgba bytes).
    """
    elements, vertex_count, fmt = parse_ply_header(path)
    n = min(vertex_count, max_splats)

    # Find vertex property indices
    vertex_el = next((e for e in elements if e["name"] == "vertex"), None)
    if not vertex_el:
        return {"success": False, "error": "No vertex element in PLY header"}

    prop_names = [p["name"] for p in vertex_el["properties"]]
    required = {"x", "y", "z", "f_dc_0", "f_dc_1", "f_dc_2"}
    missing = required - set(prop_names)
    if missing:
        return {
            "success": False,
            "error": f"Missing properties in PLY: {missing}. Got: {prop_names[:12]}",
        }

    positions = []
    colors = []
    scales_3d = []
    header_size = _ply_header_size(path)

    has_scale = "scale_0" in prop_names

    with open(path, "rb") as f:
        f.seek(header_size)
        for _ in range(n):
            data = f.read(4 * len(prop_names)) if fmt != "ascii" else b""
            if fmt == "binary_little_endian":
                vals = []
                f.seek(-len(data), 1)
                for prop in vertex_el["properties"]:
                    val = _read_ply_value(f, prop["type"])
                    vals.append(val)

                px = vals[prop_names.index("x")]
                py = vals[prop_names.index("y")]
                pz = vals[prop_names.index("z")]

                r = vals[prop_names.index("f_dc_0")]
                g = vals[prop_names.index("f_dc_1")]
                b = vals[prop_names.index("f_dc_2")]

                def sh_to_rgb(v: float) -> float:
                    return max(0.0, min(1.0, 0.5 + SH_C0 * v))

                positions.append((px * pos_scale, py * pos_scale, pz * pos_scale))
                colors.append((int(sh_to_rgb(r) * 255), int(sh_to_rgb(g) * 255), int(sh_to_rgb(b) * 255)))

                if has_scale:
                    sx = vals[prop_names.index("scale_0")]
                    sy = vals[prop_names.index("scale_1")]
                    sz = vals[prop_names.index("scale_2")]
                    # Convert log-scale to linear and clamp
                    scales_3d.append(
                        (
                            max(0.001, math.exp(sx)) * pos_scale,
                            max(0.001, math.exp(sy)) * pos_scale,
                            max(0.001, math.exp(sz)) * pos_scale,
                        )
                    )
                else:
                    scales_3d.append((0.05, 0.05, 0.05))

    return {
        "success": True,
        "count": len(positions),
        "positions": positions,
        "colors": colors,
        "scales_3d": scales_3d,
    }


def _ply_header_size(path: str) -> int:
    """Calculate the byte offset where PLY vertex data begins."""
    with open(path, "rb") as f:
        while True:
            line = f.readline()
            if line.strip() == b"end_header":
                return f.tell()


def write_compact_binary(
    positions: list[tuple[float, float, float]],
    colors: list[tuple[int, int, int]],
    scales_3d: list[tuple[float, float, float]] | None = None,
    output_path: str = "splat.bin",
):
    """Write splat data as compact binary for GDScript bridge to read.

    Format: [N:uint32] [x:f32 y:f32 z:f32 r:u8 g:u8 b:u8 a:u8 sx:f32 sy:f32 sz:f32] x N
    """
    n = len(positions)
    has_scale = scales_3d is not None and len(scales_3d) == n
    with open(output_path, "wb") as f:
        f.write(_STRUCT_HEADER.pack(n))
        for i in range(n):
            px, py, pz = positions[i]
            r, g, b = colors[i]
            f.write(_STRUCT_SPLAT.pack(px, py, pz, r, g, b, 255))
            if has_scale:
                sx, sy, sz = scales_3d[i]
                f.write(struct.pack("<fff", sx, sy, sz))
            else:
                f.write(struct.pack("<fff", 0.05, 0.05, 0.05))
    logger.info("Wrote %d splats (scales=%s) to %s", n, has_scale, output_path)


def import_splat_file(
    path: str,
    output_name: str = "splat_import",
    max_splats: int = 200000,
    pos_scale: float = 1.0,
) -> dict[str, Any]:
    """Full pipeline: read SPZ/PLY → parse → write compact binary → return path.

    Returns dict with:
      success: bool
      count: int (number of splats)
      binary_path: str (path to compact binary for GDScript)
      ply_path: str (path to decompressed PLY, .ply inputs only)
    """
    path = str(Path(path).resolve())
    is_spz = path.lower().endswith(".spz")

    if is_spz:
        # CORRECTION (2026-07-30): previously did gzip.open() + fed raw bytes
        # to the PLY parser — wrong for real Niantic SPZ files (own packed
        # binary format, not gzip(PLY)), and outright fails on v4 files
        # (NGSP header, not a gzip stream at all). Now uses the real library.
        parsed = _load_gaussian_cloud_via_spz_lib(path)
        if not parsed.get("success"):
            return parsed
        if max_splats and parsed["count"] > max_splats:
            parsed["positions"] = parsed["positions"][:max_splats]
            parsed["colors"] = parsed["colors"][:max_splats]
            parsed["scales_3d"] = parsed["scales_3d"][:max_splats]
            parsed["count"] = max_splats
        if pos_scale != 1.0:
            parsed["positions"] = [(x * pos_scale, y * pos_scale, z * pos_scale) for x, y, z in parsed["positions"]]
            parsed["scales_3d"] = [(sx * pos_scale, sy * pos_scale, sz * pos_scale) for sx, sy, sz in parsed["scales_3d"]]
        ply_path = None
    else:
        if not os.path.isfile(path):
            return {"success": False, "error": f"File not found: {path}"}
        parsed = parse_splat_ply(path, max_splats=max_splats, pos_scale=pos_scale)
        if not parsed.get("success"):
            return parsed
        ply_path = path

    positions = parsed["positions"]
    colors = parsed["colors"]
    scales_3d = parsed.get("scales_3d")

    # Write compact binary
    binary_path = str(Path(tempfile.gettempdir()) / f"{output_name}.splatbin")
    write_compact_binary(positions, colors, scales_3d, binary_path)

    return {
        "success": True,
        "count": parsed["count"],
        "binary_path": binary_path,
        "ply_path": ply_path,
        "is_spz": is_spz,
        "message": f"Imported {parsed['count']} splats",
    }
