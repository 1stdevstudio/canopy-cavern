#!/usr/bin/env python3
"""
Generates the 3 stacked modular NBT structure templates for canopycavern:elder_great_tree
(MC 26.3, DataVersion = 5023, <= 48x48x48 per piece):
  - root_hollow_base.nbt   (37x20x37, dy = -2..17)
  - mid_bough_bridges.nbt  (45x20x45, dy = 18..37)
  - crown_observatory.nbt  (39x18x39, dy = 38..55)
"""

from __future__ import annotations

import gzip
import math
import os
import struct
from pathlib import Path
from typing import Any

DATA_VERSION = 5023
LOOT_TABLE = "canopycavern:chests/elder_tree_hollow"

# Unified bounds aligned strictly with ElderTreePlan.java
PIECES = [
    ("root_hollow_base", (-18, 18), (-2, 17), (-18, 18)),
    ("mid_bough_bridges", (-22, 22), (18, 37), (-22, 22)),
    ("crown_observatory", (-19, 19), (38, 55), (-19, 19)),
]


class NbtList:
    """Typed NBT TAG_List wrapper so empty lists (e.g. entities) carry elem_type 10."""

    def __init__(self, elem_type: int, items: list[Any]) -> None:
        self.elem_type = elem_type
        self.items = items


def nbt_end() -> bytes:
    return b"\x00"


def nbt_str(s: str) -> bytes:
    raw = s.encode("utf-8")
    return struct.pack(">H", len(raw)) + raw


def nbt_tag_header(tag_type: int, name: str) -> bytes:
    return bytes([tag_type]) + nbt_str(name)


def nbt_encode_payload(val: Any) -> tuple[int, bytes]:
    if isinstance(val, int) and not isinstance(val, bool):
        return 3, struct.pack(">i", val)
    if isinstance(val, str):
        return 8, nbt_str(val)
    if isinstance(val, NbtList):
        buf = bytearray([val.elem_type]) + struct.pack(">i", len(val.items))
        for item in val.items:
            t, payload = nbt_encode_payload(item)
            assert t == val.elem_type
            buf.extend(payload)
        return 9, bytes(buf)
    if isinstance(val, list):
        if not val:
            return 9, bytes([0]) + struct.pack(">i", 0)
        elem_type, _ = nbt_encode_payload(val[0])
        buf = bytearray([elem_type]) + struct.pack(">i", len(val))
        for item in val:
            t, payload = nbt_encode_payload(item)
            assert t == elem_type
            buf.extend(payload)
        return 9, bytes(buf)
    if isinstance(val, dict):
        buf = bytearray()
        for k, v in val.items():
            t, payload = nbt_encode_payload(v)
            buf.extend(nbt_tag_header(t, k))
            buf.extend(payload)
        buf.extend(nbt_end())
        return 10, bytes(buf)
    raise TypeError(f"Unsupported NBT type: {type(val)}")


def write_nbt(path: Path, root: dict[str, Any]) -> None:
    _, payload = nbt_encode_payload(root)
    data = bytes([10]) + nbt_str("") + payload
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wb") as f:
        f.write(data)


def block_key(name: str, props: dict[str, str] | None = None, nbt: dict[str, Any] | None = None):
    prop_tuple = tuple(sorted(props.items())) if props else ()
    nbt_tuple = tuple(sorted(nbt.items())) if nbt else ()
    return (name, prop_tuple, nbt_tuple)


class MonumentCanvas:
    def __init__(self) -> None:
        self.blocks: dict[tuple[int, int, int], tuple[str, dict[str, str] | None, dict[str, Any] | None]] = {}

    def set(
        self,
        dx: int,
        dy: int,
        dz: int,
        name: str,
        props: dict[str, str] | None = None,
        nbt: dict[str, Any] | None = None,
        overwrite: bool = True,
    ) -> None:
        if dy < -2 or dy > 55:
            return
        if not overwrite and (dx, dy, dz) in self.blocks:
            return
        self.blocks[(dx, dy, dz)] = (name, props, nbt)

    def get_name(self, dx: int, dy: int, dz: int) -> str | None:
        entry = self.blocks.get((dx, dy, dz))
        return entry[0] if entry else None


