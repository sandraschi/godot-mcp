"""Splat (3D Gaussian) parser — SPZ decompression, PLY parsing, binary conversion for Godot.

The 3D Gaussian Splatting PLY format stores per-vertex:
  - x, y, z (float32): position
  - f_dc_0, f_dc_1, f_dc_2 (float32): SH DC coefficients (0.5 + SH_C0 * val gives linear RGB)
  - opacity (float32): alpha
  - scale_0..2 (float32): covariance scaling
  - rot_0..3 (float32): covariance rotation (quaternion)
"""
import gzip
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
                    scales_3d.append((
                        max(0.001, math.exp(sx)) * pos_scale,
                        max(0.001, math.exp(sy)) * pos_scale,
                        max(0.001, math.exp(sz)) * pos_scale,
                    ))
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
      ply_path: str (path to decompressed PLY)
    """
    path = str(Path(path).resolve())
    ply_path = path
    is_spz = path.lower().endswith(".spz")

    # Decompress SPZ → PLY if needed
    if is_spz:
        ply_path = str(Path(tempfile.gettempdir()) / f"{output_name}.ply")
        logger.info("Decompressing SPZ: %s → %s", path, ply_path)
        try:
            with gzip.open(path, "rb") as f_in:
                with open(ply_path, "wb") as f_out:
                    import shutil
                    shutil.copyfileobj(f_in, f_out)
        except Exception as e:
            return {"success": False, "error": f"SPZ decompression failed: {e}"}

    if not os.path.isfile(ply_path):
        return {"success": False, "error": f"File not found: {ply_path}"}

    # Parse PLY
    parsed = parse_splat_ply(ply_path, max_splats=max_splats, pos_scale=pos_scale)
    if not parsed.get("success"):
        return parsed

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
