#!/usr/bin/env python3
"""Generates Canopy Sanctuary compact modular NBT structures and manifest.json for Minecraft Java 26.3."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import math
import struct
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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


def encode_structure_nbt(
    size: Tuple[int, int, int],
    blocks_dict: Dict[Tuple[int, int, int], Tuple[str, Tuple[Tuple[str, str], ...]]],
) -> bytes:
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
    _write_payload(buf=raw, tag=TAG_COMPOUND, val=root)
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

    def add_sign(
        self,
        hx: int,
        hy: int,
        hz: int,
        wall_dir: Optional[str],
        rot16: int,
        key_prefix: str,
        wood: str = "oak",
        glow: bool = True,
    ) -> None:
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

    def add_tree(self, cx: int, cy: int, cz: int, height: int = 5, flowering: bool = False, seed: int = 1) -> None:
        """Places a compact azalea/dark-oak sanctuary tree inside canvas bounds."""
        for dy in range(height):
            if self.contains(cx, cy + dy, cz):
                self.set(cx, cy + dy, cz, bs("minecraft:dark_oak_log", axis="y"))
        top = cy + height
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                for dy in range(-2, 3):
                    d2 = dx * dx + dz * dz + (dy * dy * 1.8)
                    if d2 <= 6.2:
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
    """Lays solid foundation down to y0 with weathered surface stonework."""
    for y in range(c.y0, y_top):
        c.set(x, y, z, bs("minecraft:tuff_bricks") if y == y_top - 1 else bs("minecraft:deepslate_tiles"))
    c.set(x, y_top, z, pick_road_stone(x, z))


def lantern_post(c: PieceCanvas, x: int, y_base: int, z: int, height: int = 3, copper: bool = False) -> None:
    """Places a grounded multi-layered stone + dark-oak lantern post."""
    c.set(x, y_base, z, bs("minecraft:chiseled_tuff_bricks"))
    for dy in range(1, height):
        c.set(
            x,
            y_base + dy,
            z,
            bs("minecraft:tuff_brick_wall", east="none", north="none", south="none", west="none", up="true", waterlogged="false")
            if dy == 1
            else bs("minecraft:dark_oak_fence", east="false", north="false", south="false", west="false", waterlogged="false"),
        )
    c.set(x, y_base + height, z, bs("minecraft:dark_oak_slab", type="bottom", waterlogged="false"))
    lblock = "minecraft:copper_lantern" if copper else "minecraft:lantern"
    c.set(x, y_base + height + 1, z, bs(lblock, hanging="false", waterlogged="false"))


# --- Compact 10-Module Piece Builders (Envelope [-40..40, -29..29, -40..40], 81x59x81) ---


def build_plaza_core() -> PieceCanvas:
    """Central Arrival Plaza (31x12x31, [-15..15, -4..7, -15..15])."""
    c = PieceCanvas("plaza_core", -15, -4, -15, 15, 7, 15, "arrival_plaza", excavate_below=False, foundation_skirt=8)
    for x in range(-15, 16):
        for z in range(-15, 16):
            r = math.hypot(x, z)
            in_cardinal = (abs(x) <= 3) or (abs(z) <= 3)
            if abs(x) <= 6 and abs(z) <= 6:
                # Arrival Safe Pad [-6..6]: flat flush cobblestone/andesite compass inlay
                for y in range(-4, 0):
                    c.set(x, y, z, bs("minecraft:tuff_bricks") if y == -1 else bs("minecraft:deepslate_tiles"))
                if x == 0 and z == 0:
                    c.set(x, 0, z, bs("minecraft:chiseled_tuff_bricks"))
                elif abs(x) <= 1 and abs(z) <= 1:
                    c.set(x, 0, z, bs("minecraft:waxed_oxidized_cut_copper"))
                elif x == 0 or z == 0 or abs(x) == abs(z):
                    c.set(x, 0, z, bs("minecraft:polished_andesite"))
                elif max(abs(x), abs(z)) == 6:
                    c.set(x, 0, z, bs("minecraft:tuff_bricks"))
                else:
                    c.set(x, 0, z, bs("minecraft:stone_bricks"))
            elif in_cardinal or r <= 13.8:
                lay_road_column(c, x, z, 0)
                if 11.2 <= r <= 12.6 and not in_cardinal:
                    c.set(x, 0, z, bs("minecraft:polished_andesite"))
                if 12.8 <= r <= 14.0 and not in_cardinal and not (x >= 7 and z >= 7):
                    c.set(
                        x,
                        1,
                        z,
                        bs("minecraft:tuff_brick_wall", east="none", north="none", south="none", west="none", up="true", waterlogged="false"),
                    )
            else:
                for y in range(-4, 0):
                    c.set(x, y, z, bs("minecraft:stone") if y < -1 else bs("minecraft:dirt"))
                c.set(x, 0, z, bs("minecraft:moss_block") if (x + z) % 2 == 0 else bs("minecraft:grass_block", snowy="false"))
                if x < 0 and z < 0 and abs(x + 12) <= 1 and abs(z + 12) <= 1:
                    c.set(x, 0, z, bs("minecraft:flowering_azalea") if (x == -12 and z == -12) else bs("minecraft:moss_block"))

    # Flush concealed sea-lantern inlay pads at compass rim (-6/6 perimeter & avenues)
    for (lx, lz) in [(0, -4), (0, 4), (-4, 0), (4, 0), (-11, 0), (11, 0), (0, -11), (0, 11)]:
        c.set(lx, -1, lz, bs("minecraft:sea_lantern"))
        c.set(lx, 0, lz, bs("minecraft:waxed_copper_grate", waterlogged="false"))

    # Cozy stone benches in NW, NE, SW plaza pocket corners
    c.set(-10, 1, -9, bs("minecraft:spruce_stairs", facing="south", half="bottom", shape="straight", waterlogged="false"))
    c.set(-9, 1, -9, bs("minecraft:spruce_stairs", facing="south", half="bottom", shape="straight", waterlogged="false"))
    c.set(10, 1, -9, bs("minecraft:spruce_stairs", facing="south", half="bottom", shape="straight", waterlogged="false"))
    c.set(9, 1, -9, bs("minecraft:spruce_stairs", facing="south", half="bottom", shape="straight", waterlogged="false"))
    c.set(-10, 1, 9, bs("minecraft:spruce_stairs", facing="north", half="bottom", shape="straight", waterlogged="false"))
    c.set(-9, 1, 9, bs("minecraft:spruce_stairs", facing="north", half="bottom", shape="straight", waterlogged="false"))

    # Decorative corner lantern posts keeping [-6..6] unobstructed
    for (px, pz) in [(-4, -13), (4, -13), (-13, -4), (-13, 4), (13, -4), (13, 4), (-4, 13), (4, 13)]:
        lantern_post(c, px, 1, pz, height=3, copper=(abs(px) > 10 or pz > 10))

    # Signpost pillars outside [-6..6] pad + Sanctuary Welcome Lectern
    pillars = [
        (-4, -8, "south", "welcome", (-4, 2, -7)),
        (4, -8, "south", "choices", (4, 2, -7)),
        (8, -4, "west", "dir_east", (7, 2, -4)),
        (-8, -4, "east", "dir_west", (-7, 2, -4)),
        (-4, 8, "north", "dir_south", (-4, 2, 7)),
    ]
    for (bx, bz, wdir, skey, (sx, sy, sz)) in pillars:
        c.set(bx, 1, bz, bs("minecraft:chiseled_tuff_bricks"))
        c.set(bx, 2, bz, bs("minecraft:dark_oak_log", axis="y"))
        c.set(bx, 3, bz, bs("minecraft:waxed_oxidized_cut_copper_slab", type="bottom", waterlogged="false"))
        c.add_sign(sx, sy, sz, wdir, 0, skey, wood="oak", glow=True)

    c.set(4, 0, 7, bs("minecraft:chiseled_tuff_bricks"))
    c.add_lectern(4, 1, 7, "north", "canopy_sanctuary_welcome")

    # SE Heartroot root hollow base strictly inside x:7..15, z:7..15 (never touches [-6..6]!)
    for x in range(7, 16):
        for z in range(7, 16):
            c.set(x, 0, z, bs("minecraft:moss_block") if (x + z) % 3 else bs("minecraft:rooted_dirt"))
            dist = math.hypot(x - 10, z - 10)
            if dist <= 1.8:
                for y in range(1, 8):
                    c.set(x, y, z, bs("minecraft:dark_oak_wood", axis="y") if dist > 0.5 else bs("minecraft:dark_oak_log", axis="y"))
            elif dist <= 3.1:
                c.set(x, 1, z, bs("minecraft:dark_oak_wood", axis="y"))
                if x in (9, 10, 11) or z in (9, 10, 11):
                    c.set(x, 2, z, bs("minecraft:dark_oak_wood", axis="y"))
    # Welcoming mossy spirit shrine niche inside base of Heartroot
    c.set(8, 1, 8, bs("minecraft:sea_lantern"))
    c.set(8, 2, 8, bs("minecraft:amethyst_cluster", facing="up", waterlogged="false"))
    c.set(7, 1, 10, bs("minecraft:flowering_azalea"))
    c.set(10, 1, 7, bs("minecraft:flowering_azalea"))

    c.add_connection("north", 0, 0, -15, "north")
    c.add_connection("south", 0, 0, 15, "south")
    c.add_connection("east", 15, 0, 0, "east")
    c.add_connection("west", -15, 0, 0, "west")
    c.add_connection("heartroot_collar", 10, 7, 10, "up")
    return c


def build_heartroot_lower_se() -> PieceCanvas:
    """Compact SE Heartroot moss garden terrace bridging East Guild & South Pavilion (12x12x15)."""
    c = PieceCanvas("heartroot_lower_se", 16, -4, 13, 27, 7, 27, "landmark", excavate_below=False, foundation_skirt=8)
    for x in range(16, 28):
        for z in range(13, 28):
            d = math.hypot(x - 21, z - 20)
            for y in range(-4, 0):
                c.set(x, y, z, bs("minecraft:stone") if y < -1 else bs("minecraft:dirt"))
            if d <= 2.3 and 18 <= z <= 22:
                c.set(x, -1, z, bs("minecraft:clay"))
                c.set(x, 0, z, bs("minecraft:water", level="0"))
            elif d <= 4.8:
                c.set(x, 0, z, bs("minecraft:moss_block"))
            else:
                c.set(x, 0, z, pick_road_stone(x, z) if (x <= 18 or z <= 15) else bs("minecraft:grass_block", snowy="false"))
    c.set(18, 1, 17, bs("minecraft:flowering_azalea"))
    c.set(24, 1, 16, bs("minecraft:azalea"))
    lantern_post(c, 18, 1, 24, height=3, copper=True)
    lantern_post(c, 24, 1, 24, height=3, copper=False)
    c.set(20, 1, 25, bs("minecraft:spruce_stairs", facing="north", half="bottom", shape="straight", waterlogged="false"))
    c.set(21, 1, 25, bs("minecraft:spruce_stairs", facing="north", half="bottom", shape="straight", waterlogged="false"))
    c.add_tree(24, 1, 22, height=4, flowering=True, seed=17)
    return c


def build_heartroot_trunk() -> PieceCanvas:
    """Rising ancient Heartroot trunk strictly within x:4..15, z:4..15, y:8..18 (no wing collision)."""
    c = PieceCanvas("heartroot_trunk", 4, 8, 4, 15, 18, 15, "landmark", excavate_below=False, foundation_skirt=0, fill_air=False)
    for y in range(8, 19):
        t = (y - 8) / 10.0
        radius = 1.85 if y < 14 else 1.85 + (t - 0.6) * 2.5
        for x in range(4, 16):
            for z in range(4, 16):
                d = math.hypot(x - 10, z - 10)
                if d <= radius:
                    c.set(x, y, z, bs("minecraft:dark_oak_wood", axis="y"))
    # Extending primary branch arms near y=16..18
    for dy, off in [(16, 3), (17, 4), (18, 5)]:
        for s in range(1, off + 1):
            for (bx, bz) in [(10 - s, 10), (min(15, 10 + s), 10), (10, 10 - s), (10, min(15, 10 + s))]:
                if c.contains(bx, dy, bz):
                    c.set(bx, dy, bz, bs("minecraft:dark_oak_wood", axis="y"))
    # Hanging lanterns & shroomlight knots under limbs
    c.set(7, 15, 10, bs("minecraft:lantern", hanging="true", waterlogged="false"))
    c.set(10, 15, 7, bs("minecraft:lantern", hanging="true", waterlogged="false"))
    c.set(12, 16, 12, bs("minecraft:shroomlight"))
    return c


def build_heartroot_canopy() -> PieceCanvas:
    """Lush overhanging Heartroot leaf crown strictly y:19..29, open center view above Arrival Pad."""
    c = PieceCanvas("heartroot_canopy", -6, 19, -6, 25, 29, 25, "landmark", excavate_below=False, foundation_skirt=0, fill_air=False)
    cx, cy, cz = 11, 24, 11
    for x in range(-6, 26):
        for y in range(19, 30):
            for z in range(-6, 26):
                # Keep direct central arrival column [-4..4, -4..4] crisp sky-open while arching gracefully overhead
                if abs(x) <= 3 and abs(z) <= 3 and y <= 24:
                    continue
                dx = (x - cx) / 13.5
                dy = (y - cy) / 4.8
                dz = (z - cz) / 13.5
                ell = dx * dx + dy * dy + dz * dz
                if ell <= 1.0:
                    h = (x * 73856093 ^ y * 19349663 ^ z * 83492791) & 0xFF
                    if y <= 21 and math.hypot(x - 10, z - 10) <= 4.5 and h % 3 == 0:
                        c.set(x, y, z, bs("minecraft:dark_oak_wood", axis="y"))
                    elif h % 19 == 0 and y >= 21 and y <= 25:
                        c.set(x, y, z, bs("minecraft:shroomlight"))
                    elif h % 4 == 0:
                        c.set(x, y, z, bs("minecraft:flowering_azalea_leaves", distance="1", persistent="true", waterlogged="false"))
                    elif h % 2 == 0:
                        c.set(x, y, z, bs("minecraft:azalea_leaves", distance="1", persistent="true", waterlogged="false"))
                    else:
                        c.set(x, y, z, bs("minecraft:dark_oak_leaves", distance="1", persistent="true", waterlogged="false"))
    # Hanging lanterns suspended cleanly beneath leaf shelves
    for (lx, ly, lz) in [(6, 19, 6), (16, 19, 6), (6, 19, 16), (16, 19, 16)]:
        if c.get(lx, ly + 1, lz) != AIR:
            c.set(lx, ly, lz, bs("minecraft:lantern", hanging="true", waterlogged="false"))
    return c


def build_north_expedition_gate() -> PieceCanvas:
    """Compact North Expedition Gate & Perimeter Exit (-13..13, -4..17, -40..-16)."""
    c = PieceCanvas("north_expedition_gate", -13, -4, -40, 13, 17, -16, "north_gate", excavate_below=False, foundation_skirt=8)
    for x in range(-13, 14):
        for z in range(-40, -15):
            if abs(x) <= 3:
                lay_road_column(c, x, z, 0)
            else:
                for y in range(-4, 0):
                    c.set(x, y, z, bs("minecraft:stone") if y < -1 else bs("minecraft:dirt"))
                c.set(x, 0, z, bs("minecraft:moss_block") if (x * 3 + z * 5) % 4 == 0 else bs("minecraft:grass_block", snowy="false"))
                if abs(x) == 4 and z % 2 == 0:
                    c.set(x, 1, z, bs("minecraft:tuff_brick_wall", east="none", north="none", south="none", west="none", up="true", waterlogged="false"))

    # Twin gatehouse towers flanking road at x:-7..-4 and x:4..7, z:-29..-24
    for tx0 in (-7, 4):
        for x in range(tx0, tx0 + 4):
            for z in range(-29, -23):
                is_edge = x in (tx0, tx0 + 3) or z in (-29, -24)
                for y in range(0, 13):
                    if y == 0 or is_edge:
                        if abs(x) == 4 and z in (-27, -26) and 1 <= y <= 4:
                            continue  # tower inner arch alcove
                        c.set(x, y, z, pick_weathered_stone(x, y, z))
                # Crenellated copper-capped roof at y=13..16
                c.set(x, 13, z, bs("minecraft:waxed_oxidized_cut_copper"))
                if is_edge and (x + z) % 2 == 0:
                    c.set(x, 14, z, bs("minecraft:tuff_brick_wall", up="true", waterlogged="false"))
        cx = tx0 + 1
        c.set(cx, 14, -27, bs("minecraft:tuff_bricks"))
        c.set(cx, 15, -27, bs("minecraft:waxed_copper_bulb", lit="true", powered="false"))
        c.set(cx, 16, -27, bs("minecraft:lantern", hanging="false", waterlogged="false"))

    # Overhead gatehouse bridge & dark-oak timber arch spanning road (y=7..10, z=-28..-25)
    for x in range(-4, 5):
        for z in (-28, -27, -26, -25):
            c.set(x, 7, z, bs("minecraft:spruce_planks"))
            if z in (-28, -25):
                c.set(x, 8, z, bs("minecraft:tuff_brick_wall", up="true", waterlogged="false"))
                if x % 4 == 0:
                    c.set(x, 9, z, bs("minecraft:lantern", hanging="false", waterlogged="false"))
    c.set(0, 6, -27, bs("minecraft:lantern", hanging="true", waterlogged="false"))
    c.set(-4, 2, -24, bs("minecraft:chiseled_tuff_bricks"))
    c.add_sign(-4, 2, -23, "south", 0, "north_gate", wood="oak", glow=True)

    # Compact Exit Perimeter Boundary Marker Arch at z=-38..-40
    for bx in (-4, 4):
        for y in range(1, 6):
            c.set(bx, y, -38, bs("minecraft:dark_oak_log", axis="y"))
    for x in range(-4, 5):
        c.set(x, 6, -38, bs("minecraft:waxed_oxidized_cut_copper_slab", type="bottom", waterlogged="false"))
    c.set(0, 5, -38, bs("minecraft:lantern", hanging="true", waterlogged="false"))
    c.set(-4, 2, -38, bs("minecraft:chiseled_tuff_bricks"))
    c.add_sign(-4, 2, -37, "south", 0, "trail_exit", wood="spruce", glow=True)

    # Grove trees & lantern posts
    c.add_tree(-10, 1, -20, height=5, flowering=True, seed=21)
    c.add_tree(10, 1, -21, height=4, flowering=False, seed=22)
    c.add_tree(-10, 1, -34, height=4, flowering=False, seed=23)
    c.add_tree(10, 1, -34, height=5, flowering=True, seed=24)
    lantern_post(c, -4, 1, -18, height=3, copper=False)
    lantern_post(c, 4, 1, -18, height=3, copper=False)
    lantern_post(c, 4, 1, -33, height=3, copper=True)

    c.add_connection("south", 0, 0, -16, "south")
    c.add_connection("north_wilds", 0, 0, -40, "north")
    return c


def build_east_guild_hall() -> PieceCanvas:
    """Compact Adventurer Guild Hall & Field Guide Exhibit (16..40, -4..18, -12..12)."""
    c = PieceCanvas("east_guild_hall", 16, -4, -12, 40, 18, 12, "east_guild", excavate_below=False, foundation_skirt=8)
    for x in range(16, 41):
        for z in range(-12, 13):
            if 20 <= x <= 36 and -9 <= z <= 9:
                for y in range(-4, 0):
                    c.set(x, y, z, bs("minecraft:tuff_bricks") if y == -1 else bs("minecraft:deepslate_tiles"))
                if abs(z) <= 1:
                    c.set(x, 0, z, bs("minecraft:red_carpet") if abs(z) == 0 and 22 <= x <= 34 else bs("minecraft:polished_andesite"))
                else:
                    c.set(x, 0, z, bs("minecraft:spruce_planks"))
            elif abs(z) <= 3:
                lay_road_column(c, x, z, 0)
            else:
                for y in range(-4, 0):
                    c.set(x, y, z, bs("minecraft:stone") if y < -1 else bs("minecraft:dirt"))
                c.set(x, 0, z, bs("minecraft:moss_block") if (x + z) % 3 == 0 else bs("minecraft:grass_block", snowy="false"))

    # Guild Hall Walls (x:20..36, z:-9..9, y:1..6) with spacious W & E portals (z in -2..2, y:1..4)
    for x in range(20, 37):
        for z in (-9, 9):
            for y in range(1, 7):
                if y == 1:
                    c.set(x, y, z, bs("minecraft:stone_bricks"))
                elif x in (20, 28, 36):
                    c.set(x, y, z, bs("minecraft:dark_oak_log", axis="y"))
                elif y in (3, 4) and x in (23, 24, 25, 31, 32, 33):
                    c.set(x, y, z, bs("minecraft:tinted_glass"))
                else:
                    c.set(x, y, z, bs("minecraft:spruce_planks") if y >= 2 else bs("minecraft:stone_bricks"))
    for z in range(-9, 10):
        for x in (20, 36):
            for y in range(1, 7):
                if abs(z) <= 2 and y <= 4:
                    continue  # 5-wide, 4-tall front & rear doorways!
                if z in (-9, -3, 3, 9):
                    c.set(x, y, z, bs("minecraft:dark_oak_log", axis="y"))
                elif y == 1:
                    c.set(x, y, z, bs("minecraft:stone_bricks"))
                else:
                    c.set(x, y, z, bs("minecraft:spruce_planks"))
    # Decorative arch lintel above both doorways
    for x in (20, 36):
        for z in range(-2, 3):
            c.set(x, 5, z, bs("minecraft:dark_oak_log", axis="z"))
        c.set(x, 4, 0, bs("minecraft:lantern", hanging="true", waterlogged="false"))

    # Vaulted Pitched Copper & Dark-Oak Roof (y:7..17, closed completely at ridge dy=10 -> y=17)
    for dy in range(0, 11):
        y = 7 + dy
        z_min = -10 + dy
        z_max = 10 - dy
        for x in range(19, 38):
            targets = (z_min,) if z_min == z_max else (z_min, z_max)
            for z in targets:
                spec = (
                    bs("minecraft:waxed_oxidized_cut_copper")
                    if x in (19, 37) or z_min == z_max
                    else bs("minecraft:waxed_oxidized_cut_copper_slab", type="bottom", waterlogged="false")
                    if dy % 2 == 1
                    else bs("minecraft:waxed_weathered_cut_copper")
                )
                c.set(x, y, z, spec)
            if z_min + 1 <= z_max - 1 and x in (19, 37) and dy < 6:
                for gz in range(z_min + 1, z_max):
                    c.set(x, y, gz, bs("minecraft:tinted_glass") if abs(gz) <= 2 else bs("minecraft:spruce_planks"))
    # Structural tie-beams & hanging chandeliers (grounded from beams at y=7 -> lantern at y=5)
    for bx in (24, 28, 32):
        for bz in range(-9, 10):
            c.set(bx, 7, bz, bs("minecraft:dark_oak_log", axis="z"))
        c.set(bx, 6, 0, bs("minecraft:dark_oak_fence", waterlogged="false"))
        c.set(bx, 5, 0, bs("minecraft:lantern", hanging="true", waterlogged="false"))
    c.set(28, 16, 0, bs("minecraft:sea_lantern"))

    # Interior Equipment & Alcove Benches (zero damage hazards)
    c.set(23, 1, -6, bs("minecraft:chiseled_tuff_bricks"))
    c.set(23, 2, -6, bs("minecraft:dark_oak_log", axis="y"))
    c.add_sign(23, 2, -5, "south", 0, "guild_guide", wood="oak", glow=True)
    c.add_lectern(24, 1, -4, "south", "guild_field_guide")
    c.add_lectern(24, 1, 4, "north", "guild_expedition_routes")

    c.set(29, 1, -8, bs("minecraft:chiseled_tuff_bricks"))
    c.set(29, 2, -8, bs("minecraft:spruce_planks"))
    c.set(28, 1, -8, bs("minecraft:cartography_table"))
    c.set(30, 1, -8, bs("minecraft:bookshelf"))
    c.add_sign(29, 2, -7, "south", 0, "guild_map", wood="oak", glow=True)

    c.set(29, 1, 8, bs("minecraft:bookshelf"))
    c.set(29, 2, 8, bs("minecraft:spruce_planks"))
    c.set(28, 1, 8, bs("minecraft:crafting_table"))
    c.set(30, 1, 8, bs("minecraft:barrel", facing="north", open="false"))
    c.set(32, 1, 8, bs("minecraft:anvil", facing="east"))
    c.add_sign(29, 2, 7, "north", 0, "guild_notice", wood="oak", glow=True)

    c.set(34, 1, -6, bs("minecraft:loom", facing="west"))
    c.set(34, 1, 6, bs("minecraft:smithing_table"))
    lantern_post(c, 18, 1, -4, height=3, copper=False)
    lantern_post(c, 18, 1, 4, height=3, copper=False)
    lantern_post(c, 38, 1, -4, height=3, copper=True)
    lantern_post(c, 38, 1, 4, height=3, copper=True)
    c.add_tree(38, 1, -9, height=4, flowering=True, seed=31)
    c.add_tree(38, 1, 9, height=4, flowering=False, seed=32)

    c.add_connection("west", 16, 0, 0, "west")
    c.add_connection("east_wilds", 40, 0, 0, "east")
    return c


def build_west_nature_garden() -> PieceCanvas:
    """Compact Nature Garden, Stream Footbridge & Terrace (-40..-16, -4..15, -12..12)."""
    c = PieceCanvas("west_nature_garden", -40, -4, -12, -16, 15, 12, "west_garden", excavate_below=False, foundation_skirt=8)
    for x in range(-40, -15):
        for z in range(-12, 13):
            in_stream = (-29 <= x <= -24) and (abs(z) >= 3) and (abs(z) <= 10)
            in_path = abs(z) <= 2
            for y in range(-4, 0):
                c.set(x, y, z, bs("minecraft:clay") if (in_stream and y == -1) else bs("minecraft:stone") if y < -1 else bs("minecraft:dirt"))
            if in_path:
                if -29 <= x <= -24:
                    # Flush wooden footbridge cleanly crossing over shallow brook stream
                    c.set(x, -1, z, bs("minecraft:water", level="0"))
                    c.set(x, 0, z, bs("minecraft:spruce_planks"))
                    if abs(z) == 2:
                        c.set(x, 1, z, bs("minecraft:spruce_fence", waterlogged="false"))
                else:
                    lay_road_column(c, x, z, 0)
            elif in_stream:
                c.set(x, 0, z, bs("minecraft:water", level="0"))
                if x in (-27, -26) and abs(z) == 6:
                    c.set(x, 0, z, bs("minecraft:sea_lantern"))
            else:
                c.set(x, 0, z, bs("minecraft:moss_block") if (x * 5 + z * 3) % 3 == 0 else bs("minecraft:grass_block", snowy="false"))
                if (x * 11 + z * 7) % 13 == 0 and abs(z) >= 4:
                    c.set(x, 1, z, bs("minecraft:flowering_azalea"))

    # Entrance Timber Pergola framing West Road + Garden Lore Sign
    for gz in (-3, 3):
        for y in range(1, 5):
            c.set(-19, y, gz, bs("minecraft:dark_oak_log", axis="y"))
    for z in range(-3, 4):
        c.set(-19, 5, z, bs("minecraft:dark_oak_slab", type="bottom", waterlogged="false"))
    c.set(-19, 4, 0, bs("minecraft:lantern", hanging="true", waterlogged="false"))
    c.set(-19, 1, -4, bs("minecraft:chiseled_tuff_bricks"))
    c.set(-19, 2, -4, bs("minecraft:dark_oak_log", axis="y"))
    c.add_sign(-18, 2, -4, "east", 0, "garden_lore", wood="oak", glow=True)

    # Cozy Gazebo Lounge on SW Terrace (-36..-31, z:5..10) & Flowering Grove Trees
    for (gx, gz) in [(-36, 5), (-32, 5), (-36, 9), (-32, 9)]:
        for y in range(1, 4):
            c.set(gx, y, gz, bs("minecraft:dark_oak_fence", waterlogged="false"))
    c.fill(-36, 4, 5, -32, 4, 9, bs("minecraft:waxed_oxidized_cut_copper_slab", type="bottom", waterlogged="false"))
    c.set(-34, 3, 7, bs("minecraft:lantern", hanging="true", waterlogged="false"))
    c.set(-34, 1, 8, bs("minecraft:spruce_stairs", facing="north", half="bottom", shape="straight", waterlogged="false"))

    c.add_tree(-21, 1, -8, height=5, flowering=True, seed=41)
    c.add_tree(-35, 1, -8, height=5, flowering=False, seed=42)
    c.add_tree(-20, 1, 8, height=4, flowering=True, seed=43)
    lantern_post(c, -31, 1, -3, height=3, copper=False)
    lantern_post(c, -31, 1, 3, height=3, copper=False)
    lantern_post(c, -39, 1, -3, height=3, copper=True)
    lantern_post(c, -39, 1, 3, height=3, copper=True)

    c.add_connection("east", -16, 0, 0, "east")
    c.add_connection("west_wilds", -40, 0, 0, "west")
    return c


def build_south_trading_pavilion() -> PieceCanvas:
    """Compact Rest Pavilion, Stall Alcoves, Twin Cavern Stairheads & Surface Daylight Kiosk (-15..15, -3..17, 16..40)."""
    c = PieceCanvas("south_trading_pavilion", -15, -3, 16, 15, 17, 40, "south_pavilion", excavate_below=False, foundation_skirt=8)
    for x in range(-15, 16):
        for z in range(16, 41):
            in_main = (-13 <= x <= 13) and (16 <= z <= 28)
            in_trail = (-2 <= x <= 2) and (29 <= z <= 40)
            if in_main or in_trail:
                lay_road_column(c, x, z, 0)
            else:
                for y in range(-3, 0):
                    c.set(x, y, z, bs("minecraft:stone") if y < -1 else bs("minecraft:dirt"))
                c.set(x, 0, z, bs("minecraft:moss_block") if (x + z) % 3 == 0 else bs("minecraft:grass_block", snowy="false"))

    # Open-Air Rest Pavilion Columns & Hip Roof over z:18..27, x:-8..8 (keeps central walkway clear!)
    for px in (-7, -3, 3, 7):
        for pz in (18, 26):
            for y in range(1, 6):
                c.set(px, y, pz, bs("minecraft:dark_oak_log", axis="y"))
    for x in range(-8, 9):
        for z in range(17, 28):
            edge = abs(x) == 8 or z in (17, 27)
            c.set(x, 6, z, bs("minecraft:dark_oak_slab", type="bottom", waterlogged="false") if edge else bs("minecraft:spruce_planks"))
            if not edge and (abs(x) <= 6 and 18 <= z <= 26):
                c.set(x, 7, z, bs("minecraft:waxed_oxidized_cut_copper_slab", type="bottom", waterlogged="false"))
    # Central Belfry Watchtower over x:-2..2, z:20..24 rising up to y=17 + Ground-Reachable Bell
    for bx in (-2, 2):
        for bz in (20, 24):
            for y in range(7, 13):
                c.set(bx, y, bz, bs("minecraft:dark_oak_log", axis="y"))
    c.fill(-2, 13, 20, 2, 13, 24, bs("minecraft:waxed_oxidized_cut_copper"))
    c.fill(-1, 14, 21, 1, 14, 23, bs("minecraft:waxed_weathered_cut_copper"))
    c.set(0, 15, 22, bs("minecraft:waxed_copper_bulb", lit="true", powered="false"))
    c.set(0, 16, 22, bs("minecraft:lantern", hanging="false", waterlogged="false"))
    c.set(0, 5, 22, bs("minecraft:lantern", hanging="true", waterlogged="false"))
    # Ground-reachable Sanctuary Bell hung under oak lintel on west alcove frame
    c.set(-3, 3, 22, bs("minecraft:dark_oak_log", axis="z"))
    c.set(-3, 2, 22, bs("minecraft:bell", attachment="ceiling", facing="east", powered="false"))

    # West & East Rest / Merchant Stall Alcoves (x:-12..-9 & x:9..12, z:19..24)
    for side_x0, dir_face in [(-12, "east"), (10, "west")]:
        c.fill(side_x0, 1, 19, side_x0 + 2, 1, 24, bs("minecraft:air"))
        for z in (19, 24):
            for y in range(1, 4):
                c.set(side_x0, y, z, bs("minecraft:dark_oak_fence", waterlogged="false"))
                c.set(side_x0 + 2, y, z, bs("minecraft:dark_oak_fence", waterlogged="false"))
        c.fill(side_x0, 4, 19, side_x0 + 2, 4, 24, bs("minecraft:waxed_oxidized_cut_copper_slab", type="bottom", waterlogged="false"))
        mid_x = side_x0 + 1
        c.set(mid_x, 1, 21, bs("minecraft:crafting_table"))
        c.set(mid_x, 1, 22, bs("minecraft:barrel", facing=dir_face, open="false"))
        c.set(mid_x, 3, 22, bs("minecraft:lantern", hanging="true", waterlogged="false"))

    # Signs for Pavilion & Cavern Descent
    c.set(-4, 1, 19, bs("minecraft:chiseled_tuff_bricks"))
    c.set(-4, 2, 19, bs("minecraft:dark_oak_log", axis="y"))
    c.add_sign(-4, 2, 18, "north", 0, "pavilion_sign", wood="oak", glow=True)

    c.set(-8, 1, 27, bs("minecraft:chiseled_tuff_bricks"))
    c.set(-8, 2, 27, bs("minecraft:dark_oak_log", axis="y"))
    c.add_sign(-8, 2, 26, "north", 0, "cavern_stair", wood="spruce", glow=True)

    # Twin Entry Stairwells Descending South into cavern_descent_upper (x:-13..-11 & x:11..13, z:28..38)
    for (sx0, sx1) in [(-13, -11), (11, 13)]:
        # Protective tuff stone wall railing flanking stair opening on z:29..39
        for z in range(29, 40):
            for wx in (sx0 - 1, sx1 + 1):
                c.set(wx, 1, z, bs("minecraft:tuff_brick_wall", up="true", waterlogged="false"))
        for x in range(sx0 - 1, sx1 + 2):
            c.set(x, 1, 39, bs("minecraft:tuff_brick_wall", up="true", waterlogged="false"))
        # Steps z=29 (y=0) -> z=32 (y=-3), plus open air shaft z=33..38 down to y=-3 for clean headroom!
        for x in range(sx0, sx1 + 1):
            c.set(x, 0, 28, bs("minecraft:polished_andesite"))
            c.fill(x, 1, 28, x, 5, 28, bs("minecraft:air"))
            for step_idx, z in enumerate((29, 30, 31, 32)):
                sy = -step_idx
                for by in range(-3, sy):
                    c.set(x, by, z, bs("minecraft:tuff_bricks"))
                c.set(x, sy, z, bs("minecraft:stone_brick_stairs", facing="north", half="bottom", shape="straight", waterlogged="false"))
                c.fill(x, sy + 1, z, x, 5, z, bs("minecraft:air"))
            for z in range(33, 39):
                c.fill(x, -3, z, x, 5, z, bs("minecraft:air"))
        lantern_post(c, sx0 - 1 if sx0 < 0 else sx1 + 1, 1, 29, height=3, copper=True)
        lantern_post(c, sx0 - 1 if sx0 < 0 else sx1 + 1, 1, 39, height=3, copper=False)

    # Direct South Daylight Escape Stair Emergent Kiosk (x:5..7, emerging at z:35..39 from underground)
    # Divider wall railing around emergence cutout at x=4, x=8 and z=35..39
    for z in range(35, 39):
        c.set(4, 1, z, bs("minecraft:tuff_brick_wall", up="true", waterlogged="false"))
        c.set(8, 1, z, bs("minecraft:tuff_brick_wall", up="true", waterlogged="false"))
    for x in range(4, 9):
        c.set(x, 1, 34, bs("minecraft:tuff_brick_wall", up="true", waterlogged="false"))
    # Carve daylight opening & upper steps z=35 (-3 air headroom), z=36 (y=-3), z=37 (y=-2), z=38 (y=-1), z=39 (y=0 landing!)
    step_map = {36: -3, 37: -2, 38: -1}
    for x in range(5, 8):
        c.fill(x, -3, 35, x, 5, 35, bs("minecraft:air"))
        for z, sy in step_map.items():
            for by in range(-3, sy):
                c.set(x, by, z, bs("minecraft:tuff_bricks"))
            c.set(x, sy, z, bs("minecraft:stone_brick_stairs", facing="south", half="bottom", shape="straight", waterlogged="false"))
            c.fill(x, sy + 1, z, x, 5, z, bs("minecraft:air"))
        c.set(x, 0, 39, bs("minecraft:polished_andesite"))
        c.set(x, 0, 40, pick_road_stone(x, 40))
    # Kiosk Canopy & Exit Portal Sign facing South Trail
    for px in (4, 8):
        for pz in (36, 39):
            for y in range(1, 5):
                c.set(px, y, pz, bs("minecraft:dark_oak_log", axis="y"))
    c.fill(4, 5, 36, 8, 5, 39, bs("minecraft:waxed_oxidized_cut_copper_slab", type="bottom", waterlogged="false"))
    c.set(6, 4, 38, bs("minecraft:lantern", hanging="true", waterlogged="false"))
    c.set(3, 1, 39, bs("minecraft:chiseled_tuff_bricks"))
    c.set(3, 2, 39, bs("minecraft:dark_oak_log", axis="y"))
    c.add_sign(2, 2, 39, "west", 0, "cavern_surface_portal", wood="spruce", glow=True)

    c.add_connection("north", 0, 0, 16, "north")
    c.add_connection("south_wilds", 0, 0, 40, "south")
    c.add_connection("to_atrium_w", -12, -3, 33, "down")
    c.add_connection("to_atrium_e", 12, -3, 33, "down")
    return c


def build_cavern_descent_upper() -> PieceCanvas:
    """Upper Cavern Atrium connecting Twin Entry Stairs, Central Grotto Stair, and 3rd Daylight Return (-15..15, -17..-4, 16..40)."""
    c = PieceCanvas("cavern_descent_upper", -15, -17, 16, 15, -4, 40, "cavern_upper", excavate_below=True, foundation_skirt=4)
    # 1. Start with solid subterranean deepslate/tuff shell
    c.fill(-15, -17, 16, 15, -4, 40, bs("minecraft:deepslate_bricks"))

    # 2. Carve spacious Atrium Chamber across x:-9..9, z:17..38, floor at y=-10, roof y=-4 (air y:-9..-5 = 5 blocks tall!)
    c.fill(-9, -9, 17, 9, -5, 38, bs("minecraft:air"))
    for x in range(-9, 10):
        for z in range(17, 39):
            c.set(x, -10, z, pick_weathered_stone(x, -10, z))
    # Vault ceiling ribs & warm sea-lantern lighting at y=-5
    for z in (19, 24, 29, 34):
        for x in range(-9, 10):
            if abs(x) >= 6 or z in (19, 34):
                c.set(x, -5, z, bs("minecraft:tuff_bricks"))
        c.set(0, -5, z, bs("minecraft:sea_lantern"))
    for x in (-7, 7):
        for z in (20, 26, 32):
            c.set(x, -5, z, bs("minecraft:lantern", hanging="true", waterlogged="false"))

    # 3. Twin Entry Stairwells continuing from y=-4 (z=33) down to y=-7 (z=36..38), turning inward to Atrium y=-10
    for sign_x, sx0, sx1, turn_cols, face_out in [
        (-1, -13, -11, [(-10, -7), (-9, -8), (-8, -9)], "east"),
        (1, 11, 13, [(10, -7), (9, -8), (8, -9)], "west"),
    ]:
        for x in range(sx0, sx1 + 1):
            for step_idx, z in enumerate((33, 34, 35)):
                sy = -4 - step_idx
                c.set(x, sy, z, bs("minecraft:stone_brick_stairs", facing="north", half="bottom", shape="straight", waterlogged="false"))
                if sy + 1 <= -4:
                    c.fill(x, sy + 1, z, x, -4, z, bs("minecraft:air"))
                c.set(x, sy - 1, z, bs("minecraft:tuff_bricks"))
            # Bottom stair landing z=36..38 at y=-7
            for z in range(36, 39):
                c.set(x, -7, z, bs("minecraft:polished_andesite"))
                c.fill(x, -6, z, x, -4, z, bs("minecraft:air"))
        # Turning steps inward to Atrium floor y=-10 (at x=-7 or x=7)
        for col_x, sy in turn_cols:
            for z in range(36, 39):
                c.fill(col_x, -10, z, col_x, sy - 1, z, bs("minecraft:tuff_bricks"))
                c.set(col_x, sy, z, bs("minecraft:stone_brick_stairs", facing=face_out, half="bottom", shape="straight", waterlogged="false"))
                c.fill(col_x, sy + 1, z, col_x, -4, z, bs("minecraft:air"))
        # Lantern & Escape Sign at bottom of each twin stair
        px = -8 if sign_x < 0 else 8
        c.set(px, -9, 35, bs("minecraft:chiseled_tuff_bricks"))
        c.set(px, -8, 35, bs("minecraft:dark_oak_log", axis="y"))
        c.set(px, -7, 35, bs("minecraft:lantern", hanging="false", waterlogged="false"))
        if sign_x < 0:
            c.add_sign(-7, -8, 35, "east", 0, "cavern_escape_w", wood="spruce", glow=True)
        else:
            c.add_sign(7, -8, 35, "west", 0, "cavern_escape_e", wood="spruce", glow=True)

    # 4. Grand Central Staircase Descending Atrium (z=20, y=-10) down toward Crystal Grotto (z=27, y=-17), plus Atrium floor cutout above!
    for z in range(20, 34):
        sy = -10 - (z - 20)
        for x in range(-3, 4):
            if x in (-3, 3):
                # Framing low balustrade along upper edge
                if z == 20:
                    c.set(x, -9, z, bs("minecraft:tuff_brick_wall", up="true", waterlogged="false"))
            else:
                if -17 <= sy <= -10:
                    c.fill(x, sy + 1, z, x, -5, z, bs("minecraft:air"))
                    if sy - 1 >= -17:
                        c.fill(x, -17, z, x, sy - 1, z, bs("minecraft:air") if sy <= -13 else bs("minecraft:deepslate_bricks"))
                        c.set(x, sy - 1, z, bs("minecraft:tuff_bricks"))
                    c.set(x, sy, z, bs("minecraft:stone_brick_stairs", facing="north", half="bottom", shape="straight", waterlogged="false"))
                elif sy < -17:
                    # Carve ceiling opening above lower Grotto steps (z=28..33) so player never bumps ceiling at y=-17
                    c.fill(x, -17, z, x, -10, z, bs("minecraft:air"))
                    # Side railing along Atrium overlook around open stair pit
                    if z == 21:
                        c.set(x, -9, 20, bs("minecraft:air"))
    # Safety tuff-brick balustrade framing the Grotto pit edge at z:21..34 along x=-3 & x=3 and South Overlook z=34
    for z in range(20, 35):
        c.set(-3, -9, z, bs("minecraft:tuff_brick_wall", up="true", waterlogged="false"))
        c.set(3, -9, z, bs("minecraft:tuff_brick_wall", up="true", waterlogged="false"))
    for x in range(-3, 4):
        c.set(x, -9, 35, bs("minecraft:tuff_brick_wall", up="true", waterlogged="false"))

    # 5. Continuous 3rd Direct South Daylight Escape Stair (x:5..7) spanning Grotto (z=16, y=-23) -> Atrium (z=29, y=-10) -> Surface (z=35, y=-4)
    # Wall enclosing x=4 and x=8 on z=17..35 EXCEPT open 3-block Atrium entrance at z=29..31!
    for z in range(17, 36):
        for y in range(-9, -4):
            if not x_door_open(z):
                c.set(4, y, z, bs("minecraft:tuff_bricks"))
            c.set(8, y, z, bs("minecraft:tuff_bricks"))
    # Re-open Atrium doorway at x=4, z=29..31, y=-9..-6
    for z in (29, 30, 31):
        c.fill(4, -9, z, 4, -6, z, bs("minecraft:air"))
    for x in range(5, 8):
        for z in range(16, 36):
            sy = z - 39  # z=22 -> y=-17, z=29 -> y=-10, z=35 -> y=-4
            if sy >= -17:
                if sy - 1 >= -17:
                    c.set(x, sy - 1, z, bs("minecraft:tuff_bricks"))
                c.set(x, sy, z, bs("minecraft:stone_brick_stairs", facing="south", half="bottom", shape="straight", waterlogged="false"))
                # Ensure 4+ clear air blocks above every step inside cavern_descent_upper
                top_air = min(-4, sy + 4)
                if sy + 1 <= top_air:
                    c.fill(x, sy + 1, z, x, top_air, z, bs("minecraft:air"))
            else:
                # Carve headroom inside cavern_descent_upper for steps down at y=-21..-18 (z=18..21)
                top_air = min(-4, sy + 4)
                if top_air >= -17:
                    c.fill(x, -17, z, x, top_air, z, bs("minecraft:air"))
        # Keep x=5..7 ceiling support at y=-4.. above East Entry Stair at z=36..38 cleanly (nothing blocks y=-9..-5!)
        for z in range(36, 39):
            c.fill(x, -9, z, x, -5, z, bs("minecraft:air"))
            c.set(x, -4, z, bs("minecraft:tuff_bricks"))  # solid soffit under Daylight Stair at z=36..38!
            c.set(x, -10, z, pick_weathered_stone(x, -10, z))

    # Daylight Exit Sign mounted directly on west wall face beside 3-wide Atrium doorway (leaves z=29..31 unobstructed)
    c.add_sign(3, -8, 28, "west", 0, "cavern_escape_s", wood="spruce", glow=True)

    c.add_connection("to_grotto", 0, -17, 27, "down")
    return c


def x_door_open(z: int) -> bool:
    return 29 <= z <= 31


def build_crystal_grotto_gallery() -> PieceCanvas:
    """Vaulted Underground Crystal Grotto Gallery (-15..15, -29..-18, 12..40)."""
    c = PieceCanvas("crystal_grotto_gallery", -15, -29, 12, 15, -18, 40, "crystal_grotto", excavate_below=True, foundation_skirt=4)
    # 1. Subterranean deepslate geode shell
    c.fill(-15, -29, 12, 15, -18, 40, bs("minecraft:deepslate_tiles"))

    # 2. Carve Main Grotto Hallway & Vault (x:-13..13, z:14..38, floor y=-24, air y:-23..-19 = 5 blocks tall!)
    c.fill(-13, -23, 14, 13, -19, 38, bs("minecraft:air"))
    for x in range(-13, 14):
        for z in range(14, 39):
            # Geode reflection pools along outer E & W wings (x in -11..-8 & x in 8..11, z in 20..30)
            in_pool = ((x in (-11, -10, -9) or x in (9, 10, 11)) and 21 <= z <= 29)
            if in_pool:
                c.set(x, -25, z, bs("minecraft:calcite"))
                c.set(x, -24, z, bs("minecraft:water", level="0"))
                if z == 25 and x in (-10, 10):
                    c.set(x, -25, z, bs("minecraft:sea_lantern"))
            else:
                c.set(x, -24, z, bs("minecraft:moss_block") if (x * 7 + z * 5) % 9 == 0 else bs("minecraft:deepslate_bricks") if (x + z) % 3 == 0 else bs("minecraft:polished_andesite"))

    # Carved Amethyst & Calcite Ceiling Ribs (y=-19) + Sea-Lantern Illumination
    for z in (16, 22, 28, 34, 37):
        for x in range(-13, 14):
            if abs(x) >= 11 or z in (16, 37):
                c.set(x, -19, z, bs("minecraft:calcite"))
        c.set(0, -19, z, bs("minecraft:sea_lantern"))
    for (ax, az) in [(-12, 18), (-12, 25), (-12, 32), (12, 18), (12, 25), (12, 32)]:
        c.set(ax, -23, az, bs("minecraft:calcite"))
        c.set(ax, -22, az, bs("minecraft:amethyst_block"))
        c.set(ax, -21, az, bs("minecraft:amethyst_cluster", facing="up", waterlogged="false"))
        c.set(ax, -19, az, bs("minecraft:lantern", hanging="true", waterlogged="false"))

    # Featured Tinted-Glass Amethyst Crystal Exhibits on SW & SE Amphitheater
    for (ex, ez) in [(-9, 35), (9, 35)]:
        c.set(ex, -23, ez, bs("minecraft:calcite"))
        c.set(ex, -22, ez, bs("minecraft:amethyst_block"))
        c.set(ex, -21, ez, bs("minecraft:amethyst_cluster", facing="up", waterlogged="false"))
        c.set(ex + (1 if ex < 0 else -1), -23, ez, bs("minecraft:tinted_glass"))
        c.set(ex, -23, ez - 1, bs("minecraft:tinted_glass"))
        c.set(ex, -20, ez, bs("minecraft:sea_lantern"))

    # 3. Continue Grand Central Staircase (x:-2..2) from y=-18 (z=28) down to Grotto floor y=-24 (z=34)!
    for x in range(-2, 3):
        for z in range(28, 34):
            sy = -10 - (z - 20)  # z=28 -> -18 .. z=33 -> -23
            c.set(x, sy - 1, z, bs("minecraft:tuff_bricks"))
            c.set(x, sy, z, bs("minecraft:stone_brick_stairs", facing="north", half="bottom", shape="straight", waterlogged="false"))
            if sy + 1 <= -18:
                c.fill(x, sy + 1, z, x, -18, z, bs("minecraft:air"))
    # Carve central entry headroom under z=28..30 at y=-18.. and ground entry lanterns on pedestals
    for px in (-3, 3):
        c.set(px, -23, 33, bs("minecraft:chiseled_tuff_bricks"))
        c.set(px, -22, 33, bs("minecraft:lantern", hanging="false", waterlogged="false"))

    # 4. Start of 3rd Direct South Daylight Escape Stair (x:5..7) from Grotto floor y=-24 (z=15) up through y=-18 (z=21)
    for x in range(5, 8):
        c.set(x, -24, 14, bs("minecraft:polished_andesite"))
        c.set(x, -24, 15, bs("minecraft:polished_andesite"))
        c.fill(x, -23, 14, x, -19, 15, bs("minecraft:air"))
        for z in range(16, 22):
            sy = z - 39  # z=16 -> y=-23 .. z=21 -> y=-18
            c.set(x, sy - 1, z, bs("minecraft:tuff_bricks"))
            c.set(x, sy, z, bs("minecraft:stone_brick_stairs", facing="south", half="bottom", shape="straight", waterlogged="false"))
            if sy + 1 <= -18:
                c.fill(x, sy + 1, z, x, -18, z, bs("minecraft:air"))

    # Grotto Shrine Lore Sign & Daylight Return Sign
    c.set(0, -23, 38, bs("minecraft:calcite"))
    c.set(0, -22, 38, bs("minecraft:amethyst_block"))
    c.set(0, -21, 38, bs("minecraft:sea_lantern"))
    c.add_sign(0, -22, 37, "north", 0, "grotto_lore", wood="spruce", glow=True)

    c.set(3, -23, 16, bs("minecraft:chiseled_tuff_bricks"))
    c.set(3, -22, 16, bs("minecraft:dark_oak_log", axis="y"))
    c.set(3, -21, 16, bs("minecraft:lantern", hanging="false", waterlogged="false"))
    c.add_sign(3, -22, 17, "south", 0, "grotto_exit", wood="spruce", glow=True)

    c.add_connection("from_atrium", 0, -18, 28, "up")
    return c


# --- Validation & Compilation ---


def load_mc263_valid_block_ids() -> set[str]:
    if not SERVER_JAR_CANDIDATE.exists():
        return set()
    ids = {"minecraft:air", "minecraft:cave_air", "minecraft:void_air", "minecraft:water", "minecraft:lava"}
    with zipfile.ZipFile(SERVER_JAR_CANDIDATE) as z:
        for name in z.namelist():
            if name.startswith("data/minecraft/loot_table/blocks/") and name.endswith(".json"):
                blk = name[len("data/minecraft/loot_table/blocks/") : -len(".json")]
                ids.add("minecraft:" + blk)
                if blk.endswith("_sign") and not blk.endswith("_hanging_sign"):
                    wood = blk[: -len("_sign")]
                    ids.add(f"minecraft:{wood}_wall_sign")
    return ids


WALL_BACK_OFFSET = {
    "north": (0, 0, 1),
    "south": (0, 0, -1),
    "east": (-1, 0, 0),
    "west": (1, 0, 0),
}


def verify_all_pieces(pieces: List[PieceCanvas], valid_ids: set[str]) -> Tuple[int, int, int, int, int, int]:
    """Asserts zero piece overlaps, valid MC 26.3 IDs, supported signs/lecterns, safe arrival pad, and bounds <= 48."""
    for i, a in enumerate(pieces):
        if max(a.sx, a.sy, a.sz) > 48:
            raise AssertionError(f"Piece {a.piece_id} exceeds 48: {(a.sx, a.sy, a.sz)}")
        for b in pieces[i + 1 :]:
            ox = not (a.x1 < b.x0 or b.x1 < a.x0)
            oy = not (a.y1 < b.y0 or b.y1 < a.y0)
            oz = not (a.z1 < b.z0 or b.z1 < a.z0)
            if ox and oy and oz:
                raise AssertionError(
                    f"AABB overlap between {a.piece_id} [{a.x0}..{a.x1},{a.y0}..{a.y1},{a.z0}..{a.z1}] "
                    f"and {b.piece_id} [{b.x0}..{b.x1},{b.y0}..{b.y1},{b.z0}..{b.z1}]"
                )

        for (x, y, z), (blk_id, props) in a.voxels.items():
            if valid_ids and blk_id not in valid_ids:
                raise AssertionError(f"Invalid block ID {blk_id} in {a.piece_id}")
            if blk_id in ("minecraft:lava", "minecraft:fire", "minecraft:soul_fire", "minecraft:magma_block"):
                raise AssertionError(f"Hazard block {blk_id} forbidden in hub ({a.piece_id})")
            if blk_id.endswith("_wall_sign"):
                facing = dict(props).get("facing")
                dx, dy, dz = WALL_BACK_OFFSET[facing]
                sup = a.get(x + dx, y + dy, z + dz)[0]
                if sup == "minecraft:air":
                    raise AssertionError(f"Detached wall sign at ({x},{y},{z}) in {a.piece_id} facing={facing}")
            if blk_id in ("minecraft:lantern", "minecraft:copper_lantern"):
                hanging = dict(props).get("hanging") == "true"
                dy = 1 if hanging else -1
                if a.contains(x, y + dy, z) and a.get(x, y + dy, z)[0] == "minecraft:air":
                    raise AssertionError(f"Floating lantern ({hanging=}) at ({x},{y},{z}) in {a.piece_id}")

        for lec in a.lecterns:
            lx, ly, lz = lec["offset"]
            below = a.get(lx, ly - 1, lz)[0]
            if below == "minecraft:air":
                raise AssertionError(f"Floating lectern at ({lx},{ly},{lz}) in {a.piece_id}")

    # Verify Arrival Pad [-6..6] headroom in plaza_core
    plaza = next(p for p in pieces if p.piece_id == "plaza_core")
    for x in range(-6, 7):
        for z in range(-6, 7):
            if plaza.get(x, 0, z)[0] == "minecraft:air":
                raise AssertionError(f"Arrival pad hole at ({x}, 0, {z})")
            for y in range(1, 7):
                if plaza.get(x, y, z)[0] != "minecraft:air":
                    raise AssertionError(f"Arrival pad headroom blocked at ({x}, {y}, {z}) by {plaza.get(x, y, z)[0]}")

    min_x = min(p.x0 for p in pieces)
    min_y = min(p.y0 for p in pieces)
    min_z = min(p.z0 for p in pieces)
    max_x = max(p.x1 for p in pieces)
    max_y = max(p.y1 for p in pieces)
    max_z = max(p.z1 for p in pieces)
    return min_x, min_y, min_z, max_x, max_y, max_z


def build_all_pieces() -> List[PieceCanvas]:
    return [
        build_plaza_core(),
        build_heartroot_lower_se(),
        build_heartroot_trunk(),
        build_heartroot_canopy(),
        build_north_expedition_gate(),
        build_east_guild_hall(),
        build_west_nature_garden(),
        build_south_trading_pavilion(),
        build_cavern_descent_upper(),
        build_crystal_grotto_gallery(),
    ]


def main() -> None:
    valid_ids = load_mc263_valid_block_ids()
    pieces = build_all_pieces()
    env = verify_all_pieces(pieces, valid_ids)

    STRUCT_OUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Remove stale .nbt modules from previous non-compact layouts
    keep_names = {f"{p.piece_id}.nbt" for p in pieces}
    for old in STRUCT_OUT_DIR.glob("*.nbt"):
        if old.name not in keep_names:
            old.unlink()

    manifest_pieces = []
    total_non_air = 0
    for p in pieces:
        local_blocks = p.to_local_blocks()
        non_air = sum(1 for spec in local_blocks.values() if spec != AIR)
        total_non_air += non_air
        payload = encode_structure_nbt((p.sx, p.sy, p.sz), local_blocks)
        sha = hashlib.sha256(payload).hexdigest()[:16]
        out_nbt = STRUCT_OUT_DIR / f"{p.piece_id}.nbt"
        out_nbt.write_bytes(payload)
        manifest_pieces.append(
            {
                "id": p.piece_id,
                "template": f"canopycavern:server_spawn/{p.piece_id}",
                "role": p.role,
                "offset": [p.x0, p.y0, p.z0],
                "size": [p.sx, p.sy, p.sz],
                "excavateBelow": p.excavate_below,
                "foundationSkirt": p.foundation_skirt,
                "nonAirBlocks": non_air,
                "sha256Prefix": sha,
                "connections": p.connections,
                "signs": p.signs,
                "lecterns": p.lecterns,
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
        "envelopeMin": [env[0], env[1], env[2]],
        "envelopeMax": [env[3], env[4], env[5]],
        "supportedRotations": ["NONE", "CLOCKWISE_90", "CLOCKWISE_180", "COUNTERCLOCKWISE_90"],
        "pieces": manifest_pieces,
    }
    MANIFEST_OUT_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    span_x = env[3] - env[0] + 1
    span_y = env[4] - env[1] + 1
    span_z = env[5] - env[2] + 1
    total_signs = sum(len(p.signs) for p in pieces)
    total_lecterns = sum(len(p.lecterns) for p in pieces)
    print(
        f"Generated {len(pieces)} Canopy Sanctuary modules -> {span_x}x{span_y}x{span_z} "
        f"[{env[0]}..{env[3]}, {env[1]}..{env[4]}, {env[2]}..{env[5]}], "
        f"{total_non_air} non-air blocks, {total_signs} signs, {total_lecterns} lecterns."
    )


if __name__ == "__main__":
    main()