def deterministic_hash(x: int, y: int, z: int) -> int:
    h = (x * 73856093) ^ (y * 19349663) ^ (z * 83492791)
    return abs(h)


def wrap_pi(angle: float) -> float:
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


def leaf_block(dx: int, dy: int, dz: int) -> tuple[str, dict[str, str]]:
    h = deterministic_hash(dx, dy, dz) % 10
    if h < 2:
        name = "minecraft:flowering_azalea_leaves"
    elif h < 7:
        name = "minecraft:azalea_leaves"
    else:
        name = "minecraft:oak_leaves"
    return name, {"distance": "1", "persistent": "true", "waterlogged": "false"}


def draw_sphere_or_disc(
    c: MonumentCanvas,
    cx: float,
    cy: float,
    cz: float,
    rx: float,
    ry: float,
    rz: float,
    block_fn,
    overwrite: bool = False,
) -> None:
    x0, x1 = int(math.floor(cx - rx)), int(math.ceil(cx + rx))
    y0, y1 = int(math.floor(cy - ry)), int(math.ceil(cy + ry))
    z0, z1 = int(math.floor(cz - rz)), int(math.ceil(cz + rz))
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                norm = ((x - cx) / max(0.5, rx)) ** 2 + ((y - cy) / max(0.5, ry)) ** 2 + ((z - cz) / max(0.5, rz)) ** 2
                if norm <= 1.0:
                    res = block_fn(x, y, z)
                    if res is not None:
                        c.set(x, y, z, res[0], res[1], None, overwrite=overwrite)


def bezier3(p0, p1, p2, t: float):
    u = 1.0 - t
    return (
        u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
        u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1],
        u * u * p0[2] + 2 * u * t * p1[2] + t * t * p2[2],
    )


def paint_limb(
    c: MonumentCanvas,
    p0,
    p1,
    p2,
    r_start: float,
    r_end: float,
    steps: int = 36,
    wood_fn=None,
) -> None:
    if wood_fn is None:
        def wood_fn(x, y, z):
            return ("minecraft:mangrove_wood" if deterministic_hash(x, y, z) % 7 == 0 else "minecraft:dark_oak_wood", None)

    for i in range(steps + 1):
        t = i / steps
        bx, by, bz = bezier3(p0, p1, p2, t)
        r = r_start * (1.0 - t) + r_end * t
        ri = int(math.ceil(r + 0.5))
        ix, iy, iz = int(round(bx)), int(round(by)), int(round(bz))
        for dx in range(-ri, ri + 1):
            for dy in range(-ri, ri + 1):
                for dz in range(-ri, ri + 1):
                    px, py, pz = ix + dx, iy + dy, iz + dz
                    dist = math.sqrt((px - bx) ** 2 + (py - by) ** 2 + (pz - bz) ** 2)
                    if dist <= r:
                        name, props = wood_fn(px, py, pz)
                        c.set(px, py, pz, name, props, None, overwrite=True)


def add_foliage_cluster(c: MonumentCanvas, cx: int, cy: int, cz: int, rx: float, ry: float, rz: float) -> None:
    def pick(x: int, y: int, z: int):
        # Slightly ragged natural outer silhouette
        if deterministic_hash(x, y, z) % 11 == 0 and abs(y - cy) >= ry - 0.8:
            return None
        return leaf_block(x, y, z)

    draw_sphere_or_disc(c, cx, cy, cz, rx, ry, rz, pick, overwrite=False)
    # Occasional underside vine or moss carpet
    for dx in range(int(-rx + 1), int(rx)):
        for dz in range(int(-rz + 1), int(rz)):
            if (dx * dx + dz * dz) > (rx * 0.8) ** 2:
                continue
            h = deterministic_hash(cx + dx, cy, cz + dz)
            top_y = int(round(cy + ry))
            if h % 13 == 0 and c.get_name(cx + dx, top_y, cz + dz) in (
                "minecraft:azalea_leaves",
                "minecraft:flowering_azalea_leaves",
                "minecraft:oak_leaves",
            ) and c.get_name(cx + dx, top_y + 1, cz + dz) is None:
                c.set(cx + dx, top_y + 1, cz + dz, "minecraft:moss_carpet", None, None, overwrite=False)
            if h % 19 == 0:
                hang_y = int(round(cy - ry))
                if c.get_name(cx + dx, hang_y + 1, cz + dz) and c.get_name(cx + dx, hang_y, cz + dz) is None:
                    if h % 38 == 0:
                        c.set(cx + dx, hang_y, cz + dz, "minecraft:spore_blossom", None, None, overwrite=False)
                    else:
                        length = 1 + (h % 3)
                        for v in range(length):
                            vy = hang_y - v
                            if vy <= 18 or c.get_name(cx + dx, vy, cz + dz) is not None:
                                break
                            if v < length - 1:
                                c.set(cx + dx, vy, cz + dz, "minecraft:cave_vines_plant", {"berries": "false"}, None, overwrite=False)
                            else:
                                c.set(
                                    cx + dx,
                                    vy,
                                    cz + dz,
                                    "minecraft:cave_vines",
                                    {"age": "10", "berries": "true" if h % 3 == 0 else "false"},
                                    None,
                                    overwrite=False,
                                )


