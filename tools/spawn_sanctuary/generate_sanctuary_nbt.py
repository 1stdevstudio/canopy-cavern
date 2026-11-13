#!/usr/bin/env python3
"""Generates Canopy Sanctuary modular NBT structures and manifest.json for Minecraft Java 26.3."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import math
import os
import struct
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

DATA_VERSION = 5023
REPO_ROOT = Path(__file__).resolve().parents[2]
STRUCT_OUT_DIR = REPO_ROOT / "src/main/resources/data/canopycavern/structure/server_spawn"
MANIFEST_OUT_PATH = REPO_ROOT / "src/main/resources/data/canopycavern/server_spawn/manifest.json"
SERVER_JAR_CANDIDATE = Path("/Users/yogi/Downloads/febricserver/versions/26.3/server-26.3.jar")


# --- Minimal Binary NBT Encoder (Big-Endian Java DataOutput format) ---

TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11
TAG_LONG_ARRAY = 12


@dataclass(frozen=True)
class NbtVal:
    tag: int
    value: object


def nbt_int(v: int) -> NbtVal:
    return NbtVal(TAG_INT, int(v))


def nbt_byte(v: int) -> NbtVal:
    return NbtVal(TAG_BYTE, int(v))


def nbt_str(v: str) -> NbtVal:
    return NbtVal(TAG_STRING, str(v))


def nbt_list(elem_tag: int, items: list) -> NbtVal:
    return NbtVal(TAG_LIST, (elem_tag, items))


def nbt_compound(fields: Dict[str, object]) -> NbtVal:
    return NbtVal(TAG_COMPOUND, fields)


def _write_str(buf: io.BytesIO, s: str) -> None:
    raw = s.encode("utf-8")
    buf.write(struct.pack(">H", len(raw)))
    buf.write(raw)


def _write_payload(buf: io.BytesIO, tag: int, val: object) -> None:
    if tag == TAG_BYTE:
        buf.write(struct.pack(">b", val))
    elif tag == TAG_SHORT:
        buf.write(struct.pack(">h", val))
    elif tag == TAG_INT:
        buf.write(struct.pack(">i", val))
    elif tag == TAG_LONG:
        buf.write(struct.pack(">q", val))
    elif tag == TAG_FLOAT:
        buf.write(struct.pack(">f", val))
    elif tag == TAG_DOUBLE:
        buf.write(struct.pack(">d", val))
    elif tag == TAG_STRING:
        _write_str(buf, val)
    elif tag == TAG_LIST:
        elem_tag, items = val
        buf.write(struct.pack(">bi", elem_tag if items else 0, len(items)))
        for item in items:
            _write_payload(buf, elem_tag, item.value if isinstance(item, NbtVal) else item)
    elif tag == TAG_COMPOUND:
        for k, v in val.items():
            if isinstance(v, NbtVal):
                t, inner = v.tag, v.value
            elif isinstance(v, str):
                t, inner = TAG_STRING, v
            elif isinstance(v, bool):
                t, inner = TAG_BYTE, 1 if v else 0
            elif isinstance(v, int):
                t, inner = TAG_INT, v
            elif isinstance(v, dict):
                t, inner = TAG_COMPOUND, v
            else:
                raise TypeError(f"Unsupported NBT field {k}: {type(v)}")
            buf.write(struct.pack(">B", t))
            _write_str(buf, k)
            _write_payload(buf, t, inner)
        buf.write(struct.pack(">B", TAG_END))
    else:
        raise ValueError(f"Unsupported tag {tag}")


def encode_structure_nbt(size: Tuple[int, int, int], blocks_dict: Dict[Tuple[int, int, int], Tuple[str, Tuple[Tuple[str, str], ...]]]) -> bytes:
    """Encodes a canonical MC 26.3 StructureTemplate .nbt payload (sorted deterministic palette & block list)."""
    sx, sy, sz = size
    palette_index: Dict[Tuple[str, Tuple[Tuple[str, str], ...]], int] = {}
    palette_entries: List[dict] = []

    def get_state_idx(spec: Tuple[str, Tuple[Tuple[str, str], ...]]) -> int:
        if spec in palette_index:
            return palette_index[spec]
        idx = len(palette_entries)
        palette_index[spec] = idx
        block_id, props = spec
        entry: Dict[str, object] = {"id": nbt_str(block_id)}
        if props:
            entry["properties"] = nbt_compound({k: nbt_str(v) for k, v in props})
        palette_entries.append(entry)
        return idx

    block_entries = []
    for (x, y, z) in sorted(blocks_dict.keys()):
        if not (0 <= x < sx and 0 <= y < sy and 0 <= z < sz):
            raise ValueError(f"Block out of bounds ({x},{y},{z}) for size {size}")
        st = get_state_idx(blocks_dict[(x, y, z)])
        block_entries.append(
            nbt_compound(
                {
                    "pos": nbt_list(TAG_INT, [x, y, z]),
                    "state": nbt_int(st),
                }
            )
        )

    root = {
        "DataVersion": nbt_int(DATA_VERSION),
        "size": nbt_list(TAG_INT, [sx, sy, sz]),
        "palette": nbt_list(TAG_COMPOUND, palette_entries),
        "blocks": nbt_list(TAG_COMPOUND, block_entries),
        "entities": nbt_list(TAG_COMPOUND, []),
    }

    raw = io.BytesIO()
    raw.write(struct.pack(">B", TAG_COMPOUND))
    _write_str(raw, "")
    _write_payload(raw, TAG_COMPOUND, root)
    return gzip.compress(raw.getvalue(), compresslevel=6, mtime=0)


# --- Canvas Helper Operating in Hub-Relative Coordinates ---

BlockSpec = Tuple[str, Tuple[Tuple[str, str], ...]]


def bs(block_id: str, **props: str) -> BlockSpec:
    if not block_id.startswith("minecraft:"):
        block_id = "minecraft:" + block_id
    ordered = tuple(sorted((str(k), str(v)) for k, v in props.items()))
    return (block_id, ordered)


AIR = bs("minecraft:air")


class PieceCanvas:
    """Bounded 3D canvas anchored in hub-relative coordinates [x0..x1, y0..y1, z0..z1] inclusive."""

    def __init__(
        self,
        piece_id: str,
        x0: int,
        y0: int,
        z0: int,
        x1: int,
        y1: int,
        z1: int,
        role: str,
        excavate_below: bool = False,
        foundation_skirt: int = 8,
        fill_air: bool = True,
    ):
        self.piece_id = piece_id
        self.x0, self.y0, self.z0 = x0, y0, z0
        self.x1, self.y1, self.z1 = x1, y1, z1
        self.sx = x1 - x0 + 1
        self.sy = y1 - y0 + 1
        self.sz = z1 - z0 + 1
        if max(self.sx, self.sy, self.sz) > 48:
            raise ValueError(f"Piece {piece_id} exceeds 48 max axis: {(self.sx, self.sy, self.sz)}")
        self.role = role
        self.excavate_below = excavate_below
        self.foundation_skirt = foundation_skirt
        self.fill_air = fill_air
        self.voxels: Dict[Tuple[int, int, int], BlockSpec] = {}
        self.signs: List[dict] = []
        self.lecterns: List[dict] = []
        self.connections: List[dict] = []

    def contains(self, hx: int, hy: int, hz: int) -> bool:
        return self.x0 <= hx <= self.x1 and self.y0 <= hy <= self.y1 and self.z0 <= hz <= self.z1

    def set(self, hx: int, hy: int, hz: int, spec: BlockSpec) -> None:
        if not self.contains(hx, hy, hz):
            raise ValueError(
                f"[{self.piece_id}] Out of bounds ({hx},{hy},{hz}) in "
                f"[{self.x0}..{self.x1}, {self.y0}..{self.y1}, {self.z0}..{self.z1}]"
            )
        self.voxels[(hx, hy, hz)] = spec

    def get(self, hx: int, hy: int, hz: int) -> BlockSpec:
        return self.voxels.get((hx, hy, hz), AIR)

    def fill(self, ax: int, ay: int, az: int, bx: int, by: int, bz: int, spec: BlockSpec) -> None:
        for x in range(min(ax, bx), max(ax, bx) + 1):
            for y in range(min(ay, by), max(ay, by) + 1):
                for z in range(min(az, bz), max(az, bz) + 1):
                    self.set(x, y, z, spec)

    def fill_if_air(self, ax: int, ay: int, az: int, bx: int, by: int, bz: int, spec: BlockSpec) -> None:
        for x in range(min(ax, bx), max(ax, bx) + 1):
            for y in range(min(ay, by), max(ay, by) + 1):
                for z in range(min(az, bz), max(az, bz) + 1):
                    if self.get(x, y, z) == AIR:
                        self.set(x, y, z, spec)

    def add_sign(self, hx: int, hy: int, hz: int, wall_dir: Optional[str], rot16: int, key_prefix: str, wood: str = "oak", glow: bool = True) -> None:
        if wall_dir is not None:
            self.set(hx, hy, hz, bs(f"minecraft:{wood}_wall_sign", facing=wall_dir, waterlogged="false"))
        else:
            self.set(hx, hy, hz, bs(f"minecraft:{wood}_sign", rotation=str(rot16), waterlogged="false"))
        self.signs.append(
            {
                "offset": [hx, hy, hz],
                "glowing": glow,
                "lines": [
                    f"sign.canopycavern.{key_prefix}.1",
                    f"sign.canopycavern.{key_prefix}.2",
                    f"sign.canopycavern.{key_prefix}.3",
                    f"sign.canopycavern.{key_prefix}.4",
                ],
            }
        )

    def add_lectern(self, hx: int, hy: int, hz: int, facing: str, book_key: str) -> None:
        self.set(hx, hy, hz, bs("minecraft:lectern", facing=facing, has_book="true", powered="false"))
        self.lecterns.append({"offset": [hx, hy, hz], "bookKey": book_key})

    def add_connection(self, name: str, hx: int, hy: int, hz: int, direction: str) -> None:
        self.connections.append({"name": name, "offset": [hx, hy, hz], "direction": direction})

    def add_tree(self, cx: int, cy: int, cz: int, height: int = 6, flowering: bool = False, seed: int = 1) -> None:
        """Places a small organic azalea/dark-oak sanctuary tree inside canvas bounds."""
        for dy in range(height):
            if self.contains(cx, cy + dy, cz):
                self.set(cx, cy + dy, cz, bs("minecraft:dark_oak_log", axis="y"))
        top = cy + height
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                for dy in range(-2, 3):
                    d2 = dx * dx + dz * dz + (dy * dy * 1.8)
                    if d2 <= 8.2:
                        px, py, pz = cx + dx, top + dy, cz + dz
                        if self.contains(px, py, pz) and self.get(px, py, pz) == AIR:
                            h = (px * 73856093 ^ py * 19349663 ^ pz * 83492791 ^ seed) & 0xFF
                            if flowering and h % 4 == 0:
                                leaf = bs("minecraft:flowering_azalea_leaves", distance="1", persistent="true", waterlogged="false")
                            elif h % 3 == 0:
                                leaf = bs("minecraft:azalea_leaves", distance="1", persistent="true", waterlogged="false")
                            else:
                                leaf = bs("minecraft:dark_oak_leaves", distance="1", persistent="true", waterlogged="false")
                            self.set(px, py, pz, leaf)
        if self.contains(cx, top - 1, cz):
            self.set(cx, top - 1, cz, bs("minecraft:dark_oak_log", axis="y"))
        # Hanging glow lantern or spore accent if space exists under crown
        if self.contains(cx + 1, top - 2, cz) and self.get(cx + 1, top - 2, cz) == AIR and self.get(cx + 1, top - 1, cz) != AIR:
            self.set(cx + 1, top - 2, cz, bs("minecraft:lantern", hanging="true", waterlogged="false"))

    def to_local_blocks(self) -> Dict[Tuple[int, int, int], BlockSpec]:
        out: Dict[Tuple[int, int, int], BlockSpec] = {}
        if self.fill_air:
            for x in range(self.x0, self.x1 + 1):
                for y in range(self.y0, self.y1 + 1):
                    for z in range(self.z0, self.z1 + 1):
                        out[(x - self.x0, y - self.y0, z - self.z0)] = self.voxels.get((x, y, z), AIR)
        else:
            for (x, y, z), spec in self.voxels.items():
                out[(x - self.x0, y - self.y0, z - self.z0)] = spec
        return out


# --- Architectural Material Palettes ---

STONE_FOUNDATION = (
    bs("minecraft:deepslate_tiles"),
    bs("minecraft:tuff_bricks"),
    bs("minecraft:stone_bricks"),
)


def pick_weathered_stone(x: int, y: int, z: int) -> BlockSpec:
    h = (x * 374761393 + y * 668265263 + z * 2147483647) & 0xFFFF
    m = h % 12
    if m in (0, 1, 2):
        return bs("minecraft:mossy_stone_bricks")
    if m == 3:
        return bs("minecraft:cracked_stone_bricks")
    if m in (4, 5):
        return bs("minecraft:tuff_bricks")
    if m == 6:
        return bs("minecraft:polished_andesite")
    return bs("minecraft:stone_bricks")


def pick_road_stone(x: int, z: int) -> BlockSpec:
    h = (x * 911382323 ^ z * 972663749) & 0xFF
    if h % 9 == 0:
        return bs("minecraft:mossy_stone_bricks")
    if h % 7 == 0:
        return bs("minecraft:polished_andesite")
    if h % 11 == 0:
        return bs("minecraft:tuff_bricks")
    return bs("minecraft:stone_bricks")


def lay_road_column(c: PieceCanvas, x: int, z: int, y_top: int = 0) -> None:
    """Lays solid foundation down to y0 with surface stonework."""
    for y in range(c.y0, y_top):
        c.set(x, y, z, bs("minecraft:tuff_bricks") if y == y_top - 1 else bs("minecraft:deepslate_tiles"))
    c.set(x, y_top, z, pick_road_stone(x, z))


def lantern_post(c: PieceCanvas, x: int, y_base: int, z: int, height: int = 4, copper: bool = False) -> None:
    """Places a grounded, multi-layered stone + dark oak lantern post."""
    c.set(x, y_base, z, bs("minecraft:chiseled_tuff_bricks"))
    for dy in range(1, height):
        c.set(x, y_base + dy, z, bs("minecraft:tuff_brick_wall", east="none", north="none", south="none", west="none", up="true", waterlogged="false") if dy == 1 else bs("minecraft:dark_oak_fence", east="false", north="false", south="false", west="false", waterlogged="false"))
    c.set(x, y_base + height, z, bs("minecraft:dark_oak_slab", type="bottom", waterlogged="false"))
    lblock = "minecraft:copper_lantern" if copper else "minecraft:lantern"
    c.set(x, y_base + height + 1, z, bs(lblock, hanging="false", waterlogged="false"))


# --- Piece Builders ---

def build_plaza_core() -> PieceCanvas:
    # X: -15..15 (31), Y: -4..7 (12), Z: -15..15 (31)
    c = PieceCanvas("plaza_core", -15, -4, -15, 15, 7, 15, "arrival_plaza", excavate_below=False, foundation_skirt=8)

    # 1. Subsurface foundation & patterned plaza stonework (Y=-4..0)
    for x in range(-15, 16):
        for z in range(-15, 16):
            r = math.hypot(x, z)
            for y in range(-4, 0):
                c.set(x, y, z, bs("minecraft:deepslate_tiles") if y < -1 else bs("minecraft:tuff_bricks"))

            # 13x13 Safe Arrival Pad (-6..6, -6..6): strict full solid blocks, clean radial pattern!
            if -6 <= x <= 6 and -6 <= z <= 6:
                ax, az = abs(x), abs(z)
                if ax == 6 or az == 6:
                    c.set(x, 0, z, bs("minecraft:chiseled_stone_bricks") if (ax + az) % 2 == 0 else bs("minecraft:tuff_bricks"))
                elif (ax == 0 and az <= 4) or (az == 0 and ax <= 4) or (ax == az and ax <= 3):
                    c.set(x, 0, z, bs("minecraft:polished_andesite"))
                elif ax + az <= 2:
                    c.set(x, 0, z, bs("minecraft:chiseled_tuff_bricks"))
                else:
                    c.set(x, 0, z, bs("minecraft:stone_bricks") if (ax + az) % 2 == 0 else bs("minecraft:polished_andesite"))
            elif abs(x) <= 3 or abs(z) <= 3:
                # 7-wide main cardinal avenues
                edge = (abs(x) == 3 and abs(z) > 6) or (abs(z) == 3 and abs(x) > 6)
                c.set(x, 0, z, bs("minecraft:chiseled_tuff_bricks") if edge else (bs("minecraft:polished_andesite") if abs(x) <= 1 or abs(z) <= 1 else pick_road_stone(x, z)))
            elif r <= 15.2:
                # Ring walkway and planter quarters
                if r <= 10.5 and ((abs(x) == 7 and abs(z) == 7) or (abs(x) == 8 and abs(z) == 8)):
                    # Concealed glowing copper grates around the arrival pad perimeter (outside 13x13!)
                    c.set(x, -1, z, bs("minecraft:sea_lantern"))
                    c.set(x, 0, z, bs("minecraft:waxed_copper_grate", waterlogged="false"))
                else:
                    c.set(x, 0, z, pick_weathered_stone(x, 0, z))
            else:
                c.set(x, 0, z, bs("minecraft:moss_block") if (abs(x) + abs(z)) % 3 == 0 else bs("minecraft:mossy_cobblestone"))

    # Concealed cardinal grate lights right at r=7 along each axis (outside 13x13, on avenue border +/-3)
    for sx, sz in [(-3, -8), (3, -8), (-3, 8), (3, 8), (-8, -3), (-8, 3), (8, -3), (8, 3), (0, -9), (0, 9), (-9, 0), (9, 0)]:
        c.set(sx, -1, sz, bs("minecraft:sea_lantern"))
        c.set(sx, 0, sz, bs("minecraft:waxed_copper_grate", waterlogged="false"))

    # 2. North Arrival Welcome Gateway Pedestals & Wayfinding Signs (~8 blocks ahead facing South toward pad)
    for sx in (-4, 4):
        c.set(sx, 1, -8, bs("minecraft:chiseled_tuff_bricks"))
        c.set(sx, 2, -8, bs("minecraft:polished_tuff"))
        c.set(sx, 3, -8, bs("minecraft:tuff_brick_slab", type="bottom", waterlogged="false"))
        c.set(sx, 4, -8, bs("minecraft:lantern", hanging="false", waterlogged="false"))
    c.add_sign(-4, 2, -7, "south", 0, "welcome", wood="dark_oak", glow=True)
    c.add_sign(4, 2, -7, "south", 0, "choices", wood="dark_oak", glow=True)
    c.add_lectern(-5, 1, -7, "east", "canopy_sanctuary_welcome")

    # Quarter directional plinths inside plaza ring
    lantern_post(c, -8, 1, -8, height=3, copper=False)
    lantern_post(c, 8, 1, -8, height=3, copper=True)
    lantern_post(c, -8, 1, 8, height=3, copper=False)
    for bx, bz in [(9, -7), (-9, 7), (-4, 9)]:
        c.set(bx, 1, bz, bs("minecraft:chiseled_tuff_bricks"))
        c.set(bx, 2, bz, bs("minecraft:polished_tuff"))
        c.set(bx, 3, bz, bs("minecraft:tuff_brick_slab", type="bottom", waterlogged="false"))
    c.add_sign(8, 2, -7, "west", 0, "dir_east", wood="spruce", glow=True)
    c.add_sign(-8, 2, 7, "east", 0, "dir_west", wood="spruce", glow=True)
    c.add_sign(-4, 2, 8, "north", 0, "dir_south", wood="spruce", glow=True)

    # 3. NW & SW Botanical Planters (framed by low mossy brick curbs, well away from 13x13 pad and 7-wide roads)
    for cx, cz in [(-11, -11), (-11, 11), (11, -11)]:
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                px, pz = cx + dx, cz + dz
                if c.contains(px, 0, pz):
                    if abs(dx) == 2 or abs(dz) == 2:
                        c.set(px, 0, pz, bs("minecraft:tuff_bricks"))
                        if abs(dx) == 2 and abs(dz) == 2:
                            c.set(px, 1, pz, bs("minecraft:chiseled_tuff_bricks"))
                            c.set(px, 2, pz, bs("minecraft:waxed_copper_bulb", lit="true", powered="false"))
                            c.set(px, 3, pz, bs("minecraft:tuff_brick_slab", type="bottom", waterlogged="false"))
                    else:
                        c.set(px, 0, pz, bs("minecraft:moss_block"))
                        if dx == 0 and dz == 0:
                            c.set(px, 1, pz, bs("minecraft:flowering_azalea"))
                        elif (abs(dx) + abs(dz)) % 2 == 1:
                            c.set(px, 1, pz, bs("minecraft:moss_carpet"))
                        else:
                            c.set(px, 1, pz, bs("minecraft:azalea"))

    # 4. SE Plaza: Giant Heartroot Tree Root Pedestal & Luminous Crystal Hollow (centered at X=11, Z=11, Y=0..7)
    hx_c, hz_c = 11, 11
    for x in range(6, 16):
        for z in range(6, 16):
            if x == 6 and z == 6:
                continue  # keep arrival pad (-6..6,-6..6) strictly untouched!
            dist = math.hypot(x - hx_c, z - hz_c)
            if dist <= 5.2:
                c.set(x, 0, z, bs("minecraft:moss_block") if dist > 2.6 else bs("minecraft:amethyst_block"))
                if 2.2 <= dist <= 4.3:
                    # Leave arch openings facing Plaza West (-X) and North (-Z) so the crystal heart is visible!
                    in_view_window = (abs(x - hx_c) <= 1 and z < hz_c) or (abs(z - hz_c) <= 1 and x < hx_c)
                    if in_view_window:
                        for y in range(1, 4):
                            if y == 1:
                                c.set(x, y, z, bs("minecraft:tinted_glass"))
                            elif y == 2:
                                c.set(x, y, z, bs("minecraft:tinted_glass"))
                        c.set(x, 4, z, bs("minecraft:dark_oak_wood", axis="y"))
                        c.set(x, 5, z, bs("minecraft:dark_oak_wood", axis="y"))
                        c.set(x, 6, z, bs("minecraft:stripped_dark_oak_wood", axis="y"))
                        c.set(x, 7, z, bs("minecraft:dark_oak_wood", axis="y"))
                    else:
                        h_lim = int(round(7 - (dist - 1.5) * 1.1))
                        for y in range(1, max(2, min(8, h_lim + 1))):
                            blk = bs("minecraft:mangrove_roots", waterlogged="false") if y == 1 and dist > 3.6 else bs("minecraft:dark_oak_wood", axis="y")
                            c.set(x, y, z, blk)
                            if y == 2 and (x + z) % 3 == 0:
                                c.set(x, y, z, bs("minecraft:stripped_dark_oak_wood", axis="y"))
                elif dist < 2.2:
                    # Luminous crystal core column surrounded by amethyst & calcite
                    c.set(x, 1, z, bs("minecraft:sea_lantern") if dist < 1.1 else bs("minecraft:calcite"))
                    for y in range(2, 8):
                        if x == hx_c and z == hz_c:
                            c.set(x, y, z, bs("minecraft:sea_lantern") if y % 2 == 0 else bs("minecraft:amethyst_block"))
                        elif y <= 4 and dist < 1.6:
                            c.set(x, y, z, bs("minecraft:amethyst_block"))
                        elif y >= 5:
                            c.set(x, y, z, bs("minecraft:dark_oak_wood", axis="y"))
                elif dist <= 5.2 and (x + z) % 2 == 0:
                    c.set(x, 1, z, bs("minecraft:moss_carpet"))

    # Ground root tendrils reaching outward around (11,11) within plaza_core (always >=7 from 0,0)
    for rx, rz in [(7, 11), (11, 7), (8, 13), (13, 8), (14, 14), (15, 11), (11, 15)]:
        c.set(rx, 1, rz, bs("minecraft:dark_oak_wood", axis="x" if abs(rx - 11) > abs(rz - 11) else "z"))
        c.set(rx, 2, rz, bs("minecraft:moss_carpet"))

    c.add_connection("north", 0, 0, -15, "north")
    c.add_connection("south", 0, 0, 15, "south")
    c.add_connection("east", 15, 0, 0, "east")
    c.add_connection("west", -15, 0, 0, "west")
    c.add_connection("heartroot_collar", 11, 7, 11, "up")
    return c


def build_ring_cardinal(piece_id: str, x0: int, z0: int, x1: int, z1: int, axis_side: str) -> PieceCanvas:
    """Builds plaza_ring_north or plaza_ring_south (31 x 12 x 9) completing the 49x49 plaza terrace."""
    c = PieceCanvas(piece_id, x0, -4, z0, x1, 7, z1, "arrival_plaza", excavate_below=False, foundation_skirt=8)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            r = math.hypot(x, z)
            if abs(x) <= 3:
                lay_road_column(c, x, z, 0)
                if abs(x) == 3 and abs(z) in (19, 23):
                    c.set(x, 0, z, bs("minecraft:waxed_copper_grate", waterlogged="false"))
                    c.set(x, -1, z, bs("minecraft:sea_lantern"))
            elif r <= 23.8:
                lay_road_column(c, x, z, 0)
                if r >= 22.0 and (abs(x) > 4):
                    c.set(x, 1, z, bs("minecraft:tuff_brick_wall", east="none", north="none", south="none", west="none", up="true", waterlogged="false"))
                elif 17.0 <= r <= 21.0:
                    # Circumferential 5-wide terrace stone path
                    c.set(x, 0, z, bs("minecraft:polished_andesite") if abs(r - 19.0) <= 1.1 else pick_road_stone(x, z))
            else:
                for y in range(-4, 0):
                    c.set(x, y, z, bs("minecraft:stone"))
                c.set(x, 0, z, bs("minecraft:moss_block"))
                if (x + z) % 4 == 0:
                    c.set(x, 1, z, bs("minecraft:flowering_azalea" if (x % 2 == 0) else "minecraft:azalea"))

    # Portal/bridge flanking lantern pylons framing the 7-wide central avenue
    pz = -18 if axis_side == "north" else 18
    for px in (-4, 4):
        c.set(px, 1, pz, bs("minecraft:chiseled_tuff_bricks"))
        c.set(px, 2, pz, bs("minecraft:tuff_bricks"))
        c.set(px, 3, pz, bs("minecraft:waxed_copper_bulb", lit="true", powered="false"))
        c.set(px, 4, pz, bs("minecraft:tuff_brick_slab", type="bottom", waterlogged="false"))
        c.set(px, 5, pz, bs("minecraft:lantern", hanging="false", waterlogged="false"))

    # Add arched pergola accents framing the outer ring on each side
    for px in (-12, 12):
        oz = -20 if axis_side == "north" else 20
        c.set(px, 1, oz, bs("minecraft:stone_bricks"))
        c.set(px, 2, oz, bs("minecraft:dark_oak_log", axis="y"))
        c.set(px, 3, oz, bs("minecraft:dark_oak_log", axis="y"))
        c.set(px, 4, oz, bs("minecraft:dark_oak_slab", type="bottom", waterlogged="false"))
        lantern_post(c, px, 1, oz + (2 if axis_side == "north" else -2), height=3, copper=True)

    if axis_side == "north":
        c.add_connection("to_gate", 0, 0, -24, "north")
    else:
        c.add_connection("to_pavilion", 0, 0, 24, "south")
    return c


def build_ring_side(piece_id: str, x0: int, z0: int, x1: int, z1: int, side: str) -> PieceCanvas:
    """Builds plaza_ring_west and plaza_ring_east (9 x 12 x 40) from Z=-24..15."""
    c = PieceCanvas(piece_id, x0, -4, z0, x1, 7, z1, "arrival_plaza", excavate_below=False, foundation_skirt=8)
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            r = math.hypot(x, z)
            if abs(z) <= 3:
                lay_road_column(c, x, z, 0)
                if abs(z) == 3 and abs(x) in (19, 23):
                    c.set(x, -1, z, bs("minecraft:sea_lantern"))
                    c.set(x, 0, z, bs("minecraft:waxed_copper_grate", waterlogged="false"))
            elif r <= 23.8:
                lay_road_column(c, x, z, 0)
                if r >= 22.0 and abs(z) > 4:
                    c.set(x, 1, z, bs("minecraft:tuff_brick_wall", east="none", north="none", south="none", west="none", up="true", waterlogged="false"))
                elif 17.0 <= r <= 21.0:
                    c.set(x, 0, z, bs("minecraft:polished_andesite") if abs(r - 19.0) <= 1.1 else pick_road_stone(x, z))
            else:
                for y in range(-4, 0):
                    c.set(x, y, z, bs("minecraft:stone"))
                c.set(x, 0, z, bs("minecraft:moss_block"))
                if (x + z) % 5 == 0 and abs(z) >= 8:
                    c.set(x, 1, z, bs("minecraft:azalea"))

    px = -18 if side == "west" else 18
    for pz in (-4, 4):
        c.set(px, 1, pz, bs("minecraft:chiseled_tuff_bricks"))
        c.set(px, 2, pz, bs("minecraft:tuff_bricks"))
        c.set(px, 3, pz, bs("minecraft:waxed_copper_bulb", lit="true", powered="false"))
        c.set(px, 4, pz, bs("minecraft:tuff_brick_slab", type="bottom", waterlogged="false"))
        c.set(px, 5, pz, bs("minecraft:lantern", hanging="false", waterlogged="false"))

    # Shaded corner terrace bench & pergola kiosk around Z=-18 (NW & NE)
    bx = -20 if side == "west" else 20
    c.fill(bx - 1, 1, -19, bx + 1, 4, -17, bs("minecraft:air"))
    for cx in (bx - 1, bx + 1):
        for cz in (-19, -17):
            c.set(cx, 1, cz, bs("minecraft:tuff_bricks"))
            c.set(cx, 2, cz, bs("minecraft:dark_oak_fence", waterlogged="false"))
            c.set(cx, 3, cz, bs("minecraft:dark_oak_fence", waterlogged="false"))
    c.fill(bx - 1, 4, -19, bx + 1, 4, -17, bs("minecraft:waxed_oxidized_cut_copper_slab", type="bottom", waterlogged="false"))
    c.set(bx, 3, -18, bs("minecraft:lantern", hanging="true", waterlogged="false"))
    c.add_connection(f"to_{side}", x0 if side == "west" else x1, 0, 0, side)
    return c


def build_ring_sw_corner() -> PieceCanvas:
    c = PieceCanvas("plaza_ring_sw", -24, -4, 16, -16, 7, 24, "arrival_plaza", excavate_below=False, foundation_skirt=8)
    for x in range(-24, -15):
        for z in range(16, 25):
            r = math.hypot(x, z)
            if r <= 23.8:
                lay_road_column(c, x, z, 0)
                if r >= 22.0:
                    c.set(x, 1, z, bs("minecraft:tuff_brick_wall", up="true", waterlogged="false"))
            else:
                for y in range(-4, 0):
                    c.set(x, y, z, bs("minecraft:stone"))
                c.set(x, 0, z, bs("minecraft:moss_block"))
    lantern_post(c, -19, 1, 19, height=3, copper=False)
    c.set(-18, 1, 18, bs("minecraft:dark_oak_stairs", facing="north", half="bottom", shape="straight", waterlogged="false"))
    c.set(-20, 1, 18, bs("minecraft:dark_oak_stairs", facing="east", half="bottom", shape="straight", waterlogged="false"))
    return c


def build_heartroot_lower_se() -> PieceCanvas:
    c = PieceCanvas("heartroot_lower_se", 16, -4, 16, 24, 7, 24, "landmark", excavate_below=False, foundation_skirt=8)
    for x in range(16, 25):
        for z in range(16, 25):
            r = math.hypot(x, z)
            for y in range(-4, 0):
                c.set(x, y, z, bs("minecraft:deepslate_tiles") if y < -1 else bs("minecraft:tuff_bricks"))
            if r <= 23.8:
                c.set(x, 0, z, bs("minecraft:moss_block") if (x + z) % 2 == 0 else bs("minecraft:mossy_stone_bricks"))
                if r >= 22.2:
                    c.set(x, 1, z, bs("minecraft:tuff_brick_wall", up="true", waterlogged="false"))
            else:
                c.set(x, 0, z, bs("minecraft:moss_block"))
    # Sweeping outer root tendrils anchoring into SE corner
    for (rx, ry, rz) in [(16, 1, 16), (17, 1, 17), (18, 1, 18), (19, 1, 17), (17, 1, 19), (16, 2, 16), (17, 2, 17), (16, 3, 16)]:
        c.set(rx, ry, rz, bs("minecraft:dark_oak_wood", axis="y"))
    c.set(18, 1, 16, bs("minecraft:mangrove_roots", waterlogged="false"))
    c.set(16, 1, 18, bs("minecraft:mangrove_roots", waterlogged="false"))
    lantern_post(c, 20, 1, 20, height=3, copper=True)
    return c


def build_heartroot_trunk() -> PieceCanvas:
    # X: 3..21 (19), Y: 8..18 (11), Z: 3..21 (19) -> trunk centered on (11, y, 11)
    c = PieceCanvas("heartroot_trunk", 3, 8, 3, 21, 18, 21, "landmark", excavate_below=False, foundation_skirt=0)
    cx, cz = 11, 11
    for y in range(8, 19):
        t = (y - 8) / 10.0
        shift_x = round(math.sin(t * 2.2) * 1.2)
        shift_z = round(math.cos(t * 1.9) * 1.1)
        radius = 2.6 - 0.8 * t
        for dx in range(-4, 5):
            for dz in range(-4, 5):
                px, pz = cx + shift_x + dx, cz + shift_z + dz
                d = math.hypot(dx, dz)
                if d <= radius:
                    if d < 0.9 and (y % 2 == 0 or y <= 14):
                        c.set(px, y, pz, bs("minecraft:amethyst_block") if y % 3 == 0 else bs("minecraft:sea_lantern"))
                    elif d >= radius - 0.85 and (px + y + pz) % 5 == 0:
                        c.set(px, y, pz, bs("minecraft:stripped_dark_oak_wood", axis="y"))
                    else:
                        c.set(px, y, pz, bs("minecraft:dark_oak_wood", axis="y"))
                elif d <= radius + 0.6 and y in (8, 9) and (dx + dz) % 2 == 0:
                    c.set(px, y, pz, bs("minecraft:moss_block"))

    # Four spreading organic boughs reaching out toward Y=18 edges inside [3..21]
    boughs = [
        [(11, 15, 11), (10, 16, 9), (8, 17, 7), (6, 18, 6)],
        [(12, 15, 12), (14, 16, 14), (16, 17, 17), (18, 18, 19)],
        [(12, 14, 10), (15, 15, 9), (17, 16, 7), (19, 17, 5)],
        [(10, 14, 12), (8, 15, 15), (6, 16, 18), (5, 17, 20)],
    ]
    for pts in boughs:
        for (bx, by, bz) in pts:
            for ox in (0, 1):
                for oz in (0, 1):
                    if c.contains(bx + ox, by, bz + oz):
                        c.set(bx + ox, by, bz + oz, bs("minecraft:dark_oak_wood", axis="x" if abs(bx - 11) > abs(bz - 11) else "z"))
            if c.contains(bx, by - 1, bz) and c.get(bx, by - 1, bz) == AIR and by % 2 == 1:
                c.set(bx, by - 1, bz, bs("minecraft:lantern", hanging="true", waterlogged="false"))
    c.add_connection("base", 11, 8, 11, "down")
    c.add_connection("crown", 11, 18, 11, "up")
    return c


def build_heartroot_canopy() -> PieceCanvas:
    # X: -8..28 (37), Y: 19..30 (12), Z: -8..28 (37) -> reaches Y0+30! Split asymmetrically so (-6..6, -6..6) pad keeps sky!
    c = PieceCanvas("heartroot_canopy", -8, 19, -8, 28, 30, 28, "landmark", excavate_below=False, foundation_skirt=0)
    cx, cz = 11, 11
    # Upper limbs fanning out inside Y=19..24 (avoiding overhanging too far NW over pad (-6..6))
    limbs = [
        (11, 19, 11, 12, 26, 12),
        (11, 19, 11, 22, 25, 14),
        (11, 19, 11, 15, 25, 24),
        (11, 19, 11, 3, 24, 21),
        (11, 19, 11, 20, 24, 2),
        (11, 19, 11, 4, 23, 3),  # shorter NE/central limb stops well away from central pad sky (-2..2)
    ]
    blobs = []
    for x0, y0, z0, x1, y1, z1 in limbs:
        steps = 10
        for i in range(steps + 1):
            t = i / steps
            px = round(x0 + (x1 - x0) * t)
            py = round(y0 + (y1 - y0) * t)
            pz = round(z0 + (z1 - z0) * t)
            if c.contains(px, py, pz):
                c.set(px, py, pz, bs("minecraft:dark_oak_wood", axis="y"))
                if i == steps:
                    blobs.append((px, py + 1, pz, 5.4 if py >= 25 else 4.6))
            if i == steps // 2:
                blobs.append((px, py + 1, pz, 4.2))
    # Crown jewel spires
    blobs.append((12, 27, 12, 6.2))
    blobs.append((15, 26, 16, 5.2))
    blobs.append((17, 25, 9, 4.8))

    for (bx, by, bz, rad) in blobs:
        ir = int(math.ceil(rad))
        for dx in range(-ir, ir + 1):
            for dy in range(-2, 4):
                for dz in range(-ir, ir + 1):
                    px, py, pz = bx + dx, by + dy, bz + dz
                    if not c.contains(px, py, pz):
                        continue
                    # Asymmetric sky split gap over the arrival pad (-6..6, -6..6) so spawn enjoys open sky & daylight!
                    if px <= 4 and pz <= 4 and math.hypot(px, pz) < 7.5:
                        continue
                    dist = math.sqrt(dx * dx + (dy * 1.45) ** 2 + dz * dz)
                    if dist <= rad:
                        if c.get(px, py, pz) == AIR:
                            h = (px * 1315423911 ^ py * 2654435761 ^ pz * 19349663) & 0xFF
                            if h % 7 == 0:
                                leaf = bs("minecraft:flowering_azalea_leaves", distance="1", persistent="true", waterlogged="false")
                            elif h % 3 == 0:
                                leaf = bs("minecraft:azalea_leaves", distance="1", persistent="true", waterlogged="false")
                            else:
                                leaf = bs("minecraft:dark_oak_leaves", distance="1", persistent="true", waterlogged="false")
                            c.set(px, py, pz, leaf)
                        # Hang subtle crystal/blossom/lantern accents from underside of solid leaves
                        if dy == -1 and dist <= rad - 1.2 and (px + pz) % 13 == 0 and c.contains(px, py - 1, pz) and c.get(px, py - 1, pz) == AIR:
                            c.set(px, py - 1, pz, bs("minecraft:spore_blossom") if (px % 2 == 0) else bs("minecraft:lantern", hanging="true", waterlogged="false"))

    # Embedded amethyst star crystal heart high in canopy crown (12, 24..25, 12)
    for dy in (24, 25):
        c.set(12, dy, 12, bs("minecraft:sea_lantern") if dy == 24 else bs("minecraft:amethyst_block"))
    return c


def build_north_gate() -> PieceCanvas:
    # X: -15..15 (31), Y: -4..18 (23), Z: -49..-25 (25) -> 31x23x25 Ancient Expedition Gate
    c = PieceCanvas("north_expedition_gate", -15, -4, -49, 15, 18, -25, "gate", excavate_below=False, foundation_skirt=8)
    for x in range(-15, 16):
        for z in range(-49, -24):
            in_road = abs(x) <= 3
            if in_road or (-42 <= z <= -32 and abs(x) <= 13):
                lay_road_column(c, x, z, 0)
            else:
                for y in range(-4, 0):
                    c.set(x, y, z, bs("minecraft:stone"))
                c.set(x, 0, z, bs("minecraft:moss_block") if (abs(x) + abs(z)) % 3 == 0 else bs("minecraft:grass_block", snowy="false"))

    # Dual Monumental Stone & Timber Gatehouse Towers framing X=-11..-6 & X=+6..+11, Z=-41..-33
    for side_sign in (-1, 1):
        tx0 = 6 if side_sign > 0 else -11
        tx1 = 11 if side_sign > 0 else -6
        for x in range(tx0, tx1 + 1):
            for z in range(-41, -32):
                is_wall = x in (tx0, tx1) or z in (-41, -33)
                is_corner = x in (tx0, tx1) and z in (-41, -33)
                for y in range(1, 13):
                    if is_corner:
                        c.set(x, y, z, bs("minecraft:deepslate_bricks") if y <= 4 else bs("minecraft:dark_oak_log", axis="y"))
                    elif is_wall:
                        # Arched lookout apertures on Y=2..3 and Y=8..9
                        window = (y in (3, 4) or y in (8, 9)) and (x in (tx0 + 2, tx0 + 3) or z in (-38, -36))
                        if window and y < 11:
                            c.set(x, y, z, bs("minecraft:air") if (side_sign < 0 and x == -6 and z in (-38, -37, -36) and y <= 3) or (side_sign > 0 and x == 6 and z in (-38, -37, -36) and y <= 3) else bs("minecraft:iron_bars", waterlogged="false"))
                        else:
                            c.set(x, y, z, pick_weathered_stone(x, y, z))
                    else:
                        if y == 6 or y == 11:
                            c.set(x, y, z, bs("minecraft:spruce_planks"))
                        else:
                            c.set(x, y, z, bs("minecraft:air"))
        # Gatehouse ground doorway inward toward the central arch avenue!
        door_x = -6 if side_sign < 0 else 6
        c.fill(door_x, 1, -38, door_x, 3, -36, bs("minecraft:air"))
        # Solid spiral staircase inside each lookout tower from Y=1 to Y=11 (zero gaps!)
        cx_t = tx0 + 2
        cz_t = -37
        for step in range(1, 12):
            c.set(cx_t + (step % 2), step, cz_t - 1 + (step // 3 % 2), bs("minecraft:stone_bricks"))
        # Replace clunky loop with clean guarded interior straight flight stairs along outer back wall inside tower!
        c.fill(tx0 + 1, 1, -40, tx1 - 1, 11, -34, bs("minecraft:air"))
        for y in range(1, 7):
            c.set(tx0 + 1, y, -34 - (y - 1), bs("minecraft:spruce_stairs", facing="north", half="bottom", shape="straight", waterlogged="false"))
            c.set(tx0 + 2, y, -34 - (y - 1), bs("minecraft:spruce_planks"))
            for yy in range(1, y):
                c.set(tx0 + 1, yy, -34 - (y - 1), bs("minecraft:tuff_bricks"))
        c.fill(tx0 + 1, 6, -40, tx1 - 1, 6, -34, bs("minecraft:spruce_planks"))
        c.fill(tx0 + 1, 7, -40, tx0 + 2, 10, -39, bs("minecraft:air"))
        for y in range(7, 12):
            off = y - 7
            c.set(tx1 - 1, y, -40 + off, bs("minecraft:spruce_stairs", facing="south", half="bottom", shape="straight", waterlogged="false"))
            for yy in range(7, y):
                c.set(tx1 - 1, yy, -40 + off, bs("minecraft:tuff_bricks"))
        c.fill(tx0 + 1, 11, -40, tx1 - 1, 11, -34, bs("minecraft:spruce_planks"))
        # Clear hatch above upper flight
        for y in range(7, 12):
            off = min(4, y - 7)
            c.fill(tx1 - 1, 11, -40, tx1 - 1, 11, -35, bs("minecraft:air"))
        c.set(tx0 + 2, 10, -37, bs("minecraft:lantern", hanging="true", waterlogged="false"))
        c.set(tx0 + 2, 5, -37, bs("minecraft:lantern", hanging="true", waterlogged="false"))

        # Pyramidal Oxidized Copper & Dark Oak Stepped Spire Roof (Y=12..18)
        for dy in range(0, 6):
            y = 12 + dy
            inset = dy // 2
            rx0, rx1 = tx0 - 1 + inset, tx1 + 1 - inset
            rz0, rz1 = -42 + inset, -32 - inset
            for x in range(rx0, rx1 + 1):
                for z in range(rz0, rz1 + 1):
                    on_edge = x in (rx0, rx1) or z in (rz0, rz1)
                    if on_edge:
                        c.set(x, y, z, bs("minecraft:waxed_oxidized_cut_copper_slab", type="bottom", waterlogged="false") if dy % 2 == 1 else bs("minecraft:waxed_oxidized_copper"))
                    elif dy < 4:
                        c.set(x, y, z, bs("minecraft:dark_oak_planks"))
        c.set((tx0 + tx1) // 2, 18, -37, bs("minecraft:lantern", hanging="false", waterlogged="false"))
        c.set((tx0 + tx1) // 2, 17, -37, bs("minecraft:waxed_copper_bulb", lit="true", powered="false"))

    # Towering Central Timber & Stone Arch Bridge spanning across X=-5..5 at Y=7..14 (wide open clearance Y=1..7!)
    for z in range(-40, -33):
        c.fill(-5, 9, z, 5, 9, z, bs("minecraft:stone_bricks"))
        c.fill(-5, 10, z, 5, 10, z, bs("minecraft:moss_carpet") if z in (-38, -36) else bs("minecraft:air"))
        if z in (-40, -34):
            c.fill(-5, 10, z, 5, 10, z, bs("minecraft:tuff_brick_wall", up="true", waterlogged="false"))
        # Open arch ribs underneath Y=6..8
        for side_x in (-5, 5):
            c.set(side_x, 7, z, bs("minecraft:dark_oak_stairs", facing="east" if side_x < 0 else "west", half="top", shape="straight", waterlogged="false"))
            c.set(side_x, 8, z, bs("minecraft:tuff_bricks"))
        for side_x in (-4, 4):
            c.set(side_x, 8, z, bs("minecraft:dark_oak_stairs", facing="east" if side_sign < 0 else "west", half="top", shape="straight", waterlogged="false") if side_x < 0 else bs("minecraft:dark_oak_stairs", facing="west", half="top", shape="straight", waterlogged="false"))
    c.set(0, 8, -37, bs("minecraft:lantern", hanging="true", waterlogged="false"))
    # Gabled ridge cupola atop the arch bridge connecting the two towers
    for dy in range(0, 4):
        c.fill(-4 + dy, 11 + dy, -39 + dy // 2, 4 - dy, 11 + dy, -35 - dy // 2, bs("minecraft:waxed_oxidized_cut_copper") if dy < 3 else bs("minecraft:waxed_copper_bulb", lit="true", powered="false"))
    # Connect bridge deck directly into both towers at Y=9 (carve doorways into towers at Y=10..11? Roof floor at 11 -> step!)
    c.set(-5, 10, -37, bs("minecraft:stone_brick_stairs", facing="west", half="bottom", shape="straight", waterlogged="false"))
    c.set(5, 10, -37, bs("minecraft:stone_brick_stairs", facing="east", half="bottom", shape="straight", waterlogged="false"))
    c.fill(-6, 12, -38, -6, 13, -36, bs("minecraft:air"))
    c.fill(6, 12, -38, 6, 13, -36, bs("minecraft:air"))

    # Lanterns & Expedition Wayfinding Signs on inner arch piers
    c.set(-5, 1, -33, bs("minecraft:chiseled_tuff_bricks"))
    c.set(-5, 2, -33, bs("minecraft:polished_tuff"))
    c.set(-5, 3, -33, bs("minecraft:tuff_brick_slab", type="bottom", waterlogged="false"))
    c.add_sign(-5, 2, -32, "south", 0, "north_gate", wood="dark_oak", glow=True)
    c.set(5, 3, -33, bs("minecraft:chiseled_tuff_bricks"))
    lantern_post(c, -13, 1, -28, height=3, copper=False)
    lantern_post(c, 13, 1, -28, height=3, copper=True)
    lantern_post(c, -5, 1, -46, height=3, copper=False)
    lantern_post(c, 5, 1, -46, height=3, copper=True)

    c.add_connection("south_plaza", 0, 0, -25, "south")
    c.add_connection("north_trail", 0, 0, -49, "north")
    return c


def build_north_trail_outpost() -> PieceCanvas:
    # X: -11..11 (23), Y: -4..8 (13), Z: -95..-50 (46)
    c = PieceCanvas("north_trail_outpost", -11, -4, -95, 11, 8, -50, "road_connector", excavate_below=False, foundation_skirt=8)
    for x in range(-11, 12):
        for z in range(-95, -49):
            curve_center = round(math.sin((z + 50) / 14.0) * 2.5) if z <= -58 else 0
            dist = abs(x - curve_center)
            if dist <= 3:
                lay_road_column(c, x, z, 0)
            else:
                for y in range(-4, 0):
                    c.set(x, y, z, bs("minecraft:stone") if y < -1 else bs("minecraft:dirt"))
                c.set(x, 0, z, bs("minecraft:grass_block", snowy="false") if dist >= 5 else bs("minecraft:moss_block"))
                if dist == 4 and abs(z) % 4 == 0:
                    c.set(x, 1, z, bs("minecraft:mossy_cobblestone_slab", type="bottom", waterlogged="false"))

    # Trailside Ranger Waypost at Z=-73.. -69, X=+5..+8
    for px, pz in [(5, -73), (8, -73), (5, -70), (8, -70)]:
        c.set(px, 1, pz, bs("minecraft:stone_bricks"))
        c.set(px, 2, pz, bs("minecraft:dark_oak_fence", waterlogged="false"))
        c.set(px, 3, pz, bs("minecraft:dark_oak_fence", waterlogged="false"))
    c.fill(4, 4, -74, 9, 4, -69, bs("minecraft:spruce_slab", type="bottom", waterlogged="false"))
    c.set(6, 5, -71, bs("minecraft:waxed_oxidized_cut_copper_slab", type="bottom", waterlogged="false"))
    c.set(7, 5, -71, bs("minecraft:waxed_oxidized_cut_copper_slab", type="bottom", waterlogged="false"))
    c.set(6, 3, -71, bs("minecraft:lantern", hanging="true", waterlogged="false"))
    c.set(5, 1, -71, bs("minecraft:chiseled_tuff_bricks"))
    c.add_sign(4, 1, -71, "west", 0, "trail_exit", wood="spruce", glow=True)

    for lz in (-55, -67, -81, -93):
        cx = round(math.sin((lz + 50) / 14.0) * 2.5) if lz <= -58 else 0
        lantern_post(c, cx - 4 if lz % 2 == 0 else cx + 4, 1, lz, height=3, copper=(lz % 4 == 1))

    c.add_tree(-8, 1, -60, height=5, flowering=True, seed=11)
    c.add_tree(8, 1, -86, height=5, flowering=False, seed=12)
    c.add_connection("to_gate", 0, 0, -50, "south")
    c.add_connection("wilds_exit", round(math.sin(-45 / 14.0) * 2.5), 0, -95, "north")
    return c


def build_east_guild_hall() -> PieceCanvas:
    # X: 25..59 (35), Y: -4..18 (23), Z: -13..13 (27) -> Adventurer Guild Hall (35 x 27)
    c = PieceCanvas("east_guild_hall", 25, -4, -13, 59, 18, 13, "guild_hall", excavate_below=False, foundation_skirt=8)
    for x in range(25, 60):
        for z in range(-13, 14):
            for y in range(-4, 0):
                c.set(x, y, z, bs("minecraft:deepslate_tiles") if y < -1 else bs("minecraft:tuff_bricks"))
            if x <= 30 and abs(z) <= 3:
                lay_road_column(c, x, z, 0)
            elif 31 <= x <= 55 and -10 <= z <= 10:
                c.set(x, 0, z, bs("minecraft:polished_andesite") if abs(z) <= 2 or x in (31, 55) else bs("minecraft:spruce_planks"))
            elif x >= 56 and abs(z) <= 3:
                lay_road_column(c, x, z, 0)
            else:
                c.set(x, 0, z, bs("minecraft:moss_block") if (x + z) % 3 == 0 else bs("minecraft:tuff_bricks"))

    # Grand Asymmetrical Multi-Gable Guildhall Envelope: X=31..55, Z=-10..10 (walls Y=1..7, mezzanine loft/gallery Y=7..11, pitched layered roofs Y=8..17)
    for x in range(31, 56):
        for z in range(-10, 11):
            in_main = 31 <= x <= 51 and -9 <= z <= 9
            in_wing = 43 <= x <= 55 and -10 <= z <= 10
            if not (in_main or in_wing):
                continue
            on_perimeter = (
                (x == 31 and -9 <= z <= 9)
                or (x == 55 and -10 <= z <= 10)
                or (z in (-9, 9) and 31 <= x <= 43)
                or (z in (-10, 10) and 43 <= x <= 55)
                or (x == 43 and abs(z) in (9, 10))
            )
            pillar = x in (31, 36, 43, 49, 55) and z in (-9, -10, 9, 10)
            if pillar:
                for y in range(1, 9):
                    c.set(x, y, z, bs("minecraft:tuff_bricks") if y <= 2 else bs("minecraft:stripped_dark_oak_log", axis="y"))
            elif on_perimeter:
                for y in range(1, 8):
                    if y <= 2:
                        c.set(x, y, z, pick_weathered_stone(x, y, z))
                    elif y in (3, 4, 5) and ((abs(z) in (5, 6) and x in (31, 55)) or (x in (34, 39, 46, 52) and abs(z) >= 9)):
                        c.set(x, y, z, bs("minecraft:tinted_glass"))
                    else:
                        c.set(x, y, z, bs("minecraft:spruce_planks") if y % 2 == 0 else bs("minecraft:dark_oak_planks"))
            else:
                c.fill(x, 1, z, x, 7, z, bs("minecraft:air"))

    # Exposed timber ceiling beams & central chandelier lanterns inside (Y=7)
    for bx in (36, 43, 49):
        for z in range(-8, 9):
            c.set(bx, 7, z, bs("minecraft:stripped_dark_oak_log", axis="z"))
    for lx, lz in [(37, 0), (46, 0), (41, -5), (41, 5), (51, -5), (51, 5)]:
        c.set(lx, 6, lz, bs("minecraft:iron_chain", axis="y", waterlogged="false"))
        c.set(lx, 5, lz, bs("minecraft:lantern", hanging="true", waterlogged="false"))

    # Front & Back Entrances (West Plaza Arch X=31, Z=-2..2 & East Trail Arch X=55, Z=-2..2) — wide 5-block doorway arches!
    for ex, face in [(31, "west"), (55, "east")]:
        c.fill(ex, 1, -2, ex, 4, 2, bs("minecraft:air"))
        c.set(ex, 4, -2, bs("minecraft:dark_oak_stairs", facing="south", half="top", shape="straight", waterlogged="false"))
        c.set(ex, 4, 2, bs("minecraft:dark_oak_stairs", facing="north", half="top", shape="straight", waterlogged="false"))
        c.set(ex, 5, -3, bs("minecraft:stripped_dark_oak_log", axis="y"))
        c.set(ex, 5, 3, bs("minecraft:stripped_dark_oak_log", axis="y"))
    lantern_post(c, 28, 1, -4, height=3, copper=True)
    lantern_post(c, 28, 1, 4, height=3, copper=True)

    # Layered Overhanging Roofs (Main West-East pitched roof Y=8..14 + Cross-Gable Dormer Wing Y=8..17!)
    # Main gable running along X=30..52, ridge along Z=0 (Z=-10..10)
    for dy in range(0, 7):
        y = 8 + dy
        z_n, z_s = -10 + dy, 10 - dy
        if z_n > z_s:
            break
        for x in range(30, 53):
            if z_n == z_s:
                c.set(x, y, 0, bs("minecraft:waxed_oxidized_cut_copper_slab", type="bottom", waterlogged="false"))
            else:
                mat_n = bs("minecraft:dark_oak_stairs", facing="south", half="bottom", shape="straight", waterlogged="false") if x in (30, 52) or dy == 0 else bs("minecraft:waxed_oxidized_cut_copper_stairs", facing="south", half="bottom", shape="straight", waterlogged="false")
                mat_s = bs("minecraft:dark_oak_stairs", facing="north", half="bottom", shape="straight", waterlogged="false") if x in (30, 52) or dy == 0 else bs("minecraft:waxed_oxidized_cut_copper_stairs", facing="north", half="bottom", shape="straight", waterlogged="false")
                c.set(x, y, z_n, mat_n)
                c.set(x, y, z_s, mat_s)
                if z_n + 1 <= z_s - 1:
                    c.fill(x, y, z_n + 1, x, y, z_s - 1, bs("minecraft:dark_oak_planks") if x in (31, 51) else bs("minecraft:air"))
                    if x in (31, 51) and dy in (2, 3):
                        c.set(x, y, 0, bs("minecraft:tinted_glass"))

    # East Cross-Wing Taller Belfry Gable running North-South (X=43..56, ridge X=49..50, Z=-11..11)
    for dy in range(0, 8):
        y = 9 + dy
        x_w, x_e = 42 + dy, 56 - dy
        if x_w > x_e:
            break
        for z in range(-11, 12):
            if x_w == x_e:
                c.set(x_w, y, z, bs("minecraft:waxed_copper_bulb", lit="true", powered="false") if abs(z) % 4 == 0 else bs("minecraft:waxed_oxidized_cut_copper_slab", type="bottom", waterlogged="false"))
                c.set(x_w, y + 1, z, bs("minecraft:tuff_brick_slab", type="bottom", waterlogged="false") if abs(z) % 4 == 0 else bs("minecraft:air"))
            else:
                mat_w = bs("minecraft:dark_oak_stairs", facing="east", half="bottom", shape="straight", waterlogged="false") if abs(z) == 11 or dy == 0 else bs("minecraft:waxed_weathered_cut_copper_stairs", facing="east", half="bottom", shape="straight", waterlogged="false")
                mat_e = bs("minecraft:dark_oak_stairs", facing="west", half="bottom", shape="straight", waterlogged="false") if abs(z) == 11 or dy == 0 else bs("minecraft:waxed_weathered_cut_copper_stairs", facing="west", half="bottom", shape="straight", waterlogged="false")
                c.set(x_w, y, z, mat_w)
                c.set(x_e, y, z, mat_e)
                if abs(z) == 10 and x_w + 1 <= x_e - 1:
                    c.fill(x_w + 1, y, z, x_e - 1, y, z, bs("minecraft:spruce_planks"))

    # Interior Exhibits: Canopy Field Guide Reading Gallery (North side Z=-7..-4)
    for x in range(34, 42):
        c.set(x, 1, -8, bs("minecraft:chiseled_bookshelf") if x % 2 == 0 else bs("minecraft:bookshelf"))
        c.set(x, 2, -8, bs("minecraft:bookshelf"))
        c.set(x, 3, -8, bs("minecraft:dark_oak_slab", type="top", waterlogged="false"))
    c.add_lectern(36, 1, -5, "south", "guild_field_guide")
    c.add_lectern(40, 1, -5, "south", "guild_expedition_routes")
    c.add_sign(38, 2, -7, "south", 0, "guild_guide", wood="dark_oak", glow=True)

    # Interior Exhibits: Expedition Route Map Board & Noticeboard (South side Z=+4..+8)
    for x in range(34, 42):
        c.set(x, 1, 8, bs("minecraft:spruce_planks"))
        c.set(x, 2, 8, bs("minecraft:chiseled_tuff_bricks") if x % 3 == 0 else bs("minecraft:spruce_planks"))
        c.set(x, 3, 8, bs("minecraft:dark_oak_slab", type="top", waterlogged="false"))
    c.set(35, 1, 7, bs("minecraft:cartography_table"))
    c.add_sign(38, 2, 7, "north", 0, "guild_map", wood="spruce", glow=True)
    c.add_sign(40, 2, 7, "north", 0, "guild_notice", wood="spruce", glow=True)

    # Central Enclosed Luminous Crystal Archive Pillar (non-hazardous!) + Benches in East Wing (X=48..52)
    for (ax, az) in [(48, -6), (52, -6), (48, 6), (52, 6)]:
        c.set(ax, 1, az, bs("minecraft:tuff_bricks"))
        c.set(ax, 2, az, bs("minecraft:waxed_copper_bulb", lit="true", powered="false"))
        c.set(ax, 3, az, bs("minecraft:tuff_brick_slab", type="bottom", waterlogged="false"))
    c.set(46, 1, -3, bs("minecraft:dark_oak_stairs", facing="north", half="bottom", shape="straight", waterlogged="false"))
    c.set(47, 1, -3, bs("minecraft:dark_oak_stairs", facing="north", half="bottom", shape="straight", waterlogged="false"))
    c.set(46, 1, 3, bs("minecraft:dark_oak_stairs", facing="south", half="bottom", shape="straight", waterlogged="false"))
    c.set(47, 1, 3, bs("minecraft:dark_oak_stairs", facing="south", half="bottom", shape="straight", waterlogged="false"))

    c.add_connection("west_plaza", 25, 0, 0, "west")
    c.add_connection("east_trail", 59, 0, 0, "east")
    return c


def build_west_nature_garden() -> PieceCanvas:
    # X: -59..-25 (35), Y: -4..15 (20), Z: -13..13 (27) -> Ramp-Accessible Conservatory Garden & Shaded Market
    c = PieceCanvas("west_nature_garden", -59, -4, -13, -25, 15, 13, "nature_garden", excavate_below=False, foundation_skirt=8)
    for x in range(-59, -24):
        for z in range(-13, 14):
            for y in range(-4, 0):
                c.set(x, y, z, bs("minecraft:deepslate_tiles") if y < -1 else bs("minecraft:tuff_bricks"))
            # 5-wide wheel/step-free level avenue + wide gentle half-block terrace X=-49..-35
            if abs(z) <= 2 or (x in (-27, -26, -25) and abs(z) <= 3):
                # Continuous level center walkway & shallow stone bridges over Z=±5 reflection pools
                lay_road_column(c, x, z, 0)
            elif -47 <= x <= -35 and 4 <= abs(z) <= 9:
                # 1-block-deep safe crystal reflection basin surrounded by tuff curb (zero drowning depth)
                if -45 <= x <= -37 and 5 <= abs(z) <= 7:
                    c.set(x, -1, z, bs("minecraft:sea_lantern") if (x + z) % 4 == 0 else bs("minecraft:polished_andesite"))
                    c.set(x, 0, z, bs("minecraft:water", level="0"))
                else:
                    c.set(x, 0, z, bs("minecraft:mossy_stone_bricks") if abs(z) == 4 else bs("minecraft:moss_block"))
            elif -56 <= x <= -48 and -9 <= z <= 9:
                # Raised Botanical Gazebo Terrace at Y=+1 reached cleanly via smooth 5-wide slab ramp at X=-48!
                c.set(x, 0, z, bs("minecraft:stone_bricks"))
                c.set(x, 1, z, bs("minecraft:polished_andesite") if abs(z) <= 4 else bs("minecraft:moss_block"))
            else:
                c.set(x, 0, z, bs("minecraft:moss_block") if (x + z) % 2 == 0 else bs("minecraft:grass_block", snowy="false"))

    # Smooth Wheelchair/Jump-Free 0.5-block Step Ramp from Y=0 (X=-47) up to Y=+1 (X=-49) across Z=-2..+2 (5 wide!)
    for z in range(-2, 3):
        c.set(-47, 1, z, bs("minecraft:polished_andesite_slab", type="bottom", waterlogged="false"))
        c.set(-48, 1, z, bs("minecraft:polished_andesite"))
        # Side garden curb slabs
        c.set(-47, 1, -3, bs("minecraft:mossy_stone_brick_wall", up="true", waterlogged="false"))
        c.set(-47, 1, 3, bs("minecraft:mossy_stone_brick_wall", up="true", waterlogged="false"))

    # Crosswise 5-wide Stone Bridges spanning over both reflection pools at X=-42..-38 -> Z=-10..10
    for x in range(-43, -38):
        for z in range(-10, 11):
            if abs(z) >= 3:
                c.set(x, 0, z, bs("minecraft:spruce_planks"))
            if x in (-43, -39) and 5 <= abs(z) <= 8:
                c.set(x, 1, z, bs("minecraft:dark_oak_fence", waterlogged="false"))

    # Covered Shaded Pergola / Botanical Trellis Arches spanning Plaza side (-34..-29) & West Gazebo (-56..-50)
    for px in (-33, -29):
        for pz in (-5, 5):
            for y in range(1, 5):
                c.set(px, y, pz, bs("minecraft:stripped_dark_oak_log", axis="y"))
    for x in range(-34, -28):
        for z in range(-5, 6):
            if x in (-33, -29) or abs(z) in (4, 5):
                c.set(x, 5, z, bs("minecraft:spruce_slab", type="bottom", waterlogged="false"))
            else:
                c.set(x, 5, z, bs("minecraft:flowering_azalea_leaves" if (x + z) % 2 == 0 else "minecraft:azalea_leaves", distance="1", persistent="true", waterlogged="false"))
    c.set(-31, 4, -4, bs("minecraft:lantern", hanging="true", waterlogged="false"))
    c.set(-31, 4, 4, bs("minecraft:lantern", hanging="true", waterlogged="false"))

    # Grand West Botanical Conservatory Gazebo (floor Y=1 at X=-56..-49, Z=-7..7)
    for gx, gz in [(-56, -7), (-50, -7), (-56, 7), (-50, 7), (-56, -3), (-56, 3), (-50, -3), (-50, 3)]:
        c.set(gx, 2, gz, bs("minecraft:tuff_bricks"))
        for y in range(3, 7):
            c.set(gx, y, gz, bs("minecraft:dark_oak_log", axis="y"))
    for dy in range(0, 5):
        y = 7 + dy
        for x in range(-57 + dy, -48 - dy):
            for z in range(-8 + dy, 9 - dy):
                edge = x in (-57 + dy, -49 - dy) or z in (-8 + dy, 8 - dy)
                if edge:
                    c.set(x, y, z, bs("minecraft:waxed_oxidized_cut_copper_slab", type="bottom", waterlogged="false") if dy % 2 == 0 else bs("minecraft:dark_oak_slab", type="bottom", waterlogged="false"))
    c.set(-53, 12, 0, bs("minecraft:waxed_copper_bulb", lit="true", powered="false"))
    c.set(-53, 13, 0, bs("minecraft:lantern", hanging="false", waterlogged="false"))
    c.set(-53, 6, 0, bs("minecraft:spore_blossom"))
    c.set(-53, 2, 0, bs("minecraft:polished_tuff"))
    c.set(-53, 3, 0, bs("minecraft:chiseled_tuff_bricks"))
    c.set(-53, 4, 0, bs("minecraft:flowering_azalea"))
    c.add_sign(-52, 2, 0, "east", 0, "garden_lore", wood="spruce", glow=True)

    # Neutral Shaded Market Benches & Floral Beds (no villager job sites)
    c.add_tree(-31, 1, -10, height=4, flowering=True, seed=21)
    c.add_tree(-31, 1, 10, height=4, flowering=True, seed=22)
    lantern_post(c, -36, 1, -3, height=3, copper=False)
    lantern_post(c, -36, 1, 3, height=3, copper=False)

    # Exit Ramp on West back of Gazebo (-56 down to -58 -> Y=1 down to Y=0 cleanly!)
    for z in range(-2, 3):
        c.set(-57, 1, z, bs("minecraft:polished_andesite_slab", type="bottom", waterlogged="false"))
        c.set(-58, 0, z, bs("minecraft:polished_andesite"))

    c.add_connection("east_plaza", -25, 0, 0, "east")
    c.add_connection("west_trail", -59, 0, 0, "west")
    return c


def build_side_trail(piece_id: str, x0: int, x1: int, side: str) -> PieceCanvas:
    """East or West outer perimeter scenic trail extending to +-95."""
    c = PieceCanvas(piece_id, x0, -4, -20, x1, 12, 20, "road_connector", excavate_below=False, foundation_skirt=8)
    for x in range(x0, x1 + 1):
        for z in range(-20, 21):
            curve_z = round(math.sin((abs(x) - 60) / 11.0) * 3.0)
            if abs(z - curve_z) <= 3:
                lay_road_column(c, x, z, 0)
            else:
                for y in range(-4, 0):
                    c.set(x, y, z, bs("minecraft:stone") if y < -1 else bs("minecraft:dirt"))
                c.set(x, 0, z, bs("minecraft:moss_block") if (x + z) % 3 == 0 else bs("minecraft:grass_block", snowy="false"))
                if abs(z - curve_z) >= 6 and (abs(x) * 31 + abs(z) * 17) % 23 == 0:
                    c.set(x, 1, z, bs("minecraft:mossy_cobblestone"))
                    if (x + z) % 2 == 0:
                        c.set(x, 2, z, bs("minecraft:mossy_cobblestone_slab", type="bottom", waterlogged="false"))

    mid_x = (x0 + x1) // 2
    c.add_tree(mid_x - 6, 1, -11, height=5, flowering=(side == "west"), seed=31 if side == "west" else 41)
    c.add_tree(mid_x + 5, 1, 11, height=5, flowering=(side == "east"), seed=32 if side == "west" else 42)
    for lx in range(x0 + 4, x1 - 3, 10):
        cz = round(math.sin((abs(lx) - 60) / 11.0) * 3.0)
        lantern_post(c, lx, 1, cz + (4 if (lx // 10) % 2 == 0 else -4), height=3, copper=(side == "east"))

    c.add_connection("inner", x1 if side == "west" else x0, 0, 0, "east" if side == "west" else "west")
    edge_x = x0 if side == "west" else x1
    c.add_connection("outer", edge_x, 0, round(math.sin((abs(edge_x) - 60) / 11.0) * 3.0), side)
    return c


def build_south_trading_pavilion() -> PieceCanvas:
    # X: -22..22 (45), Y: -3..17 (21), Z: 25..54 (30) -> Trading / Rest Pavilion + Twin Cavern Descent Stairways
    c = PieceCanvas("south_trading_pavilion", -22, -3, 25, 22, 17, 54, "pavilion", excavate_below=False, foundation_skirt=8)

    # Note carefully: central stairwell descent shafts at X=-11..-9 (West Stair) and X=+9..+11 (East Stair) over Z=36..51 carve down from Y=0 to Y=-3!
    def in_stair_shaft(x: int, z: int) -> bool:
        return (x in (-11, -10, -9) or x in (9, 10, 11)) and (36 <= z <= 48)

    for x in range(-22, 23):
        for z in range(25, 55):
            if in_stair_shaft(x, z):
                # Carve stairwell opening down to hand off cleanly to cavern_descent_upper at Y=-4!
                for y in range(-3, 1):
                    c.set(x, y, z, bs("minecraft:air"))
            else:
                for y in range(-3, 0):
                    c.set(x, y, z, bs("minecraft:deepslate_tiles") if y < -1 else bs("minecraft:tuff_bricks"))
                if abs(x) <= 3 or (-20 <= x <= 20 and 28 <= z <= 51):
                    is_stall_floor = abs(x) >= 14 and 32 <= z <= 47
                    c.set(x, 0, z, bs("minecraft:spruce_planks") if is_stall_floor else (bs("minecraft:polished_andesite") if abs(x) <= 2 else pick_road_stone(x, z)))
                else:
                    c.set(x, 0, z, bs("minecraft:moss_block"))

    # Carve exact guarded steps for Twin Stairways descending South from Y=0 (Z=36..38) down to Y=-3 (Z=42..44) and landing into Y=-4!
    for sx_base in (-11, 9):
        # Guardrail walls along West & East edges of shaft (X=-12 & X=-8, X=8 & X=12) + South wall at Z=49
        for z in range(35, 50):
            c.set(sx_base - 1, 1, z, bs("minecraft:tuff_brick_wall", up="true", waterlogged="false"))
            c.set(sx_base + 3, 1, z, bs("minecraft:tuff_brick_wall", up="true", waterlogged="false"))
        # Top entry starts at Z=37 moving south down:
        # Z=37 step Y=0, Z=39 step Y=-1, Z=41 step Y=-2, Z=43 step Y=-3 (hand-off at Z=45 Y=-4!)
        for idx in range(4):
            sz = 37 + idx * 2
            sy = -idx
            for x in range(sx_base, sx_base + 3):
                for z in (sz, sz + 1):
                    # Solid tuff under step, clear 5+ blocks headroom above
                    for yy in range(-3, sy):
                        c.set(x, yy, z, bs("minecraft:deepslate_tiles"))
                    c.set(x, sy, z, bs("minecraft:stone_brick_stairs", facing="north", half="bottom", shape="straight", waterlogged="false") if z == sz else bs("minecraft:stone_bricks"))
                    for yy in range(sy + 1, 6):
                        c.set(x, yy, z, bs("minecraft:air"))
        # Landing below Y=-3 around Z=45..48 cleared down through Y=-3
        for z in range(45, 50):
            for x in range(sx_base, sx_base + 3):
                for yy in range(-3, 2):
                    c.set(x, yy, z, bs("minecraft:air"))
        for x in range(sx_base, sx_base + 3):
            c.set(x, 1, 49, bs("minecraft:tuff_brick_wall", up="true", waterlogged="false"))
        # Entry arch lantern & crystal stair signage mounted on solid left stone pier
        c.set(sx_base - 1, 1, 35, bs("minecraft:chiseled_tuff_bricks"))
        c.set(sx_base - 1, 2, 35, bs("minecraft:polished_tuff"))
        c.set(sx_base - 1, 3, 35, bs("minecraft:lantern", hanging="false", waterlogged="false"))
        c.add_sign(sx_base - 1, 2, 34, "north", 0, "cavern_stair", wood="dark_oak", glow=True)
        c.set(sx_base - 1, 2, 36, bs("minecraft:lantern", hanging="false", waterlogged="false"))
        c.set(sx_base + 3, 2, 36, bs("minecraft:lantern", hanging="false", waterlogged="false"))

    # Towering Vaulted Open-Air Pavilion Columns (X=±6, ±13, ±20; Z=29, 39, 49) & Neutral Market Alcoves (NO villagers/workstations!)
    for px in (-20, -13, -6, 6, 13, 20):
        for pz in (29, 39, 49):
            c.set(px, 1, pz, bs("minecraft:chiseled_tuff_bricks"))
            for y in range(2, 8):
                c.set(px, y, pz, bs("minecraft:dark_oak_log", axis="y") if abs(px) in (6, 20) else bs("minecraft:tuff_bricks"))
            c.set(px, 6, pz, bs("minecraft:waxed_copper_bulb", lit="true", powered="false"))
            c.set(px, 7, pz, bs("minecraft:stripped_dark_oak_log", axis="y"))

    # Neutral Shaded Stall Canopies along East/West outer Pavilion aisles (X=±16..19, Z=32..36 & 42..46)
    for sx0, sx1 in [(-19, -15), (15, 19)]:
        for sz0, sz1 in [(31, 37), (41, 47)]:
            for x in range(sx0, sx1 + 1):
                for z in range(sz0, sz1 + 1):
                    if x in (sx0, sx1) and z in (sz0, sz1):
                        for y in range(1, 5):
                            c.set(x, y, z, bs("minecraft:spruce_fence", waterlogged="false"))
                    elif x in (sx0 + 1, sx1 - 1) and z == sz0 + 1:
                        c.set(x, 1, z, bs("minecraft:spruce_slab", type="top", waterlogged="false"))
                    c.set(x, 5, z, bs("minecraft:waxed_weathered_cut_copper_slab" if (x + z) % 2 == 0 else "minecraft:spruce_slab", type="bottom", waterlogged="false"))
            c.set((sx0 + sx1) // 2, 4, (sz0 + sz1) // 2, bs("minecraft:lantern", hanging="true", waterlogged="false"))

    # Central Vaulted Pavilion Canopy Roof + Asymmetric South Watch-Belfry (Y=8..17, open clear 7+ high ceiling beneath!)
    for dy in range(0, 7):
        y = 8 + dy
        for x in range(-21 + dy, 22 - dy):
            for z in range(27 + dy // 2, 52 - dy // 2):
                edge = x in (-21 + dy, 21 - dy) or z in (27 + dy // 2, 51 - dy // 2)
                if edge:
                    c.set(x, y, z, bs("minecraft:waxed_oxidized_cut_copper_slab", type="bottom", waterlogged="false") if dy % 2 == 0 else bs("minecraft:dark_oak_slab", type="bottom", waterlogged="false"))
                elif dy == 6:
                    c.set(x, y, z, bs("minecraft:waxed_copper_grate", waterlogged="false") if (x + z) % 3 == 0 else bs("minecraft:dark_oak_planks"))
    # Central Bell Belfry Crown at X=-3..3, Z=36..42, Y=14..17
    for bx in (-3, 3):
        for bz in (36, 42):
            for y in range(14, 17):
                c.set(bx, y, bz, bs("minecraft:dark_oak_log", axis="y"))
    for x in range(-4, 5):
        for z in range(35, 44):
            if abs(x) <= 2 and 37 <= z <= 41:
                c.set(x, 17, z, bs("minecraft:waxed_oxidized_cut_copper_slab", type="bottom", waterlogged="false"))
            elif abs(x) == 4 or z in (35, 43):
                c.set(x, 16, z, bs("minecraft:dark_oak_slab", type="bottom", waterlogged="false"))
    c.set(0, 15, 39, bs("minecraft:chiseled_tuff_bricks"))
    c.set(0, 16, 39, bs("minecraft:bell", attachment="floor", facing="north", powered="false"))
    for cy in range(9, 14):
        c.set(0, cy, 39, bs("minecraft:iron_chain", axis="y", waterlogged="false"))
    c.set(0, 8, 39, bs("minecraft:lantern", hanging="true", waterlogged="false"))
    c.set(-4, 1, 27, bs("minecraft:chiseled_tuff_bricks"))
    c.set(-4, 2, 27, bs("minecraft:polished_tuff"))
    c.set(-4, 3, 27, bs("minecraft:tuff_brick_slab", type="bottom", waterlogged="false"))
    c.set(-4, 4, 27, bs("minecraft:lantern", hanging="false", waterlogged="false"))
    c.add_sign(-4, 2, 26, "north", 0, "pavilion_sign", wood="spruce", glow=True)

    c.add_connection("north_plaza", 0, 0, 25, "north")
    c.add_connection("south_apron", 0, 0, 54, "south")
    c.add_connection("west_stair_bottom", -10, -3, 45, "down")
    c.add_connection("east_stair_bottom", 10, -3, 45, "down")
    return c


def build_south_pavilion_apron() -> PieceCanvas:
    # X: -15..15 (31), Y: -3..12 (16), Z: 55..66 (12) -> Bridges South Pavilion (Z=54) to South Trail (Z=67) seamlessly!
    c = PieceCanvas("south_pavilion_apron", -15, -3, 55, 15, 12, 66, "road_connector", excavate_below=False, foundation_skirt=8)
    for x in range(-15, 16):
        for z in range(55, 67):
            for y in range(-3, 0):
                c.set(x, y, z, bs("minecraft:deepslate_tiles") if y < -1 else bs("minecraft:tuff_bricks"))
            if abs(x) <= 4:
                lay_road_column(c, x, z, 0)
            else:
                c.set(x, 0, z, bs("minecraft:moss_block") if (x + z) % 2 == 0 else bs("minecraft:grass_block", snowy="false"))
    lantern_post(c, -5, 1, 58, height=3, copper=True)
    lantern_post(c, 5, 1, 58, height=3, copper=True)
    c.add_tree(-10, 1, 61, height=5, flowering=True, seed=51)
    c.add_tree(10, 1, 61, height=5, flowering=False, seed=52)
    c.add_connection("north", 0, 0, 55, "north")
    c.add_connection("south", 0, 0, 66, "south")
    return c


def build_cavern_descent_upper() -> PieceCanvas:
    # X: -14..14 (29), Y: -19..-4 (16), Z: 30..66 (37) -> Receives Twin Stairs at Y=-4 (Z=45..48) -> Atrium -> Descends to Crystal Grotto Y=-20!
    c = PieceCanvas("cavern_descent_upper", -14, -19, 30, 14, -4, 66, "cavern_descent", excavate_below=True, foundation_skirt=0)
    # Fill outer rock jacket and hollow illuminated stone staircases/atrium
    for x in range(-14, 15):
        for y in range(-19, -3):
            for z in range(30, 67):
                c.set(x, y, z, bs("minecraft:deepslate") if y < -11 else bs("minecraft:tuff"))

    # Twin Side Return Stairways descending from Z=45..49 (Y=-4) -> Northward/Southward into Upper Cavern Atrium at Z=50..62 (Y=-12)!
    #Wait: X=-11..-9 & X=+9..+11 at Y=-4 start at Z=45! Going South from Z=45 to Z=53 gives 9 steps: -4 down to -12!
    for sx_base in (-11, 9):
        for i in range(9):
            sz = 45 + i
            sy = -4 - i
            for x in range(sx_base, sx_base + 3):
                c.set(x, sy - 1, sz, bs("minecraft:deepslate_bricks"))
                c.set(x, sy, sz, bs("minecraft:deepslate_tile_stairs", facing="north", half="bottom", shape="straight", waterlogged="false"))
                for yy in range(sy + 1, min(-3, sy + 6)):
                    c.set(x, yy, sz, bs("minecraft:air"))
            # Warm wall lanterns every 3 steps (stay inside piece Y <= -4)
            if i % 3 == 1:
                lx = sx_base - 1 if sx_base < 0 else sx_base + 3
                c.set(lx, min(-4, sy + 2), sz, bs("minecraft:waxed_copper_bulb", lit="true", powered="false"))

    # Upper Cavern Atrium Gallery (X=-12..12, Y=-12..-5, Z=54..63)
    for x in range(-12, 13):
        for z in range(54, 64):
            c.set(x, -13, z, bs("minecraft:deepslate_tiles") if (abs(x) <= 4 or abs(z - 58) <= 1) else bs("minecraft:polished_deepslate"))
            for y in range(-12, -5):
                is_rib = (
                    (x in (-12, -6, 6, 12) and z in (54, 58, 63))
                    or (z == 54 and abs(x) in (5, 7, 8))
                )
                if is_rib:
                    c.set(x, y, z, bs("minecraft:chiseled_deepslate") if y == -12 else bs("minecraft:deepslate_bricks"))
                else:
                    c.set(x, y, z, bs("minecraft:air"))
            c.set(x, -5, z, bs("minecraft:deepslate_bricks") if abs(x) in (6, 12) else bs("minecraft:cobbled_deepslate"))
    # Atrium lighting & directional sign back up BOTH stairs!
    for lx in (-8, 0, 8):
        c.set(lx, -6, 58, bs("minecraft:lantern", hanging="true", waterlogged="false"))
        c.set(lx, -13, 58, bs("minecraft:waxed_copper_grate", waterlogged="false"))
        c.set(lx, -14, 58, bs("minecraft:sea_lantern"))
    c.add_sign(-8, -11, 55, "south", 0, "cavern_escape_w", wood="spruce", glow=True)
    c.add_sign(8, -11, 55, "south", 0, "cavern_escape_e", wood="spruce", glow=True)

    # Grand Central Escalator-Wide Stair descending Northward (or Southward? Moving North from Z=53 down to Z=44 gets you under Pavilion!)
    # Or Descending North at X=-3..3 from Z=54 (Y=-12) down 8 steps to Z=46 (Y=-19) -> opens straight into Crystal Grotto Gallery Y=-20!
    for i in range(8):
        sz = 53 - i
        sy = -12 - i
        for x in range(-4, 5):
            if abs(x) == 4:
                c.set(x, sy + 1, sz, bs("minecraft:deepslate_tile_wall", up="true", waterlogged="false"))
                c.set(x, sy, sz, bs("minecraft:deepslate_bricks"))
            else:
                if sy > -19:
                    c.set(x, sy - 1, sz, bs("minecraft:deepslate_bricks"))
                c.set(x, sy, sz, bs("minecraft:deepslate_brick_stairs", facing="south", half="bottom", shape="straight", waterlogged="false"))
            for yy in range(sy + 1, min(-5, sy + 6)):
                if abs(x) < 4:
                    c.set(x, yy, sz, bs("minecraft:air"))
        if i % 3 == 0:
            c.set(-4, sy + 2, sz, bs("minecraft:lantern", hanging="false", waterlogged="false"))
            c.set(4, sy + 2, sz, bs("minecraft:lantern", hanging="false", waterlogged="false"))
    # Bottom atrium shaft clearance through Y=-19 at Z=40..45 so players walk straight onto Y=-20 floor of crystal_grotto_gallery?
    # Wait: crystal_grotto_gallery covers Y=-34..-20, with its Grand Mezzanine Balcony floor at Y=-20 or floor at Y=-31!
    # Let's clear Z=38..46 X=-3..3 down to Y=-19 so cavern_descent_upper hands off directly onto a guarded landing in crystal_grotto_gallery!
    # Clear spacious headroom across X=-8..8, Z=39..45 down to Y=-19 above Grotto Balcony & upper wing steps!
    for x in range(-8, 9):
        for z in range(39, 46):
            for y in range(-19, -14):
                c.set(x, y, z, bs("minecraft:air"))
    # Guardrails around the Grotto Overlook Balcony edges (North Z=38, X=-7..7; East/West overlook X=±4 at Z=43..45)
    for x in range(-7, 8):
        c.set(x, -19, 38, bs("minecraft:deepslate_tile_wall", up="true", waterlogged="false"))
    for z in range(43, 46):
        c.set(-4, -19, z, bs("minecraft:deepslate_tile_wall", up="true", waterlogged="false"))
        c.set(4, -19, z, bs("minecraft:deepslate_tile_wall", up="true", waterlogged="false"))
    for lx in (-4, 4):
        c.set(lx, -18, 43, bs("minecraft:lantern", hanging="false", waterlogged="false"))

    # Third Return Route Connector: South Emergency Surface Tunnel at Z=64..66 (Y=-12..-9, X=-2..2) -> hands off to south_crag_trail at Z=67!
    for z in range(64, 67):
        for x in range(-2, 3):
            c.set(x, -13, z, bs("minecraft:deepslate_tiles"))
            for y in range(-12, -8):
                c.set(x, y, z, bs("minecraft:air"))
            c.set(x, -8, z, bs("minecraft:deepslate_bricks"))
        c.set(0, -9, 65, bs("minecraft:lantern", hanging="true", waterlogged="false"))
    for y in range(-12, -8):
        c.set(-3, y, 64, bs("minecraft:deepslate_bricks"))
    c.add_sign(-3, -11, 63, "north", 0, "cavern_escape_s", wood="warped", glow=True)

    c.add_connection("west_stair_top", -10, -4, 45, "up")
    c.add_connection("east_stair_top", 10, -4, 45, "up")
    c.add_connection("south_emergency_tunnel", 0, -12, 66, "south")
    c.add_connection("grotto_upper_landing", 0, -19, 44, "down")
    return c


def build_crystal_grotto_gallery() -> PieceCanvas:
    # X: -21..21 (43), Y: -34..-20 (15), Z: 32..71 (40) -> Subterranean Crystal Grotto Gallery
    c = PieceCanvas("crystal_grotto_gallery", -21, -34, 32, 21, -20, 71, "crystal_grotto", excavate_below=True, foundation_skirt=0)
    # Stone/Deepslate outer rock encasement
    for x in range(-21, 22):
        for y in range(-34, -19):
            for z in range(32, 72):
                c.set(x, y, z, bs("minecraft:deepslate") if y < -28 else bs("minecraft:tuff"))

    # Vaulted Geode Exhibition Hall interior: X=-17..17, Z=36..67, Floor Y=-32, Vault Ceiling arches up to Y=-21!
    for x in range(-17, 18):
        for z in range(36, 68):
            arch_r = (x / 17.5) ** 2 + ((z - 52) / 16.5) ** 2
            ceil_y = -21 - int(min(6, arch_r * 5.0))
            for y in range(-31, ceil_y):
                c.set(x, y, z, bs("minecraft:air"))
            # Vaulted ceiling skin
            c.set(x, ceil_y, z, bs("minecraft:calcite") if (x * x + z * z) % 7 == 0 else bs("minecraft:deepslate_bricks"))
            # Floor at Y=-32 (wide central promenade, stone bridge over shallow 1-deep luminous crystal reflection pool!)
            in_pool = 7 <= abs(x) <= 13 and 44 <= z <= 60
            if in_pool:
                c.set(x, -33, z, bs("minecraft:sea_lantern") if (x + z) % 3 == 0 else bs("minecraft:calcite"))
                c.set(x, -32, z, bs("minecraft:water", level="0"))
            elif abs(x) in (6, 14) and 43 <= z <= 61:
                # Raised curb parapet around mineral pools so players can't step unintentionally into water
                c.set(x, -32, z, bs("minecraft:polished_deepslate"))
                c.set(x, -31, z, bs("minecraft:deepslate_tile_wall", up="true", waterlogged="false"))
            elif 43 <= z <= 61 and abs(z) in (43, 61) and 6 <= abs(x) <= 14:
                c.set(x, -32, z, bs("minecraft:polished_deepslate"))
                c.set(x, -31, z, bs("minecraft:deepslate_tile_wall", up="true", waterlogged="false"))
            else:
                c.set(x, -32, z, bs("minecraft:polished_deepslate") if abs(x) <= 3 else (bs("minecraft:moss_block") if (x + z) % 5 == 0 else bs("minecraft:deepslate_tiles")))

    # Royal Grotto Overlook Balcony at Y=-20 (X=-4..4, Z=39..45) receiving cavern_descent_upper cleanly from Z=46 (Y=-19)
    for x in range(-3, 4):
        for z in range(39, 46):
            c.set(x, -20, z, bs("minecraft:polished_deepslate"))
    # North rim sill and under-stair backing at Z=38 and Z=45..46
    for x in range(-4, 5):
        c.set(x, -20, 46, bs("minecraft:deepslate_bricks"))
        c.set(x, -20, 38, bs("minecraft:deepslate_bricks"))
        c.set(x, -21, 45, bs("minecraft:deepslate_bricks"))
        for y in range(-22, -20):
            c.set(x, y, 45, bs("minecraft:deepslate_bricks"))
    # Twin Sweeping Balustrade Balcony Wings Descending East & West from X=±4 (Y=-20) -> X=±15 (Y=-31) along Z=39..42!
    for wing_sign in (-1, 1):
        for i in range(12):
            sx = wing_sign * (4 + i)
            sy = -20 - i
            st_dir = "east" if wing_sign < 0 else "west"
            for sz in range(39, 43):
                for yy in range(-32, sy):
                    c.set(sx, yy, sz, bs("minecraft:deepslate_tiles"))
                c.set(sx, sy, sz, bs("minecraft:deepslate_tile_stairs", facing=st_dir, half="bottom", shape="straight", waterlogged="false"))
                for yy in range(sy + 1, min(-20, sy + 5)):
                    c.set(sx, yy, sz, bs("minecraft:air"))
            # Guardrail walls along Z=38 and Z=43 framing both sides of the wing stair!
            for gz in (38, 43):
                c.set(sx, sy, gz, bs("minecraft:deepslate_bricks"))
                c.set(sx, min(-20, sy + 1), gz, bs("minecraft:deepslate_tile_wall", up="true", waterlogged="false"))
            if i in (4, 8):
                c.set(sx, min(-20, sy + 2), 43, bs("minecraft:lantern", hanging="false", waterlogged="false"))

    # Emergency Rear Exit Stair climbing South from Grotto Gallery floor Y=-31 (Z=60..71) up to Y=-20 (Z=71)!
    for i in range(12):
        sz = 60 + i
        sy = -31 + i
        for x in range(-2, 3):
            for yy in range(-32, sy):
                c.set(x, yy, sz, bs("minecraft:deepslate_tiles"))
            c.set(x, sy, sz, bs("minecraft:deepslate_brick_stairs", facing="south", half="bottom", shape="straight", waterlogged="false"))
            for yy in range(sy + 1, min(-19, sy + 5)):
                c.set(x, yy, sz, bs("minecraft:air"))
        c.set(-3, sy, sz, bs("minecraft:deepslate_bricks"))
        c.set(3, sy, sz, bs("minecraft:deepslate_bricks"))
    c.set(-3, -31, 60, bs("minecraft:deepslate_bricks"))
    c.set(-3, -30, 60, bs("minecraft:chiseled_deepslate"))
    c.add_sign(-3, -30, 59, "north", 0, "grotto_exit", wood="warped", glow=True)

    # Tinted-Glass Amethyst Geode Showcase Alcoves along East/West Galleries (safe non-walkable display crystals!)
    for side_x in (-16, 16):
        for gz in (40, 52, 63):
            # Showcase base at (side_x, -32.. -26, gz-2..gz+2) encased in tinted_glass
            for dx in range(-1, 2):
                for dz in range(-2, 3):
                    px, pz = side_x + dx, gz + dz
                    if c.contains(px, -31, pz):
                        on_glass = abs(dx) == 1 or abs(dz) == 2
                        if on_glass:
                            for y in range(-31, -27):
                                c.set(px, y, pz, bs("minecraft:calcite") if y == -31 else bs("minecraft:tinted_glass"))
                            c.set(px, -27, pz, bs("minecraft:polished_deepslate"))
                        else:
                            c.set(px, -31, pz, bs("minecraft:sea_lantern"))
                            c.set(px, -30, pz, bs("minecraft:amethyst_block"))
                            c.set(px, -29, pz, bs("minecraft:amethyst_block"))
                            c.set(px, -28, pz, bs("minecraft:amethyst_cluster", facing="up", waterlogged="false"))

    # Hanging Lantern Chandeliers + Floor Grate Lights + Exhibition Sign
    for (lx, lz) in [(0, 58), (-10, 40), (10, 40), (-10, 63), (10, 63)]:
        c.set(lx, -33, lz, bs("minecraft:sea_lantern"))
        c.set(lx, -32, lz, bs("minecraft:waxed_copper_grate", waterlogged="false"))
        c.set(lx, -23, lz, bs("minecraft:iron_chain", axis="y", waterlogged="false"))
        c.set(lx, -24, lz, bs("minecraft:copper_lantern", hanging="true", waterlogged="false"))
    c.set(0, -31, 56, bs("minecraft:chiseled_deepslate"))
    c.set(0, -30, 56, bs("minecraft:polished_deepslate"))
    c.set(0, -29, 56, bs("minecraft:lantern", hanging="false", waterlogged="false"))
    c.add_sign(0, -30, 57, "south", 0, "grotto_lore", wood="spruce", glow=True)

    c.add_connection("from_descent", 0, -20, 44, "up")
    c.add_connection("emergency_south_exit", 0, -21, 71, "south")
    return c


def build_south_crag_trail() -> PieceCanvas:
    # X: -22..22 (45), Y: -19..12 (32), Z: 67..95 (29) -> Surface Trail + Daylight Cavern Stair Emergence!
    c = PieceCanvas("south_crag_trail", -22, -19, 67, 22, 12, 95, "road_connector", excavate_below=True, foundation_skirt=8)
    for x in range(-22, 23):
        for z in range(67, 96):
            for y in range(-19, 0):
                c.set(x, y, z, bs("minecraft:deepslate") if y < -9 else bs("minecraft:stone"))
            if abs(x) <= 3:
                lay_road_column(c, x, z, 0)
            else:
                c.set(x, 0, z, bs("minecraft:moss_block") if (x + z) % 3 == 0 else bs("minecraft:grass_block", snowy="false"))

    # 3rd Emergency Escape Stair climbing smoothly from Z=67 (Y=-12, connected directly to cavern_descent_upper's emergency tunnel AND Grotto stair!) up to surface Z=79 (Y=0)!
    for i in range(13):
        sz = 67 + i
        sy = -12 + i
        for x in range(4, 9):  # Run along X=5..7 right beside the main South surface road X=-3..3!
            if x in (4, 8):
                c.set(x, sy, sz, bs("minecraft:tuff_bricks"))
                if sy >= 0:
                    c.set(x, 1, sz, bs("minecraft:tuff_brick_wall", up="true", waterlogged="false"))
            else:
                c.set(x, sy - 1, sz, bs("minecraft:deepslate_tiles"))
                c.set(x, sy, sz, bs("minecraft:stone_brick_stairs", facing="south", half="bottom", shape="straight", waterlogged="false") if sy < 0 else bs("minecraft:stone_bricks"))
                for yy in range(sy + 1, max(4, sy + 5)):
                    c.set(x, yy, sz, bs("minecraft:air"))
        if i % 3 == 0 and sy < 0:
            c.set(4, sy + 2, sz, bs("minecraft:lantern", hanging="false", waterlogged="false"))

    # Connect cavern_descent_upper exit (0, -12, 66) smoothly across Z=67..68 from X=0..4 onto stair at X=5..7!
    for x in range(0, 5):
        for z in (67, 68):
            c.set(x, -13, z, bs("minecraft:deepslate_tiles"))
            for yy in range(-12, -8):
                c.set(x, yy, z, bs("minecraft:air"))
            c.set(x, -8, z, bs("minecraft:deepslate_bricks"))
    c.set(2, -10, 67, bs("minecraft:waxed_copper_bulb", lit="true", powered="false"))

    # Continue Grotto Rear Emergency Stair cleanly from (X=-2..2, Z=68..71 headroom -> Z=72..79, Y=-19..-12 -> cross-landing X=-7..2 -> West Daylight Gazebo at Z=92, Y=0)!
    for sz in range(68, 72):
        # Clear headroom directly above grotto's Z=68..71 upper steps inside Y=-19..-15
        for x in range(-2, 3):
            for yy in range(-19, -14):
                c.set(x, yy, sz, bs("minecraft:air"))
    for i in range(8):
        sz = 72 + i
        sy = -19 + i
        for x in range(-2, 3):
            if sy > -19:
                c.set(x, sy - 1, sz, bs("minecraft:deepslate_tiles"))
            c.set(x, sy, sz, bs("minecraft:deepslate_brick_stairs", facing="south", half="bottom", shape="straight", waterlogged="false"))
            for yy in range(sy + 1, sy + 5):
                c.set(x, yy, sz, bs("minecraft:air"))
        c.set(-3, sy, sz, bs("minecraft:deepslate_bricks"))
        c.set(3, sy, sz, bs("minecraft:deepslate_bricks"))
        if i % 3 == 0:
            c.set(3, sy + 2, sz, bs("minecraft:waxed_copper_bulb", lit="true", powered="false"))
    # Deep cross-gallery landing at Y=-12, Z=79..80 from X=-7..2 (completely under South road!)
    for x in range(-7, 3):
        for z in (79, 80):
            c.set(x, -13, z, bs("minecraft:deepslate_tiles"))
            for yy in range(-12, -8):
                c.set(x, yy, z, bs("minecraft:air"))
            c.set(x, -8, z, bs("minecraft:deepslate_bricks"))
    c.set(-5, -10, 80, bs("minecraft:waxed_copper_bulb", lit="true", powered="false"))
    # West Daylight Stairwell climbing South along X=-7..-5 (beside road X=-3..3!) from Z=81 (Y=-11) up to Z=92 (Y=0)
    for i in range(12):
        sz = 81 + i
        sy = -11 + i
        for x in range(-8, -3):
            if x in (-8, -4):
                c.set(x, sy, sz, bs("minecraft:tuff_bricks"))
                if sy >= 0:
                    c.set(x, 1, sz, bs("minecraft:tuff_brick_wall", up="true", waterlogged="false"))
            else:
                c.set(x, sy - 1, sz, bs("minecraft:deepslate_tiles"))
                c.set(x, sy, sz, bs("minecraft:stone_brick_stairs", facing="south", half="bottom", shape="straight", waterlogged="false") if sy < 0 else bs("minecraft:stone_bricks"))
                for yy in range(sy + 1, max(4, sy + 5)):
                    c.set(x, yy, sz, bs("minecraft:air"))
        if i % 4 == 0 and sy < 0:
            c.set(-8, sy + 2, sz, bs("minecraft:lantern", hanging="false", waterlogged="false"))
    for z in range(91, 95):
        for x in range(-7, -4):
            lay_road_column(c, x, z, 0)
        if z in (91, 94):
            for y in range(1, 5):
                c.set(-8, y, z, bs("minecraft:dark_oak_log", axis="y"))
                c.set(-4, y, z, bs("minecraft:dark_oak_log", axis="y"))
    for x in range(-8, -3):
        for z in range(91, 95):
            c.set(x, 5, z, bs("minecraft:waxed_oxidized_cut_copper_slab", type="bottom", waterlogged="false"))
    c.set(-6, 4, 92, bs("minecraft:lantern", hanging="true", waterlogged="false"))
    # Emergency Cavern Exit Kiosk Arch right beside South Surface Trail at X=4..8, Z=79..81!
    for x in (4, 8):
        for z in (79, 81):
            for y in range(1, 5):
                c.set(x, y, z, bs("minecraft:dark_oak_log", axis="y"))
    for x in range(4, 9):
        for z in range(79, 82):
            c.set(x, 5, z, bs("minecraft:waxed_oxidized_cut_copper_slab", type="bottom", waterlogged="false"))
    c.set(6, 4, 80, bs("minecraft:lantern", hanging="true", waterlogged="false"))
    c.add_sign(4, 2, 82, "south", 0, "cavern_surface_portal", wood="spruce", glow=True)

    # Scenic Crag Boulders & Sanctuary Pines toward Southern Perimeter (Z=84..95)
    c.add_tree(-14, 1, 76, height=6, flowering=False, seed=61)
    c.add_tree(15, 1, 85, height=5, flowering=True, seed=62)
    lantern_post(c, -4, 1, 72, height=3, copper=False)
    lantern_post(c, -4, 1, 88, height=3, copper=True)
    lantern_post(c, 4, 1, 88, height=3, copper=True)

    c.add_connection("north", 0, 0, 67, "north")
    c.add_connection("south_wilds", 0, 0, 95, "south")
    return c


def build_corner_landscape(piece_id: str, x0: int, z0: int, x1: int, z1: int, quad: str) -> PieceCanvas:
    """Organic ancient ruins, mossy crag boulders, water garden / grove filling ~192x192 corners cleanly."""
    c = PieceCanvas(piece_id, x0, -4, z0, x1, 14, z1, "perimeter_landscape", excavate_below=False, foundation_skirt=8)
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    seed = {"nw": 101, "ne": 202, "sw": 303, "se": 404}[quad]
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            d = math.hypot(x - cx, z - cz)
            for y in range(-4, 0):
                c.set(x, y, z, bs("minecraft:stone") if y < -1 else bs("minecraft:dirt"))
            if quad == "sw" and 4.5 <= d <= 8.5 and abs(x - cx) <= 6:
                # Shallow garden brook pool with safe stone crossing!
                if abs(z - cz) <= 1:
                    c.set(x, 0, z, bs("minecraft:spruce_planks"))
                else:
                    c.set(x, -1, z, bs("minecraft:clay"))
                    c.set(x, 0, z, bs("minecraft:water", level="0"))
            elif d <= 5.5:
                c.set(x, 0, z, pick_weathered_stone(x, 0, z))
            else:
                c.set(x, 0, z, bs("minecraft:moss_block") if (x * 7 + z * 11 + seed) % 5 == 0 else bs("minecraft:grass_block", snowy="false"))

    # Focal Ancient Ruin Arch / Watch Pillar + Lantern + Sanctuary Grove Trees
    for (px, pz, h) in [(cx - 3, cz - 3, 5), (cx + 3, cz - 3, 4), (cx - 3, cz + 3, 4), (cx + 3, cz + 3, 6)]:
        for y in range(1, h):
            c.set(px, y, pz, pick_weathered_stone(px, y, pz))
        c.set(px, h, pz, bs("minecraft:stone_brick_slab", type="bottom", waterlogged="false"))
    c.set(cx - 3, 5, cz - 3, bs("minecraft:lantern", hanging="false", waterlogged="false"))
    c.set(cx + 3, 6, cz + 3, bs("minecraft:waxed_copper_bulb", lit="true", powered="false"))
    c.set(cx + 3, 7, cz + 3, bs("minecraft:lantern", hanging="false", waterlogged="false"))
    # Stone ruin arch spanning between (cx-3, cz-3) and (cx+3, cz-3)
    for x in range(cx - 2, cx + 3):
        c.set(x, 4, cz - 3, pick_weathered_stone(x, 4, cz - 3))
        if abs(x - cx) <= 1:
            c.set(x, 5, cz - 3, bs("minecraft:moss_carpet"))
    c.set(cx, 3, cz - 3, bs("minecraft:lantern", hanging="true", waterlogged="false"))

    if quad == "se":
        # Ancient amethyst crystal outcrop shrine in SE grove
        c.set(cx, 1, cz, bs("minecraft:calcite"))
        c.set(cx, 2, cz, bs("minecraft:amethyst_block"))
        c.set(cx, 3, cz, bs("minecraft:amethyst_cluster", facing="up", waterlogged="false"))
        c.set(cx + 1, 1, cz, bs("minecraft:sea_lantern"))
        c.set(cx + 1, 2, cz, bs("minecraft:tinted_glass"))

    c.add_tree(cx - 10, 1, cz - 9, height=5, flowering=(quad in ("nw", "sw")), seed=seed + 1)
    c.add_tree(cx + 11, 1, cz + 9, height=6, flowering=(quad in ("ne", "se")), seed=seed + 2)
    c.add_tree(cx - 9, 1, cz + 11, height=4, flowering=True, seed=seed + 3)
    return c


# --- Validation & Compilation ---

def load_mc263_valid_block_ids() -> set[str]:
    if not SERVER_JAR_CANDIDATE.exists():
        return set()
    ids = {"minecraft:air", "minecraft:cave_air", "minecraft:void_air", "minecraft:water", "minecraft:lava"}
    with zipfile.ZipFile(SERVER_JAR_CANDIDATE) as z:
        for name in z.namelist():
            if name.startswith("data/minecraft/loot_table/blocks/") and name.endswith(".json"):
                blk = name[len("data/minecraft/loot_table/blocks/"):-len(".json")]
                ids.add("minecraft:" + blk)
                if blk.endswith("_sign") and not blk.endswith("_hanging_sign"):
                    wood = blk[:-len("_sign")]
                    ids.add(f"minecraft:{wood}_wall_sign")
    return ids


def verify_all_pieces(canvases: List[PieceCanvas]) -> None:
    # 1. Verify pairwise 3D AABB disjointness
    for i, a in enumerate(canvases):
        for b in canvases[i + 1 :]:
            overlap_x = not (a.x1 < b.x0 or b.x1 < a.x0)
            overlap_y = not (a.y1 < b.y0 or b.y1 < a.y0)
            overlap_z = not (a.z1 < b.z0 or b.z1 < a.z0)
            if overlap_x and overlap_y and overlap_z:
                raise AssertionError(
                    f"Bounding box overlap between {a.piece_id} ({a.x0}..{a.x1},{a.y0}..{a.y1},{a.z0}..{a.z1}) "
                    f"and {b.piece_id} ({b.x0}..{b.x1},{b.y0}..{b.y1},{b.z0}..{b.z1})"
                )

    # 2. Global combined voxel map for cross-piece checks (pad cleanliness, supports, hazards)
    world: Dict[Tuple[int, int, int], BlockSpec] = {}
    valid_ids = load_mc263_valid_block_ids()

    for c in canvases:
        for (hx, hy, hz), spec in c.voxels.items():
            bid, props = spec
            if valid_ids and bid not in valid_ids:
                raise AssertionError(f"Unverified MC 26.3 block ID in {c.piece_id}: {bid}")
            if bid != "minecraft:air":
                world[(hx, hy, hz)] = spec

    # 3. Verify 13x13 Safe Arrival Pad (-6..6, -6..6)
    for x in range(-6, 7):
        for z in range(-6, 7):
            floor_id = world.get((x, 0, z), AIR)[0]
            if floor_id in ("minecraft:air", "minecraft:water", "minecraft:lava", "minecraft:magma_block"):
                raise AssertionError(f"Unsafe arrival pad floor at ({x},0,{z}): {floor_id}")
            if "slab" in floor_id or "carpet" in floor_id:
                raise AssertionError(f"Arrival pad must have solid full block at ({x},0,{z}), got {floor_id}")
            for y in range(1, 6):
                above_id = world.get((x, y, z), AIR)[0]
                if above_id != "minecraft:air":
                    raise AssertionError(f"Arrival pad headroom blocked at ({x},{y},{z}): {above_id}")

    # 4. Verify zero open lava/magma/fire/cactus/sweet_berry hazards anywhere in Sanctuary
    forbidden_hazards = {
        "minecraft:lava", "minecraft:magma_block", "minecraft:fire",
        "minecraft:soul_fire", "minecraft:cactus", "minecraft:sweet_berry_bush",
        "minecraft:bubble_column", "minecraft:spawner", "minecraft:trial_spawner",
        "minecraft:nether_portal", "minecraft:end_portal", "minecraft:command_block",
        "minecraft:repeating_command_block", "minecraft:chain_command_block",
    }
    for pos, (bid, _) in world.items():
        if bid in forbidden_hazards:
            raise AssertionError(f"Forbidden block {bid} found at {pos}")

    # 5. Verify hanging lanterns/chains/signs/bells have solid attachment
    for (x, y, z), (bid, props) in world.items():
        pmap = dict(props)
        if bid in ("minecraft:lantern", "minecraft:copper_lantern", "minecraft:soul_lantern"):
            if pmap.get("hanging") == "true":
                above = world.get((x, y + 1, z), AIR)[0]
                if above == "minecraft:air":
                    raise AssertionError(f"Floating hanging lantern at {(x, y, z)}")
            else:
                below = world.get((x, y - 1, z), AIR)[0]
                if below == "minecraft:air":
                    raise AssertionError(f"Floating standing lantern at {(x, y, z)}")
        if bid.endswith("_wall_sign"):
            facing = pmap["facing"]
            dx, dz = {"north": (0, 1), "south": (0, -1), "east": (-1, 0), "west": (1, 0)}[facing]
            support = world.get((x + dx, y, z + dz), AIR)[0]
            if support == "minecraft:air":
                raise AssertionError(f"Wall sign at {(x, y, z)} facing {facing} has no solid backing at {(x+dx, y, z+dz)}")


def build_all_pieces() -> List[PieceCanvas]:
    return [
        build_plaza_core(),
        build_ring_cardinal("plaza_ring_north", -15, -24, 15, -16, "north"),
        build_ring_cardinal("plaza_ring_south", -15, 16, 15, 24, "south"),
        build_ring_side("plaza_ring_west", -24, -24, -16, 15, "west"),
        build_ring_sw_corner(),
        build_ring_side("plaza_ring_east", 16, -24, 24, 15, "east"),
        build_heartroot_lower_se(),
        build_heartroot_trunk(),
        build_heartroot_canopy(),
        build_north_gate(),
        build_north_trail_outpost(),
        build_east_guild_hall(),
        build_side_trail("east_meadow_trail", 60, 95, "east"),
        build_west_nature_garden(),
        build_side_trail("west_grove_trail", -95, -60, "west"),
        build_south_trading_pavilion(),
        build_south_pavilion_apron(),
        build_cavern_descent_upper(),
        build_crystal_grotto_gallery(),
        build_south_crag_trail(),
        build_corner_landscape("landscape_nw", -72, -72, -32, -32, "nw"),
        build_corner_landscape("landscape_ne", 32, -72, 72, -32, "ne"),
        build_corner_landscape("landscape_sw", -72, 32, -32, 72, "sw"),
        build_corner_landscape("landscape_se", 32, 32, 72, 72, "se"),
    ]


def main() -> None:
    canvases = build_all_pieces()
    verify_all_pieces(canvases)

    STRUCT_OUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Clean stale .nbt files in server_spawn before writing fresh set
    for old_file in STRUCT_OUT_DIR.glob("*.nbt"):
        old_file.unlink()

    manifest_pieces = []
    min_x = min(c.x0 for c in canvases)
    min_y = min(c.y0 for c in canvases)
    min_z = min(c.z0 for c in canvases)
    max_x = max(c.x1 for c in canvases)
    max_y = max(c.y1 for c in canvases)
    max_z = max(c.z1 for c in canvases)

    total_non_air = 0
    for c in canvases:
        local_blocks = c.to_local_blocks()
        non_air = sum(1 for v in local_blocks.values() if v != AIR)
        total_non_air += non_air
        raw_bytes = encode_structure_nbt((c.sx, c.sy, c.sz), local_blocks)
        nbt_path = STRUCT_OUT_DIR / f"{c.piece_id}.nbt"
        nbt_path.write_bytes(raw_bytes)
        sha = hashlib.sha256(raw_bytes).hexdigest()[:16]

        manifest_pieces.append(
            {
                "id": c.piece_id,
                "template": f"canopycavern:server_spawn/{c.piece_id}",
                "role": c.role,
                "offset": [c.x0, c.y0, c.z0],
                "size": [c.sx, c.sy, c.sz],
                "excavateBelow": c.excavate_below,
                "foundationSkirt": c.foundation_skirt,
                "nonAirBlocks": non_air,
                "sha256Prefix": sha,
                "connections": c.connections,
                "signs": c.signs,
                "lecterns": c.lecterns,
            }
        )

    manifest = {
        "schemaVersion": 1,
        "hubId": "canopy_sanctuary",
        "dataVersion": DATA_VERSION,
        "arrivalLocalPos": [0, 1, 0],
        "arrivalBaseYaw": 180.0,
        "safePadRadius": 6,
        "safeZoneDefaultRadius": 48,
        "envelopeMin": [min_x, min_y, min_z],
        "envelopeMax": [max_x, max_y, max_z],
        "supportedRotations": ["NONE", "CLOCKWISE_90", "CLOCKWISE_180", "COUNTERCLOCKWISE_90"],
        "pieces": manifest_pieces,
    }
    MANIFEST_OUT_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(
        f"Generated {len(canvases)} Canopy Sanctuary modules "
        f"(envelope [{min_x}..{max_x}, {min_y}..{max_y}, {min_z}..{max_z}], "
        f"span {max_x-min_x+1}x{max_y-min_y+1}x{max_z-min_z+1}, total non-air={total_non_air})"
    )


if __name__ == "__main__":
    main()