def build_trunk_and_hollow_shell(c: MonumentCanvas) -> None:
    for dy in range(-2, 49):
        if dy <= 8:
            base_out = 5.4 + 0.35 * (8 - dy)
        elif dy <= 41:
            base_out = 5.2 - 0.015 * (dy - 9)
        else:
            base_out = 4.7 + 0.52 * (dy - 41)

        r_in = 4.2 if 0 <= dy <= 6 else (3.2 if 7 <= dy <= 47 else 8.5)
        max_r = int(math.ceil(base_out + 2.2))

        for dx in range(-max_r, max_r + 1):
            for dz in range(-max_r, max_r + 1):
                r = math.hypot(dx, dz)
                theta = math.atan2(dz, dx)
                rib = 1.15 * math.cos(5.0 * theta + 0.07 * dy) + 0.55 * math.sin(3.0 * theta - 0.05 * dy)
                r_out = max(r_in + 1.4, base_out + rib)

                if r <= r_out:
                    if dy < 0:
                        # Foundation floor beneath ground chamber
                        if r <= r_in + 0.3 and dy == -1:
                            h = deterministic_hash(dx, dy, dz) % 7
                            mat = "minecraft:mossy_cobblestone" if h < 2 else ("minecraft:dark_oak_planks" if h < 5 else "minecraft:moss_block")
                            c.set(dx, dy, dz, mat)
                        else:
                            c.set(dx, dy, dz, "minecraft:dark_oak_wood")
                    elif dy == 48 and r <= 7.8:
                        # Crown observatory floor deck
                        if r <= 3.1:
                            c.set(dx, dy, dz, "minecraft:air")
                        else:
                            h = deterministic_hash(dx, dy, dz) % 9
                            mat = "minecraft:moss_block" if h == 0 else ("minecraft:spruce_planks" if h % 3 == 0 else "minecraft:dark_oak_planks")
                            c.set(dx, dy, dz, mat)
                    elif r <= r_in:
                        c.set(dx, dy, dz, "minecraft:air")
                    else:
                        h = deterministic_hash(dx, dy, dz) % 18
                        if r <= r_in + 1.05:
                            mat = "minecraft:stripped_dark_oak_wood" if h < 14 else "minecraft:dark_oak_wood"
                        elif dy <= 9 and h < 3:
                            mat = "minecraft:mangrove_wood"
                        elif r >= r_out - 0.85 and h == 4 and dy >= 1:
                            mat = "minecraft:moss_block"
                        else:
                            mat = "minecraft:dark_oak_wood"
                        c.set(dx, dy, dz, mat)


def build_arching_roots(c: MonumentCanvas) -> None:
    # 4 grand diagonal arching roots + 4 low twisting buttresses avoiding cardinal doors
    angles_grand = [math.pi * 0.25 + k * math.pi * 0.5 for k in range(4)]
    for a in angles_grand:
        ca, sa = math.cos(a), math.sin(a)
        p0 = (ca * 4.4, 7.5, sa * 4.4)
        p1 = (ca * 10.5, 9.5, sa * 10.5)
        p2 = (ca * 15.2, 0.0, sa * 15.2)
        paint_limb(c, p0, p1, p2, r_start=2.05, r_end=1.25, steps=34)
        # Solid ground-contact root pier right down to dy=-2 for ElderTreeStructure anchoring
        tx, tz = int(round(ca * 15.2)), int(round(sa * 15.2))
        for px in range(tx - 1, tx + 2):
            for pz in range(tz - 1, tz + 2):
                if abs(px) <= 17 and abs(pz) <= 17 and (px - tx) ** 2 + (pz - tz) ** 2 <= 2:
                    for ry in range(-2, 2):
                        c.set(px, ry, pz, "minecraft:dark_oak_wood")
                    c.set(px, 2, pz, "minecraft:moss_carpet", overwrite=False)

        # Anchor under outer knee so arches never float oddly on flat ground
        kx, kz = int(round(ca * 12.2)), int(round(sa * 12.2))
        for ry in range(-2, 4):
            c.set(kx, ry, kz, "minecraft:mangrove_roots" if ry == 3 else "minecraft:dark_oak_wood")

    angles_low = [0.42 + k * (math.pi * 0.5) for k in range(4)]
    for a in angles_low:
        ca, sa = math.cos(a), math.sin(a)
        p0 = (ca * 5.2, 4.2, sa * 5.2)
        p1 = (ca * 9.5, 3.8, sa * 9.5)
        p2 = (ca * 13.0, -1.5, sa * 13.0)
        paint_limb(c, p0, p1, p2, r_start=1.6, r_end=1.0, steps=24)
        tx, tz = int(round(ca * 13.0)), int(round(sa * 13.0))
        for px in range(tx - 1, tx + 2):
            for pz in range(tz - 1, tz + 2):
                if (px - tx) ** 2 + (pz - tz) ** 2 <= 1:
                    for ry in range(-2, 0):
                        c.set(px, ry, pz, "minecraft:dark_oak_wood")


def build_mid_boughs_and_canopy(c: MonumentCanvas) -> None:
    boughs = [
        # (p0, p1, p2, r0, r1, foliage_centers)
        ((3, 21, 3), (8, 21, 8), (16, 25, 16), 1.95, 1.1, [(17, 29, 17, 4.5, 2.5, 4.5)]),
        ((-3, 24, -2), (-10, 28, -8), (-17, 32, -14), 1.9, 1.0, [(-17, 34, -14, 4.8, 2.6, 4.8), (-12, 32, -7, 4.0, 2.3, 4.0)]),
        ((2, 26, -3), (9, 29, -9), (16, 33, -15), 1.85, 0.95, [(16, 34, -15, 4.8, 2.6, 4.8), (11, 32, -10, 4.2, 2.4, 4.2)]),
        ((-4, 27, 1), (-11, 29, 2), (-17, 33, 6), 1.85, 0.95, [(-17, 34, 6, 4.8, 2.6, 4.8), (-13, 33, 10, 4.0, 2.3, 4.0)]),
        ((3, 28, 1), (10, 31, -2), (17, 34, -4), 1.75, 0.9, [(17, 35, -4, 4.6, 2.5, 4.6)]),
        ((-1, 25, 4), (-7, 29, 11), (-13, 33, 17), 1.8, 0.9, [(-13, 34, 17, 4.6, 2.5, 4.6)]),
    ]
    for p0, p1, p2, r0, r1, leaves in boughs:
        paint_limb(c, p0, p1, p2, r0, r1, steps=30)
        for lx, ly, lz, rx, ry, rz in leaves:
            add_foliage_cluster(c, lx, ly, lz, rx, ry, rz)

    # Secondary fork off bough 2 & bough 3 inside mid_bough_bridges (dy=29..36, |dx|,|dz|<=21)
    paint_limb(c, (-11, 29, -8), (-14, 32, -4), (-16, 33, -2), 1.15, 0.75, steps=16)
    add_foliage_cluster(c, -16, 35, -2, 3.8, 2.2, 3.8)
    paint_limb(c, (10, 30, -9), (13, 32, -12), (14, 33, -8), 1.1, 0.75, steps=16)

    # Bee nests hung cleanly under leaf clusters
    c.set(-15, 32, -12, "minecraft:bee_nest", {"facing": "south", "honey_level": "3"}, overwrite=True)
    c.set(14, 32, -13, "minecraft:bee_nest", {"facing": "west", "honey_level": "2"}, overwrite=True)


def build_crown_observatory_and_canopy(c: MonumentCanvas) -> None:
    # 4 sweeping crown canopy limbs rising from observatory rim out to wide green dome (dy=49..55, |x|,|z|<=18)
    crown_angles = [0.3 + k * (math.pi * 0.5) for k in range(4)]
    for idx, a in enumerate(crown_angles):
        ca, sa = math.cos(a), math.sin(a)
        p0 = (ca * 6.5, 48.0, sa * 6.5)
        p1 = (ca * 11.5, 51.0, sa * 11.5)
        p2 = (ca * 14.5, 53.0, sa * 14.5)
        paint_limb(c, p0, p1, p2, 1.55, 0.85, steps=22)
        cx, cz = int(round(ca * 13.0)), int(round(sa * 13.0))
        add_foliage_cluster(c, cx, 52, cz, 5.2, 2.5, 5.2)
        # Overarching vaulted chandelier ribs meeting above central chandelier (dy=54)
        rib_p0 = (ca * 7.2, 48.5, sa * 7.2)
        rib_p1 = (ca * 4.0, 54.0, sa * 4.0)
        rib_p2 = (0.0, 54.0, 0.0)
        paint_limb(c, rib_p0, rib_p1, rib_p2, 1.0, 0.75, steps=16)

    # Grand topmost domed leaf crown (kept above dy=53 so observatory deck stays open & airy!)
    add_foliage_cluster(c, 0, 54, 0, 9.0, 1.4, 9.0)
    # Clear air inside observatory room below chandelier (dy = 49..52, r <= 6.8)
    for dy in range(49, 53):
        for dx in range(-7, 8):
            for dz in range(-7, 8):
                if math.hypot(dx, dz) <= 6.8:
                    c.set(dx, dy, dz, "minecraft:air")

    # Railing & lanterns around observatory deck edge (dy=49)
    for dx in range(-8, 9):
        for dz in range(-8, 9):
            r = math.hypot(dx, dz)
            if 7.0 <= r <= 7.85:
                if abs(dx) == abs(dz) or (abs(dx) == 0 and abs(dz) == 7) or (abs(dz) == 0 and abs(dx) == 7):
                    c.set(dx, 49, dz, "minecraft:dark_oak_wood")
                    c.set(dx, 50, dz, "minecraft:lantern", {"hanging": "false", "waterlogged": "false"})
                else:
                    c.set(dx, 49, dz, "minecraft:dark_oak_fence", {"waterlogged": "false"})

    # Chandelier hanging safely high at dy=52..54
    c.set(0, 54, 0, "minecraft:dark_oak_wood")
    c.set(0, 53, 0, "minecraft:iron_chain", {"axis": "y", "waterlogged": "false"})
    c.set(0, 52, 0, "minecraft:ochre_froglight")
    c.set(0, 51, 0, "minecraft:spore_blossom")

    # Decorative moss benches on observatory deck
    for dx, dz in [(-4, -3), (-4, 3), (4, -3), (4, 3)]:
        c.set(dx, 49, dz, "minecraft:moss_block")
        c.set(dx, 50, dz, "minecraft:moss_carpet")


def build_core_and_spiral_staircase(c: MonumentCanvas) -> None:
    # Carve clean ground hall + core shaft before placing spiral stairs
    for dy in range(0, 49):
        clear_r = 4.1 if dy <= 6 else 3.1
        ri = int(math.ceil(clear_r))
        for dx in range(-ri, ri + 1):
            for dz in range(-ri, ri + 1):
                if math.hypot(dx, dz) <= clear_r:
                    c.set(dx, dy, dz, "minecraft:air")

    # Central glowing core axis pillar (dy = 0..47, NOT blocking observatory center at 48+)
    for dy in range(0, 48):
        if dy in (5, 13, 21, 29, 37, 45):
            c.set(0, dy, 0, "minecraft:ochre_froglight")
        else:
            c.set(0, dy, 0, "minecraft:stripped_dark_oak_wood")

    # Smooth 0.5-block spiral slab staircase (h = 1..97 covers y = 0.5 .. 48.5!)
    # Rate: ~11 deg/half-step -> 32.7 half-steps = ~16.3 vertical blocks per 360 turn -> ~14 blocks headroom!
    rate = math.pi / 16.0
    for h in range(1, 98):
        dy = h // 2
        slab_type = "bottom" if (h % 2 == 0) else "top"
        target_angle = -0.3 + h * rate
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                r = math.hypot(dx, dz)
                if not (1.05 <= r <= 3.05):
                    continue
                dtheta = abs(wrap_pi(math.atan2(dz, dx) - target_angle))
                if dtheta <= 0.34:
                    c.set(
                        dx,
                        dy,
                        dz,
                        "minecraft:spruce_slab",
                        {"type": slab_type, "waterlogged": "false"},
                        overwrite=True,
                    )
                    # Guarantee 3 clear air blocks strictly above every placed stair voxel
                    for air_dy in (dy + 1, dy + 2, dy + 3):
                        if air_dy <= 51 and c.get_name(dx, air_dy, dz) != "minecraft:spruce_slab":
                            c.set(dx, air_dy, dz, "minecraft:air", overwrite=True)

    # Smooth entry step at ground level y=0 connecting ground floor to h=1
    for dx in range(1, 4):
        c.set(dx, 0, 0, "minecraft:spruce_slab", {"type": "bottom", "waterlogged": "false"}, overwrite=True)


def build_doorways_and_interior_rooms(c: MonumentCanvas) -> None:
    # 4 cardinal doorways through base wall (dy=0..3) + mossy cobble paths
    cardinals = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    for fx, fz in cardinals:
        px, pz = -fz, fx
        for dist in range(3, 10):
            for w in (-1, 0, 1):
                cx = fx * dist + px * w
                cz = fz * dist + pz * w
                # Floor stone
                c.set(cx, -1, cz, "minecraft:mossy_cobblestone" if (dist + w) % 2 == 0 else "minecraft:dark_oak_planks")
                # Arched doorway clearance (wider in middle, vaulted at dy=3 center)
                max_h = 3 if w == 0 else 2
                for ay in range(0, max_h + 1):
                    c.set(cx, ay, cz, "minecraft:air")
                if dist == 6 and w == 0:
                    c.set(cx, 3, cz, "minecraft:lantern", {"hanging": "true", "waterlogged": "false"})
                    c.set(cx, 4, cz, "minecraft:dark_oak_wood")

    # Ground Sanctuary alcoves & Chest #1 (at diagonal (-3, 0, -2) away from doors & start stairs)
    c.set(-3, 0, -2, "minecraft:chest", {"facing": "south", "type": "single", "waterlogged": "false"}, nbt={"id": "minecraft:chest", "LootTable": LOOT_TABLE})
    c.set(-2, 0, -3, "minecraft:bookshelf")
    c.set(-3, 1, -3, "minecraft:potted_flowering_azalea_bush")
    c.set(3, 0, -3, "minecraft:barrel", {"facing": "up", "open": "false"})
    c.set(3, 1, -3, "minecraft:lantern", {"hanging": "false", "waterlogged": "false"})
    c.set(-3, 0, 3, "minecraft:flowering_azalea")
    for dx, dz in [(-2, 2), (2, 2), (-2, -1), (1, -2)]:
        c.set(dx, 0, dz, "minecraft:moss_carpet", overwrite=False)

    # Mid-level Botanist Study Pod at (11, 20, 11) connected right off spiral azimuth (~61 deg) at dy=19..20
    # Curved walkway from (3, 19, 3) -> (8, 20, 8) -> Study
    for step in range(3, 11):
        cx, cz = step, step
        wy = 19 if step <= 4 else 20
        for ox, oz in [(0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)]:
            wx, wz = cx + ox, cz + oz
            c.set(wx, wy, wz, "minecraft:dark_oak_planks")
            for ay in range(wy + 1, wy + 5):
                c.set(wx, ay, wz, "minecraft:air")

    # Study Cabin Shell centered at (11, 20, 11)
    sx, sz = 11, 11
    for dy in range(20, 27):
        for dx in range(sx - 4, sx + 5):
            for dz in range(sz - 4, sz + 5):
                dist = math.hypot(dx - sx, dz - sz)
                if dy == 20 and dist <= 3.8:
                    c.set(dx, dy, dz, "minecraft:spruce_planks" if dist <= 2.2 else "minecraft:dark_oak_planks")
                elif 21 <= dy <= 24:
                    if dist <= 2.9:
                        c.set(dx, dy, dz, "minecraft:air")
                    elif dist <= 3.9:
                        # Open scenic window strips at dy=22 facing N/E/S/W
                        if dy == 22 and (abs(dx - sx) <= 1 or abs(dz - sz) <= 1) and not (dx < sx and dz < sz):
                            c.set(dx, dy, dz, "minecraft:oak_fence", {"waterlogged": "false"})
                        else:
                            c.set(dx, dy, dz, "minecraft:stripped_dark_oak_wood" if (dx + dz) % 3 == 0 else "minecraft:dark_oak_wood")
                elif dy == 25 and dist <= 4.1:
                    c.set(dx, dy, dz, "minecraft:dark_oak_wood" if dist >= 2.2 else "minecraft:moss_block")
                elif dy == 26 and dist <= 2.6:
                    c.set(dx, dy, dz, "minecraft:moss_block")

    # Botanist Study furnishings & Chest #2
    c.set(sx + 2, 21, sz + 1, "minecraft:chest", {"facing": "west", "type": "single", "waterlogged": "false"}, nbt={"id": "minecraft:chest", "LootTable": LOOT_TABLE})
    c.set(sx + 1, 21, sz + 2, "minecraft:bookshelf")
    c.set(sx + 1, 22, sz + 2, "minecraft:potted_flowering_azalea_bush")
    c.set(sx - 1, 21, sz + 2, "minecraft:lectern", {"facing": "north", "has_book": "false", "powered": "false"})
    c.set(sx + 2, 21, sz - 1, "minecraft:brewing_stand")
    c.set(sx, 24, sz, "minecraft:shroomlight")
    c.set(sx, 23, sz, "minecraft:lantern", {"hanging": "true", "waterlogged": "false"})

    # Suspension Bridge A: Trunk (-3, 25, 0) [spiral azimuth ~196 deg] -> West Bough (-15, 28, 5)
    for t_step in range(13):
        t = t_step / 12.0
        bx = -3 - 12 * t
        bz = round(5 * t)
        sag_y = round(25.0 + 3.0 * t - 1.2 * math.sin(math.pi * t))
        ix, iz = int(round(bx)), int(bz)
        for wz in range(iz - 1, iz + 2):
            c.set(ix, sag_y, wz, "minecraft:spruce_slab" if abs(wz - iz) == 0 else "minecraft:dark_oak_planks", {"type": "bottom", "waterlogged": "false"} if abs(wz - iz) == 0 else None)
            for ay in range(sag_y + 1, sag_y + 4):
                c.set(ix, ay, wz, "minecraft:air")
            if abs(wz - iz) == 1 and t_step % 3 == 0:
                c.set(ix, sag_y + 1, wz, "minecraft:oak_fence", {"waterlogged": "false"})
                if t_step in (3, 9):
                    c.set(ix, sag_y + 2, wz, "minecraft:lantern", {"hanging": "false", "waterlogged": "false"})

    # Suspension Bridge B: Trunk (0, 29, -3) [spiral azimuth ~275 deg] -> NE/N Bough (8, 31, -11)
    for t_step in range(11):
        t = t_step / 10.0
        bx = round(8 * t)
        bz = round(-3 - 8 * t)
        sag_y = round(29.0 + 2.0 * t - 1.2 * math.sin(math.pi * t))
        ix, iz = int(bx), int(bz)
        for wx, wz in [(ix, iz), (ix + 1, iz), (ix, iz - 1)]:
            c.set(wx, sag_y, wz, "minecraft:spruce_planks")
            for ay in range(sag_y + 1, sag_y + 4):
                c.set(wx, ay, wz, "minecraft:air")
        if t_step % 3 == 0:
            c.set(ix + 1, sag_y + 1, iz, "minecraft:oak_fence", {"waterlogged": "false"})
            c.set(ix + 1, sag_y + 2, iz, "minecraft:iron_chain", {"axis": "y", "waterlogged": "false"})


def _connects_wood_fence(neighbor: str | None) -> bool:
    if not neighbor:
        return False
    if neighbor.endswith("_fence") or neighbor.endswith("_fence_gate"):
        return neighbor != "minecraft:nether_brick_fence"
    return neighbor in {
        "minecraft:dark_oak_wood",
        "minecraft:stripped_dark_oak_wood",
        "minecraft:mangrove_wood",
        "minecraft:dark_oak_planks",
        "minecraft:spruce_planks",
        "minecraft:moss_block",
        "minecraft:bookshelf",
    }


def _resolve_block_props(c: MonumentCanvas, dx: int, dy: int, dz: int, bname: str, props: dict[str, str] | None) -> dict[str, str] | None:
    if not bname.endswith("_fence"):
        return dict(props) if props else None
    resolved = dict(props) if props else {}
    for dir_name, ox, oz in (("north", 0, -1), ("south", 0, 1), ("east", 1, 0), ("west", -1, 0)):
        resolved[dir_name] = "true" if _connects_wood_fence(c.get_name(dx + ox, dy, dz + oz)) else "false"
    resolved.setdefault("waterlogged", "false")
    return resolved


def slice_and_export(c: MonumentCanvas, out_dir: Path) -> None:
    chests_found = 0
    for name, (min_x, max_x), (min_y, max_y), (min_z, max_z) in PIECES:
        size_x = max_x - min_x + 1
        size_y = max_y - min_y + 1
        size_z = max_z - min_z + 1
        assert size_x <= 48 and size_y <= 48 and size_z <= 48, f"{name} exceeds 48 cube"

        palette_index: dict[Any, int] = {}
        palette_list: list[dict[str, Any]] = []
        block_list: list[dict[str, Any]] = []

        for (dx, dy, dz), (bname, props, bnbt) in sorted(c.blocks.items()):
            if not (min_y <= dy <= max_y):
                continue
            assert min_x <= dx <= max_x and min_z <= dz <= max_z, (
                f"Block {(dx, dy, dz)} ({bname}) in vertical slice {name} escaped XZ bounds {(min_x, max_x)}x{(min_z, max_z)}"
            )
            if bname == "minecraft:chest":
                chests_found += 1
            resolved_props = _resolve_block_props(c, dx, dy, dz, bname, props)
            key = block_key(bname, resolved_props, None)
            idx = palette_index.get(key)
            if idx is None:
                idx = len(palette_list)
                palette_index[key] = idx
                # MC 26.3 StructureTemplate/NbtUtils expects lowercase "id" and "properties".
                entry: dict[str, Any] = {"id": bname}
                if resolved_props:
                    entry["properties"] = resolved_props
                palette_list.append(entry)

            lx = dx - min_x
            ly = dy - min_y
            lz = dz - min_z
            b_entry: dict[str, Any] = {"pos": [lx, ly, lz], "state": idx}
            if bnbt:
                b_entry["nbt"] = dict(bnbt)
            block_list.append(b_entry)

        root = {
            "DataVersion": DATA_VERSION,
            "size": [size_x, size_y, size_z],
            "palette": NbtList(10, palette_list),
            "blocks": NbtList(10, block_list),
            "entities": NbtList(10, []),
        }
        out_path = out_dir / f"{name}.nbt"
        write_nbt(out_path, root)
        print(f"Wrote {out_path}: size={size_x}x{size_y}x{size_z}, palette={len(palette_list)}, blocks={len(block_list)}")

    assert chests_found == 2, f"Expected 2 loot chests, found {chests_found}"


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    out_dir = repo_root / "src/main/resources/data/canopycavern/structure/elder_great_tree"
    canvas = MonumentCanvas()
    build_trunk_and_hollow_shell(canvas)
    build_arching_roots(canvas)
    build_mid_boughs_and_canopy(canvas)
    build_crown_observatory_and_canopy(canvas)
    build_core_and_spiral_staircase(canvas)
    build_doorways_and_interior_rooms(canvas)
    slice_and_export(canvas, out_dir)
    print("Self-validation passed: bounds <= 48, 0 out-of-bounds blocks, 2 loot chests verified.")


if __name__ == "__main__":
    main()
