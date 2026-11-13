#!/usr/bin/env python3
from __future__ import annotations
"""
Generates architecturally detailed multi-piece Jigsaw exploration structures
and 4 themed Villager Civilizations (with Villagers, Iron Golems, and
canopycavern:village_sentinel guards) for Canopy Cavern v0.3.0.
"""

import gzip
import json
import random
import struct
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "src/main/resources/data/canopycavern"
STRUCT_DIR = DATA / "structure"

# Tag constants for big-endian NBT serialization
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


class NbtTyped:
    def __init__(self, tag_type: int, value, elem_type: int | None = None):
        self.tag_type = tag_type
        self.value = value
        self.elem_type = elem_type


def nbt_byte(v): return NbtTyped(TAG_BYTE, int(v))
def nbt_int(v): return NbtTyped(TAG_INT, int(v))
def nbt_float(v): return NbtTyped(TAG_FLOAT, float(v))
def nbt_double(v): return NbtTyped(TAG_DOUBLE, float(v))
def nbt_str(v): return NbtTyped(TAG_STRING, str(v))
def nbt_list(elem_t, items): return NbtTyped(TAG_LIST, list(items), elem_t)
def nbt_int_list(vals): return nbt_list(TAG_INT, [int(x) for x in vals])
def nbt_double_list(vals): return nbt_list(TAG_DOUBLE, [float(x) for x in vals])
def nbt_float_list(vals): return nbt_list(TAG_FLOAT, [float(x) for x in vals])
def nbt_int_array(vals): return NbtTyped(TAG_INT_ARRAY, [int(x) for x in vals])


def encode_nbt_payload(buf: bytearray, tag_type: int, val, elem_type=None):
    if tag_type == TAG_BYTE:
        buf.extend(struct.pack(">b", val))
    elif tag_type == TAG_SHORT:
        buf.extend(struct.pack(">h", val))
    elif tag_type == TAG_INT:
        buf.extend(struct.pack(">i", val))
    elif tag_type == TAG_LONG:
        buf.extend(struct.pack(">q", val))
    elif tag_type == TAG_FLOAT:
        buf.extend(struct.pack(">f", val))
    elif tag_type == TAG_DOUBLE:
        buf.extend(struct.pack(">d", val))
    elif tag_type == TAG_STRING:
        raw = val.encode("utf-8")
        buf.extend(struct.pack(">H", len(raw)))
        buf.extend(raw)
    elif tag_type == TAG_INT_ARRAY:
        buf.extend(struct.pack(">i", len(val)))
        for x in val:
            buf.extend(struct.pack(">i", x))
    elif tag_type == TAG_LIST:
        et = elem_type if elem_type is not None else (TAG_COMPOUND if val and isinstance(val[0], dict) else TAG_END)
        buf.append(et)
        buf.extend(struct.pack(">i", len(val)))
        for item in val:
            encode_nbt_payload(buf, et, item)
    elif tag_type == TAG_COMPOUND:
        for k, v in val.items():
            if isinstance(v, NbtTyped):
                buf.append(v.tag_type)
                kb = k.encode("utf-8")
                buf.extend(struct.pack(">H", len(kb)))
                buf.extend(kb)
                encode_nbt_payload(buf, v.tag_type, v.value, v.elem_type)
            elif isinstance(v, dict):
                buf.append(TAG_COMPOUND)
                kb = k.encode("utf-8")
                buf.extend(struct.pack(">H", len(kb)))
                buf.extend(kb)
                encode_nbt_payload(buf, TAG_COMPOUND, v)
            elif isinstance(v, str):
                buf.append(TAG_STRING)
                kb = k.encode("utf-8")
                buf.extend(struct.pack(">H", len(kb)))
                buf.extend(kb)
                encode_nbt_payload(buf, TAG_STRING, v)
            elif isinstance(v, int):
                buf.append(TAG_INT)
                kb = k.encode("utf-8")
                buf.extend(struct.pack(">H", len(kb)))
                buf.extend(kb)
                encode_nbt_payload(buf, TAG_INT, v)
            elif isinstance(v, float):
                buf.append(TAG_DOUBLE)
                kb = k.encode("utf-8")
                buf.extend(struct.pack(">H", len(kb)))
                buf.extend(kb)
                encode_nbt_payload(buf, TAG_DOUBLE, v)
            else:
                raise TypeError(f"Unsupported value {type(v)} for {k}")
        buf.append(TAG_END)


def write_nbt(rel_path: str, compound: dict):
    out = STRUCT_DIR / rel_path
    out.parent.mkdir(parents=True, exist_ok=True)
    buf = bytearray()
    buf.append(TAG_COMPOUND)
    buf.extend(struct.pack(">H", 0))  # empty root name
    encode_nbt_payload(buf, TAG_COMPOUND, compound)
    out.write_bytes(gzip.compress(bytes(buf)))


class StructureBuilder:
    def __init__(self, sx: int, sy: int, sz: int, fill_block: str = "minecraft:air"):
        self.sx, self.sy, self.sz = sx, sy, sz
        self.grid = {}
        self.block_nbts = {}
        self.entities = []
        if fill_block:
            for x in range(sx):
                for y in range(sy):
                    for z in range(sz):
                        self.set(x, y, z, fill_block)

    def _norm(self, spec):
        if isinstance(spec, tuple):
            bid, props = spec
            return (bid, tuple(sorted(props.items())))
        return (spec, ())

    def set(self, x: int, y: int, z: int, spec, nbt: dict | None = None):
        if not (0 <= x < self.sx and 0 <= y < self.sy and 0 <= z < self.sz):
            return
        self.grid[(x, y, z)] = self._norm(spec)
        if nbt is not None:
            self.block_nbts[(x, y, z)] = nbt
        elif (x, y, z) in self.block_nbts:
            del self.block_nbts[(x, y, z)]

    def fill(self, x0: int, y0: int, z0: int, x1: int, y1: int, z1: int, spec):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    self.set(x, y, z, spec)

    def hollow_box(self, x0: int, y0: int, z0: int, x1: int, y1: int, z1: int, wall_spec, fill_spec="minecraft:air"):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    if x in (x0, x1) or y in (y0, y1) or z in (z0, z1):
                        self.set(x, y, z, wall_spec)
                    elif fill_spec is not None:
                        self.set(x, y, z, fill_spec)

    def chest(self, x: int, y: int, z: int, facing: str, loot_table: str):
        self.set(
            x, y, z,
            ("minecraft:chest", {"facing": facing, "type": "single", "waterlogged": "false"}),
            {"id": "minecraft:chest", "LootTable": loot_table},
        )

    def jigsaw(self, x: int, y: int, z: int, orientation: str, name: str, target: str, pool: str, final_state: str, joint: str = "aligned"):
        self.set(
            x, y, z,
            ("minecraft:jigsaw", {"orientation": orientation}),
            {
                "id": "minecraft:jigsaw",
                "joint": joint,
                "name": name,
                "target": target,
                "pool": pool,
                "final_state": final_state,
            },
        )

    def stairs(self, x: int, y: int, z: int, block_id: str, facing: str, half: str = "bottom", shape: str = "straight"):
        self.set(x, y, z, (block_id, {"facing": facing, "half": half, "shape": shape, "waterlogged": "false"}))

    def slab(self, x: int, y: int, z: int, block_id: str, kind: str = "bottom"):
        self.set(x, y, z, (block_id, {"type": kind, "waterlogged": "false"}))

    def door(self, x: int, y: int, z: int, block_id: str, facing: str):
        self.set(x, y, z, (block_id, {"facing": facing, "half": "lower", "hinge": "left", "open": "false", "powered": "false"}))
        self.set(x, y + 1, z, (block_id, {"facing": facing, "half": "upper", "hinge": "left", "open": "false", "powered": "false"}))

    def bed(self, x: int, y: int, z: int, color_bed: str, facing: str):
        dx, dz = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[facing]
        self.set(x, y, z, (color_bed, {"facing": facing, "occupied": "false", "part": "foot"}))
        self.set(x + dx, y, z + dz, (color_bed, {"facing": facing, "occupied": "false", "part": "head"}))

    def lantern(self, x: int, y: int, z: int, hanging: bool = False):
        self.set(x, y, z, ("minecraft:lantern", {"hanging": "true" if hanging else "false", "waterlogged": "false"}))

    def add_entity(self, x: float, y: float, z: float, entity_id: str, extra_nbt: dict | None = None):
        rng = random.Random(hash((entity_id, x, y, z, len(self.entities))))
        uuid_ints = [rng.randint(-2**31, 2**31 - 1) for _ in range(4)]
        bx, by, bz = int(x), int(y), int(z)
        nbt = {
            "id": entity_id,
            "PersistenceRequired": nbt_byte(1),
            "UUID": nbt_int_array(uuid_ints),
            "OnGround": nbt_byte(1),
        }
        if extra_nbt:
            nbt.update(extra_nbt)
        self.entities.append({
            "blockPos": nbt_int_list([bx, by, bz]),
            "pos": nbt_double_list([x, y, z]),
            "nbt": nbt,
        })

    @staticmethod
    def _is_full_face_solid(bid: str) -> bool:
        if not bid:
            return False
        name = bid.split(":")[-1]
        if bid in (
            "minecraft:air", "minecraft:cave_air", "minecraft:void_air",
            "minecraft:structure_void", "minecraft:water", "minecraft:lava",
            "minecraft:iron_bars", "minecraft:iron_chain", "minecraft:chain",
            "minecraft:lightning_rod", "minecraft:end_rod", "minecraft:conduit",
            "minecraft:stonecutter", "minecraft:lectern", "minecraft:enchanting_table",
            "minecraft:brewing_stand", "minecraft:grindstone", "minecraft:anvil",
            "minecraft:chipped_anvil", "minecraft:damaged_anvil", "minecraft:cauldron",
            "minecraft:hopper", "minecraft:bell", "minecraft:ladder",
            "minecraft:lantern", "minecraft:soul_lantern", "minecraft:campfire",
            "minecraft:soul_campfire", "minecraft:sea_pickle", "minecraft:kelp",
            "minecraft:kelp_plant", "minecraft:seagrass", "minecraft:tall_seagrass",
            "minecraft:flower_pot", "minecraft:fern", "minecraft:azalea",
            "minecraft:flowering_azalea", "minecraft:sweet_berry_bush",
        ):
            return False
        partial_suffixes = (
            "_pane", "_fence", "_fence_gate", "_wall", "_door", "_trapdoor",
            "_stairs", "_slab", "_carpet", "_bed", "_chest", "_torch",
            "_button", "_pressure_plate", "_sign", "_hanging_sign", "_banner",
            "_candle", "_rail", "_coral", "_coral_fan", "_sapling", "_head",
            "_skull", "_cluster", "_amethyst_bud", "_vines", "_vines_plant",
        )
        if name.endswith(partial_suffixes) or name.startswith("potted_"):
            return False
        if name in (
            "cornflower", "poppy", "dandelion", "blue_orchid", "allium", "azure_bluet",
            "oxeye_daisy", "lily_of_the_valley", "white_tulip", "pink_tulip",
            "red_tulip", "orange_tulip", "short_grass", "tall_grass", "large_fern",
            "dead_bush", "moss_carpet", "snow", "lever", "tripwire_hook", "tripwire",
            "redstone_wire", "repeater", "comparator", "glow_lichen", "sculk_vein",
            "vine", "pointed_dripstone", "cake", "bamboo", "sugar_cane", "lilac",
            "rose_bush", "peony", "sunflower", "spawner", "mob_spawner",
        ):
            return False
        return True

    def _compute_connected_props(self, x: int, y: int, z: int, bid: str, props: tuple):
        pdict = {k: v for k, v in props} if props else {}
        dirs = (("north", 0, -1), ("south", 0, 1), ("east", 1, 0), ("west", -1, 0))
        is_pane_or_bar = (
            bid == "minecraft:glass_pane"
            or bid.endswith("_stained_glass_pane")
            or bid == "minecraft:iron_bars"
        )
        is_fence = bid.endswith("_fence") and not bid.endswith("_fence_gate")
        is_wall = bid.endswith("_wall")

        if is_pane_or_bar:
            for dname, dx, dz in dirs:
                if dname in pdict:
                    continue
                nb = self.grid.get((x + dx, y, z + dz), ("minecraft:air", ()))[0]
                connects = (
                    nb == "minecraft:glass_pane"
                    or nb.endswith("_stained_glass_pane")
                    or nb == "minecraft:iron_bars"
                    or nb.endswith("_wall")
                    or self._is_full_face_solid(nb)
                )
                pdict[dname] = "true" if connects else "false"
            pdict.setdefault("waterlogged", "false")
        elif is_fence:
            is_nether = bid == "minecraft:nether_brick_fence"
            for dname, dx, dz in dirs:
                if dname in pdict:
                    continue
                nb = self.grid.get((x + dx, y, z + dz), ("minecraft:air", ()))[0]
                nb_is_fence = nb.endswith("_fence") and not nb.endswith("_fence_gate")
                same_fence_group = (
                    (nb == "minecraft:nether_brick_fence")
                    if is_nether
                    else (nb_is_fence and nb != "minecraft:nether_brick_fence")
                )
                connects = (
                    same_fence_group
                    or nb.endswith("_fence_gate")
                    or self._is_full_face_solid(nb)
                )
                pdict[dname] = "true" if connects else "false"
            pdict.setdefault("waterlogged", "false")
        elif is_wall:
            def _wall_connects(nx_id: str) -> bool:
                return (
                    nx_id.endswith("_wall")
                    or nx_id.endswith("_fence_gate")
                    or nx_id == "minecraft:glass_pane"
                    or nx_id.endswith("_stained_glass_pane")
                    or nx_id == "minecraft:iron_bars"
                    or self._is_full_face_solid(nx_id)
                )

            above_bid = self.grid.get((x, y + 1, z), ("minecraft:air", ()))[0]
            above_solid = self._is_full_face_solid(above_bid) or above_bid.endswith("_wall")
            conn_map = {}
            for dname, dx, dz in dirs:
                if dname in pdict:
                    conn_map[dname] = pdict[dname]
                    continue
                nb = self.grid.get((x + dx, y, z + dz), ("minecraft:air", ()))[0]
                if not _wall_connects(nb):
                    conn_map[dname] = "none"
                else:
                    above_nb = self.grid.get((x + dx, y + 1, z + dz), ("minecraft:air", ()))[0]
                    conn_map[dname] = "tall" if (above_solid and _wall_connects(above_nb)) else "low"
                pdict[dname] = conn_map[dname]
            if "up" not in pdict:
                ns_straight = (
                    conn_map["north"] != "none" and conn_map["south"] != "none"
                    and conn_map["east"] == "none" and conn_map["west"] == "none"
                    and conn_map["north"] == conn_map["south"]
                )
                ew_straight = (
                    conn_map["east"] != "none" and conn_map["west"] != "none"
                    and conn_map["north"] == "none" and conn_map["south"] == "none"
                    and conn_map["east"] == conn_map["west"]
                )
                pdict["up"] = "false" if ((ns_straight or ew_straight) and not above_solid) else "true"
            pdict.setdefault("waterlogged", "false")

        return tuple(sorted(pdict.items()))

    def save(self, rel_path: str):
        palette_map = {}
        palette_list = []
        blocks_list = []
        for (x, y, z), (bid, props) in sorted(self.grid.items()):
            # Leaving structure_void out of NBT blocks[] preserves world blocks (e.g. ocean water).
            if bid == "minecraft:structure_void":
                continue
            final_props = self._compute_connected_props(x, y, z, bid, props)
            key = (bid, final_props)
            if key not in palette_map:
                palette_map[key] = len(palette_list)
                entry = {"id": bid}
                if final_props:
                    entry["properties"] = {k: v for k, v in final_props}
                palette_list.append(entry)
            b_entry = {
                "pos": nbt_int_list([x, y, z]),
                "state": palette_map[key],
            }
            if (x, y, z) in self.block_nbts:
                b_entry["nbt"] = self.block_nbts[(x, y, z)]
            blocks_list.append(b_entry)

        root = {
            "DataVersion": 5023,
            "size": nbt_int_list([self.sx, self.sy, self.sz]),
            "palette": nbt_list(TAG_COMPOUND, palette_list),
            "blocks": nbt_list(TAG_COMPOUND, blocks_list),
            "entities": nbt_list(TAG_COMPOUND, self.entities),
        }
        write_nbt(rel_path, root)


def write_json(rel_path: str, payload: dict):
    path = DATA / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Common entities & villagers (Jigsaw 1x2x1 standees using PersistenceRequired)
# ---------------------------------------------------------------------------
def build_common_entity_templates():
    # Sentinel guard (exact 1x3x1 down_south Jigsaw entity template matching vanilla)
    sb = StructureBuilder(1, 3, 1, fill_block="minecraft:air")
    sb.jigsaw(0, 0, 0, "down_south", "minecraft:bottom", "minecraft:bottom", "minecraft:empty", "minecraft:structure_void", "rollable")
    sb.add_entity(0.5, 1.0, 0.5, "canopycavern:village_sentinel")
    sb.save("common/village_sentinel.nbt")

    write_json("worldgen/template_pool/common/village_sentinel.json", {
        "elements": [{
            "element": {
                "element_type": "minecraft:single_pool_element",
                "location": "canopycavern:common/village_sentinel",
                "processors": {"processors": []},
                "projection": "rigid",
            },
            "weight": 1,
        }],
        "fallback": "minecraft:empty",
    })

    # Villager presets with professions
    for v_name, prof, v_type in [
        ("plains_farmer", "minecraft:farmer", "minecraft:plains"),
        ("plains_weaponsmith", "minecraft:weaponsmith", "minecraft:plains"),
        ("plains_librarian", "minecraft:librarian", "minecraft:plains"),
        ("taiga_armorer", "minecraft:armorer", "minecraft:taiga"),
        ("taiga_cartographer", "minecraft:cartographer", "minecraft:taiga"),
        ("taiga_farmer", "minecraft:farmer", "minecraft:taiga"),
    ]:
        vb = StructureBuilder(1, 3, 1, fill_block="minecraft:air")
        vb.jigsaw(0, 0, 0, "down_south", "minecraft:bottom", "minecraft:bottom", "minecraft:empty", "minecraft:structure_void", "rollable")
        vb.add_entity(0.5, 1.0, 0.5, "minecraft:villager", {
            "VillagerData": {
                "level": 2,
                "profession": prof,
                "type": v_type,
            }
        })
        vb.save(f"common/villagers/{v_name}.nbt")

    write_json("worldgen/template_pool/common/temperate_villagers.json", {
        "elements": [
            {"element": {"element_type": "minecraft:single_pool_element", "location": f"canopycavern:common/villagers/{n}", "processors": {"processors": []}, "projection": "rigid"}, "weight": 1}
            for n in ("plains_farmer", "plains_weaponsmith", "plains_librarian")
        ],
        "fallback": "minecraft:empty",
    })
    write_json("worldgen/template_pool/common/alpine_villagers.json", {
        "elements": [
            {"element": {"element_type": "minecraft:single_pool_element", "location": f"canopycavern:common/villagers/{n}", "processors": {"processors": []}, "projection": "rigid"}, "weight": 1}
            for n in ("taiga_armorer", "taiga_cartographer", "taiga_farmer")
        ],
        "fallback": "minecraft:empty",
    })


# ---------------------------------------------------------------------------
# Architectural House & Tower Primitives (non-boxy, overhanging gable roofs!)
# ---------------------------------------------------------------------------
def draw_gabled_cottage(
    pal: dict,
    role: str,
    villager_pool: str,
    loot_table: str,
) -> StructureBuilder:
    """
    9x10x9 detailed architectural cottage/forge/library/guardhouse with:
    - stone foundation plinth & front stair landing
    - corner log pillars & recessed multi-material walls
    - glass-pane windows with upside-down stair sills / flower boxes
    - overhanging pitched gable roof along Z-axis (stairs + ridge slabs)
    - brick/stone chimney (or guard parapet)
    - interior floor, bed, workstation, lantern, loot chest, villager & optional sentinel
    Entrance jigsaw sits at [4, 0, 0] facing north_up (`minecraft:building_entrance`).
    """
    sb = StructureBuilder(9, 10, 9, fill_block="minecraft:air")
    plinth = pal["plinth"]
    wall = pal["wall"]
    accent = pal["accent"]
    pillar = (pal["pillar"], {"axis": "y"})
    floor = pal["floor"]
    roof_stairs = pal["roof_stairs"]
    roof_slab = pal["roof_slab"]
    roof_solid = pal["roof_solid"]
    fence = pal["fence"]
    door = pal["door"]
    pane = pal["pane"]

    # Footprint x: 1..7, z: 1..7, ground-level doorstep terrace at z=0
    sb.fill(1, 0, 1, 7, 0, 7, plinth)
    sb.fill(1, 0, 0, 7, 0, 0, plinth)
    sb.fill(2, 0, 2, 6, 0, 6, floor)
    # Entrance connector at [4, 1, 0] facing north_up so house y=0 foundation aligns flush with street y=0!
    sb.jigsaw(4, 1, 0, "north_up", "minecraft:building_entrance", "minecraft:building_entrance", "minecraft:empty", "minecraft:structure_void", "aligned")
    # Porch side lanterns on fence posts
    sb.set(2, 1, 0, fence)
    sb.lantern(2, 2, 0, hanging=False)
    sb.set(6, 1, 0, fence)
    sb.lantern(6, 2, 0, hanging=False)

    # Walls y=1..3 (x=1..7, z=1..7)
    for y in range(1, 4):
        for x in range(1, 8):
            for z in range(1, 8):
                is_edge = x in (1, 7) or z in (1, 7)
                if not is_edge:
                    continue
                is_corner = x in (1, 7) and z in (1, 7)
                if is_corner:
                    sb.set(x, y, z, pillar)
                elif y == 1:
                    sb.set(x, y, z, plinth)
                else:
                    sb.set(x, y, z, wall)

    # Timber ring beam at y=4
    for x in range(1, 8):
        sb.set(x, 4, 1, accent)
        sb.set(x, 4, 7, accent)
    for z in range(1, 8):
        sb.set(1, 4, z, accent)
        sb.set(7, 4, z, accent)

    # Doorway at (4, 1..2, 1)
    sb.door(4, 1, 1, door, "south")

    # Recessed glass-pane windows + window sill slabs
    for wx, wz in [(2, 1), (6, 1), (4, 7)]:
        sb.set(wx, 2, wz, pane)
        sb.slab(wx, 1, wz - 1 if wz == 1 else wz + 1, pal["sill_slab"], "top")
    for wx in (1, 7):
        for wz in (3, 5):
            sb.set(wx, 2, wz, pane)
            sb.slab(wx - 1 if wx == 1 else wx + 1, 1, wz, pal["sill_slab"], "top")

    # Overhanging Gable Roof (running front-to-back along Z, peaking along x=4 from x=0..8, z=0..8)
    for z in range(0, 9):
        # Eaves overhang at x=0 and x=8
        sb.stairs(0, 4, z, roof_stairs, "east")
        sb.stairs(8, 4, z, roof_stairs, "west")
        # Step 1: x=1,7 at y=5
        sb.stairs(1, 5, z, roof_stairs, "east")
        sb.stairs(7, 5, z, roof_stairs, "west")
        # Step 2: x=2,6 at y=6
        sb.stairs(2, 6, z, roof_stairs, "east")
        sb.stairs(6, 6, z, roof_stairs, "west")
        # Step 3: x=3,5 at y=7
        sb.stairs(3, 7, z, roof_stairs, "east")
        sb.stairs(5, 7, z, roof_stairs, "west")
        # Ridge peak x=4 at y=7..8
        sb.set(4, 7, z, roof_solid)
        sb.slab(4, 8, z, roof_slab, "bottom")

    # Gable triangles filled nicely at z=1 and z=7
    for gz in (1, 7):
        for x in range(2, 7):
            sb.set(x, 5, gz, wall)
        for x in range(3, 6):
            sb.set(x, 6, gz, wall)
        sb.set(4, 6, gz, pane)  # Attic gable window!

    # Interior furnishings & architectural role flavor
    sb.lantern(4, 5, 4, hanging=True)
    if role == "house":
        sb.bed(2, 1, 5, pal["bed"], "south")
        sb.set(5, 1, 6, "minecraft:crafting_table")
        sb.set(4, 1, 6, ("minecraft:barrel", {"facing": "north", "open": "false"}))
        sb.chest(2, 1, 2, "east", loot_table)
        # Cozy stone chimney at corner x=6, z=6 with smoker facing NORTH into the open room!
        for cy in range(2, 9):
            sb.set(6, cy, 6, "minecraft:stone_bricks")
        sb.set(6, 1, 6, ("minecraft:smoker", {"facing": "north", "lit": "true"}))
        sb.set(6, 9, 6, "minecraft:campfire")
    elif role == "forge":
        sb.set(2, 1, 6, "minecraft:stone_bricks")
        sb.set(3, 1, 6, "minecraft:stone_bricks")
        sb.set(2, 2, 6, "minecraft:stone_bricks")
        sb.set(3, 2, 6, "minecraft:stone_bricks")
        sb.set(2, 1, 5, ("minecraft:blast_furnace", {"facing": "north", "lit": "true"}))
        sb.set(3, 1, 5, "minecraft:lava_cauldron")
        sb.set(5, 1, 6, ("minecraft:anvil", {"facing": "east"}))
        sb.set(6, 1, 5, "minecraft:smithing_table")
        sb.chest(2, 1, 3, "east", loot_table)
        for cy in range(3, 9):
            sb.set(2, cy, 6, "minecraft:cobblestone")
        sb.set(2, 9, 6, "minecraft:stone_brick_wall")
    elif role == "library":
        for bx in (2, 3, 5, 6):
            sb.set(bx, 1, 6, "minecraft:bookshelf")
            sb.set(bx, 2, 6, "minecraft:bookshelf")
        sb.set(2, 1, 4, ("minecraft:lectern", {"facing": "east", "has_book": "false"}))
        sb.set(6, 1, 4, "minecraft:moss_block")
        sb.set(6, 2, 4, "minecraft:flowering_azalea")
        sb.chest(5, 1, 3, "west", loot_table)
    elif role == "guardhouse":
        # Open ground archway entrance + wide courtyard so Sentinels stand OUTDOORS unobstructed!
        sb.fill(3, 1, 1, 5, 2, 1, "minecraft:air")
        sb.bed(2, 1, 5, "minecraft:red_bed", "south")
        sb.set(6, 1, 6, "minecraft:grindstone")
        sb.set(5, 1, 6, "minecraft:fletching_table")
        sb.set(3, 2, 6, ("minecraft:bell", {"attachment": "single_wall", "facing": "north"}))
        sb.chest(2, 1, 3, "east", loot_table)
        # Ground-level outdoor Sentinels standing on front porch courtyard z=0 (never trapped inside!)
        sb.jigsaw(1, 0, 0, "up_north", "minecraft:bottom", "minecraft:bottom", "canopycavern:common/village_sentinel", plinth, "rollable")
        sb.jigsaw(7, 0, 0, "up_north", "minecraft:bottom", "minecraft:bottom", "canopycavern:common/village_sentinel", plinth, "rollable")

    # Resident villager in ground-floor hall (and guardhouse stays spacious & doorless!)
    sb.jigsaw(4, 0, 4, "up_north", "minecraft:bottom", "minecraft:bottom", villager_pool, pal["floor"], "rollable")
    return sb


def draw_central_plaza(pal: dict, landmark: str, villager_pool: str) -> StructureBuilder:
    """13x13x13 town square with ornate focal monument, lamps, stalls, 3 villagers, 1 Iron Golem, 2 Sentinels."""
    sb = StructureBuilder(13, 13, 13, fill_block="minecraft:air")
    plinth = pal["plinth"]
    wall = pal["wall"]
    accent = pal["accent"]
    floor = pal["floor"]
    road = pal["road"]
    pillar = (pal["pillar"], {"axis": "y"})
    fence = pal["fence"]
    s_pool = pal["street_pool"]

    # Base terrace y=0
    sb.fill(0, 0, 0, 12, 0, 12, plinth)
    sb.fill(1, 0, 1, 11, 0, 11, road)
    # Stone trim walkways cross
    for i in range(0, 13):
        sb.set(i, 0, 6, accent)
        sb.set(6, 0, i, accent)

    # Central octagonal plinth (4..8, 4..8)
    sb.fill(4, 0, 4, 8, 1, 8, plinth)
    sb.fill(5, 1, 5, 7, 1, 7, floor)
    sb.stairs(6, 1, 4, pal["step_block"], "south")
    sb.stairs(6, 1, 8, pal["step_block"], "north")
    sb.stairs(4, 1, 6, pal["step_block"], "east")
    sb.stairs(8, 1, 6, pal["step_block"], "west")

    if landmark == "crystal":
        # Glowing Amethyst Fountain Obelisk
        sb.fill(5, 1, 5, 7, 1, 7, "minecraft:water")
        sb.fill(6, 1, 6, 6, 6, 6, "minecraft:calcite")
        sb.set(6, 7, 6, "minecraft:amethyst_block")
        sb.set(6, 8, 6, ("minecraft:amethyst_cluster", {"facing": "up", "waterlogged": "false"}))
        for cx, cz in [(5, 5), (7, 5), (5, 7), (7, 7)]:
            sb.set(cx, 2, cz, "minecraft:deepslate_brick_wall")
            sb.lantern(cx, 3, cz, hanging=False)
    elif landmark == "peak":
        # Bell & Hearth Memorial Tower
        for cx, cz in [(5, 5), (7, 5), (5, 7), (7, 7)]:
            for y in range(2, 7):
                sb.set(cx, y, cz, pillar)
        sb.fill(5, 7, 5, 7, 7, 7, accent)
        sb.stairs(5, 8, 6, pal["roof_stairs"], "east")
        sb.stairs(7, 8, 6, pal["roof_stairs"], "west")
        sb.set(6, 8, 6, pal["roof_solid"])
        sb.slab(6, 9, 6, pal["roof_slab"], "bottom")
        sb.set(6, 2, 6, "minecraft:campfire")
        sb.set(6, 5, 5, ("minecraft:bell", {"attachment": "single_wall", "facing": "north"}))
    else:
        # Mossy Canopy Arbor Well & Hanging Gardens
        for cx, cz in [(5, 5), (7, 5), (5, 7), (7, 7)]:
            for y in range(2, 6):
                sb.set(cx, y, cz, pillar)
        sb.fill(5, 1, 5, 7, 1, 7, "minecraft:water")
        sb.set(6, 2, 6, "minecraft:water")
        sb.fill(4, 6, 4, 8, 6, 8, pal["roof_solid"])
        sb.fill(5, 7, 5, 7, 7, 7, pal["roof_slab"])
        sb.set(6, 7, 6, "minecraft:moss_block")
        sb.set(6, 8, 6, "minecraft:azalea")
        sb.lantern(6, 5, 6, hanging=True)

    # Corner lamp gardens & bell noticeboard
    for lx, lz in [(2, 2), (10, 2), (2, 10), (10, 10)]:
        sb.set(lx, 1, lz, "minecraft:moss_block")
        sb.set(lx, 1, lz + (1 if lz == 2 else -1), fence)
        sb.lantern(lx, 2, lz + (1 if lz == 2 else -1), hanging=False)
    sb.set(2, 1, 9, "minecraft:emerald_block")
    sb.set(2, 2, 9, ("minecraft:bell", {"attachment": "floor", "facing": "north"}))

    # 4 cardinal street connectors at y=1
    sb.jigsaw(6, 1, 0, "north_up", "minecraft:street", "minecraft:street", s_pool, "minecraft:structure_void", "aligned")
    sb.jigsaw(6, 1, 12, "south_up", "minecraft:street", "minecraft:street", s_pool, "minecraft:structure_void", "aligned")
    sb.jigsaw(12, 1, 6, "east_up", "minecraft:street", "minecraft:street", s_pool, "minecraft:structure_void", "aligned")
    sb.jigsaw(0, 1, 6, "west_up", "minecraft:street", "minecraft:street", s_pool, "minecraft:structure_void", "aligned")

    # Villager, Iron Golem, and 2 Security Sentinels
    sb.jigsaw(2, 0, 4, "up_north", "minecraft:bottom", "minecraft:bottom", villager_pool, road, "rollable")
    sb.jigsaw(10, 0, 8, "up_north", "minecraft:bottom", "minecraft:bottom", villager_pool, road, "rollable")
    sb.jigsaw(9, 0, 3, "up_north", "minecraft:bottom", "minecraft:bottom", "minecraft:village/common/iron_golem", road, "rollable")
    sb.jigsaw(3, 0, 10, "up_north", "minecraft:bottom", "minecraft:bottom", "canopycavern:common/village_sentinel", road, "rollable")
    sb.jigsaw(10, 0, 4, "up_north", "minecraft:bottom", "minecraft:bottom", "canopycavern:common/village_sentinel", road, "rollable")
    return sb


def build_village_theme(village_id: str, biomes: list[str], pal: dict, landmark: str, villager_pool: str, spacing_seed: int):
    # Streets: 5x3x15 staggered avenue with opposite-side plot entrances (zero cottage collision!)
    st = StructureBuilder(5, 3, 15, fill_block="minecraft:air")
    st.fill(1, 0, 0, 3, 0, 14, pal["road"])
    for z in range(0, 15):
        st.set(0, 0, z, pal["plinth"])
        st.set(4, 0, z, pal["plinth"])
    st.set(0, 1, 1, pal["fence"])
    st.lantern(0, 2, 1, hanging=False)
    st.set(4, 1, 13, pal["fence"])
    st.lantern(4, 2, 13, hanging=False)
    st.jigsaw(2, 1, 0, "north_up", "minecraft:street", "minecraft:street", pal["street_pool"], "minecraft:structure_void", "aligned")
    st.jigsaw(2, 1, 14, "south_up", "minecraft:street", "minecraft:street", pal["street_pool"], "minecraft:structure_void", "aligned")
    st.jigsaw(0, 1, 6, "west_up", "minecraft:building_entrance", "minecraft:building_entrance", pal["building_pool"], "minecraft:air", "aligned")
    st.jigsaw(4, 1, 10, "east_up", "minecraft:building_entrance", "minecraft:building_entrance", pal["building_pool"], "minecraft:air", "aligned")
    st.jigsaw(2, 0, 4, "up_north", "minecraft:bottom", "minecraft:bottom", "canopycavern:common/village_sentinel", pal["road"], "rollable")
    st.jigsaw(2, 0, 11, "up_north", "minecraft:bottom", "minecraft:bottom", "canopycavern:common/village_sentinel", pal["road"], "rollable")
    st.save(f"{village_id}/street_avenue.nbt")

    term = StructureBuilder(5, 3, 3, fill_block="minecraft:air")
    term.fill(1, 0, 0, 3, 0, 2, pal["road"])
    term.set(0, 0, 0, pal["plinth"])
    term.set(4, 0, 0, pal["plinth"])
    term.set(0, 1, 1, pal["plinth"])
    term.set(4, 1, 1, pal["plinth"])
    term.set(2, 1, 2, pal["fence"])
    term.lantern(2, 2, 2, hanging=False)
    term.jigsaw(2, 1, 0, "north_up", "minecraft:street", "minecraft:street", "minecraft:empty", "minecraft:structure_void", "aligned")
    term.save(f"{village_id}/terminator.nbt")

    center = draw_central_plaza(pal, landmark, villager_pool)
    center.save(f"{village_id}/town_center.nbt")

    for role in ("house", "forge", "library", "guardhouse"):
        b = draw_gabled_cottage(pal, role, villager_pool, "canopycavern:chests/village_supply")
        b.save(f"{village_id}/{role}.nbt")

    # Template pools
    write_json(f"worldgen/template_pool/{village_id}/start.json", {
        "elements": [{
            "element": {"element_type": "minecraft:single_pool_element", "location": f"canopycavern:{village_id}/town_center", "processors": {"processors": []}, "projection": "rigid"},
            "weight": 1,
        }],
        "fallback": "minecraft:empty",
    })
    write_json(f"worldgen/template_pool/{village_id}/streets.json", {
        "elements": [{
            "element": {"element_type": "minecraft:single_pool_element", "location": f"canopycavern:{village_id}/street_avenue", "processors": {"processors": []}, "projection": "terrain_matching"},
            "weight": 1,
        }],
        "fallback": f"canopycavern:{village_id}/terminators",
    })
    write_json(f"worldgen/template_pool/{village_id}/terminators.json", {
        "elements": [{
            "element": {"element_type": "minecraft:single_pool_element", "location": f"canopycavern:{village_id}/terminator", "processors": {"processors": []}, "projection": "terrain_matching"},
            "weight": 1,
        }],
        "fallback": "minecraft:empty",
    })
    write_json(f"worldgen/template_pool/{village_id}/buildings.json", {
        "elements": [
            {"element": {"element_type": "minecraft:single_pool_element", "location": f"canopycavern:{village_id}/{r}", "processors": {"processors": []}, "projection": "rigid"}, "weight": w}
            for r, w in [("house", 3), ("forge", 2), ("library", 2), ("guardhouse", 2)]
        ],
        "fallback": "minecraft:empty",
    })

    # Structure + biome tag
    write_json(f"tags/worldgen/biome/has_structure/{village_id}.json", {"replace": False, "values": biomes})
    write_json(f"worldgen/structure/{village_id}.json", {
        "type": "minecraft:jigsaw",
        "biomes": f"#canopycavern:has_structure/{village_id}",
        "max_distance_from_center": 80,
        "project_start_to_heightmap": "WORLD_SURFACE_WG",
        "size": 5,
        "spawn_overrides": {},
        "start_height": {"absolute": 0},
        "start_pool": f"canopycavern:{village_id}/start",
        "step": "surface_structures",
        "terrain_adaptation": "beard_thin",
        "use_expansion_hack": True,
    })


def build_underground_grotto_town():
    """Encapsulated underground cavern settlement for Verdant Grotto & Amber Caverns."""
    vid = "grotto_outpost_town"
    pal = {
        "plinth": "minecraft:polished_deepslate",
        "wall": "minecraft:deepslate_bricks",
        "accent": "minecraft:mossy_stone_bricks",
        "pillar": "minecraft:stripped_spruce_log",
        "floor": "minecraft:spruce_planks",
        "road": "minecraft:cobbled_deepslate",
        "grass": "minecraft:moss_block",
        "roof_stairs": "minecraft:deepslate_tile_stairs",
        "roof_slab": "minecraft:deepslate_tile_slab",
        "roof_solid": "minecraft:deepslate_tiles",
        "step_block": "minecraft:deepslate_brick_stairs",
        "sill_slab": "minecraft:spruce_slab",
        "fence": "minecraft:spruce_fence",
        "door": "minecraft:spruce_door",
        "pane": "minecraft:glass_pane",
        "bed": "minecraft:green_bed",
        "street_pool": f"canopycavern:{vid}/streets",
        "building_pool": f"canopycavern:{vid}/buildings",
    }

    # Enclosed subterranean town dome 13x9x13
    center = StructureBuilder(13, 9, 13, fill_block="minecraft:air")
    center.hollow_box(0, 0, 0, 12, 8, 12, "minecraft:deepslate_bricks", "minecraft:air")
    center.fill(1, 0, 1, 11, 0, 11, "minecraft:cobbled_deepslate")
    for x in (1, 11):
        for z in (1, 11):
            center.fill(x, 1, z, x, 7, z, "minecraft:polished_deepslate")
    # glowing cave crystal fountain
    center.fill(5, 0, 5, 7, 1, 7, "minecraft:moss_block")
    center.set(6, 1, 6, "minecraft:water")
    center.fill(6, 2, 6, 6, 6, 6, "minecraft:amethyst_block")
    center.lantern(5, 3, 5, hanging=False)
    center.lantern(7, 3, 7, hanging=False)
    center.lantern(6, 7, 6, hanging=True)
    # 4 arched corridor exits (open 3x3 arches at floor y=1..3, jigsaw at center y=1)
    for ox, oz, ori in [(6, 0, "north_up"), (6, 12, "south_up"), (12, 6, "east_up"), (0, 6, "west_up")]:
        if ox in (0, 12):
            for dy in range(1, 4):
                for dz in range(5, 8):
                    center.set(ox, dy, dz, "minecraft:air")
        else:
            for dy in range(1, 4):
                for dx in range(5, 8):
                    center.set(dx, dy, oz, "minecraft:air")
        center.jigsaw(ox, 1, oz, ori, "minecraft:street", "minecraft:street", pal["street_pool"], "minecraft:air", "aligned")

    center.jigsaw(3, 0, 3, "up_north", "minecraft:bottom", "minecraft:bottom", "canopycavern:common/temperate_villagers", "minecraft:cobbled_deepslate", "rollable")
    center.jigsaw(9, 0, 9, "up_north", "minecraft:bottom", "minecraft:bottom", "canopycavern:common/temperate_villagers", "minecraft:cobbled_deepslate", "rollable")
    center.jigsaw(9, 0, 3, "up_north", "minecraft:bottom", "minecraft:bottom", "minecraft:village/common/iron_golem", "minecraft:cobbled_deepslate", "rollable")
    center.jigsaw(3, 0, 9, "up_north", "minecraft:bottom", "minecraft:bottom", "canopycavern:common/village_sentinel", "minecraft:cobbled_deepslate", "rollable")
    center.save(f"{vid}/town_center.nbt")

    # Vaulted subterranean street tunnel (9x6x15) with staggered side exits (zero building overlap!)
    st = StructureBuilder(9, 6, 15, fill_block="minecraft:air")
    st.hollow_box(0, 0, 0, 8, 5, 14, "minecraft:deepslate_bricks", "minecraft:air")
    st.fill(1, 0, 1, 7, 0, 13, "minecraft:cobbled_deepslate")
    st.fill(3, 1, 0, 5, 3, 14, "minecraft:air")
    # Staggered wide doorways at x=0 (z=4..6) and x=8 (z=9..11)
    st.fill(0, 1, 4, 0, 3, 6, "minecraft:air")
    st.fill(8, 1, 9, 8, 3, 11, "minecraft:air")
    st.lantern(3, 4, 4, hanging=True)
    st.lantern(5, 4, 10, hanging=True)
    st.jigsaw(4, 1, 0, "north_up", "minecraft:street", "minecraft:street", pal["street_pool"], "minecraft:air", "aligned")
    st.jigsaw(4, 1, 14, "south_up", "minecraft:street", "minecraft:street", pal["street_pool"], "minecraft:air", "aligned")
    st.jigsaw(0, 1, 5, "west_up", "minecraft:building_entrance", "minecraft:building_entrance", pal["building_pool"], "minecraft:air", "aligned")
    st.jigsaw(8, 1, 10, "east_up", "minecraft:building_entrance", "minecraft:building_entrance", pal["building_pool"], "minecraft:air", "aligned")
    st.jigsaw(4, 0, 3, "up_north", "minecraft:bottom", "minecraft:bottom", "canopycavern:common/village_sentinel", "minecraft:cobbled_deepslate", "rollable")
    st.jigsaw(4, 0, 11, "up_north", "minecraft:bottom", "minecraft:bottom", "canopycavern:common/village_sentinel", "minecraft:cobbled_deepslate", "rollable")
    st.save(f"{vid}/street_tunnel.nbt")

    term = StructureBuilder(5, 5, 3, fill_block="minecraft:air")
    term.hollow_box(0, 0, 0, 4, 4, 2, "minecraft:deepslate_bricks", "minecraft:air")
    term.fill(1, 1, 0, 3, 3, 0, "minecraft:air")
    term.lantern(2, 3, 1, hanging=True)
    term.jigsaw(2, 1, 0, "north_up", "minecraft:street", "minecraft:street", "minecraft:empty", "minecraft:air", "aligned")
    term.save(f"{vid}/terminator.nbt")

    for role in ("house", "forge", "library", "guardhouse"):
        b = draw_gabled_cottage(pal, role, "canopycavern:common/temperate_villagers", "canopycavern:chests/village_supply")
        b.save(f"{vid}/{role}.nbt")

    write_json(f"worldgen/template_pool/{vid}/start.json", {
        "elements": [{"element": {"element_type": "minecraft:single_pool_element", "location": f"canopycavern:{vid}/town_center", "processors": {"processors": []}, "projection": "rigid"}, "weight": 1}],
        "fallback": "minecraft:empty",
    })
    write_json(f"worldgen/template_pool/{vid}/streets.json", {
        "elements": [{"element": {"element_type": "minecraft:single_pool_element", "location": f"canopycavern:{vid}/street_tunnel", "processors": {"processors": []}, "projection": "rigid"}, "weight": 1}],
        "fallback": f"canopycavern:{vid}/terminators",
    })
    write_json(f"worldgen/template_pool/{vid}/terminators.json", {
        "elements": [{"element": {"element_type": "minecraft:single_pool_element", "location": f"canopycavern:{vid}/terminator", "processors": {"processors": []}, "projection": "rigid"}, "weight": 1}],
        "fallback": "minecraft:empty",
    })
    write_json(f"worldgen/template_pool/{vid}/buildings.json", {
        "elements": [
            {"element": {"element_type": "minecraft:single_pool_element", "location": f"canopycavern:{vid}/{r}", "processors": {"processors": []}, "projection": "rigid"}, "weight": w}
            for r, w in [("house", 3), ("forge", 2), ("library", 2), ("guardhouse", 2)]
        ],
        "fallback": "minecraft:empty",
    })

    write_json(f"tags/worldgen/biome/has_structure/{vid}.json", {
        "replace": False,
        "values": ["canopycavern:verdant_grotto", "canopycavern:amber_caverns"],
    })
    write_json(f"worldgen/structure/{vid}.json", {
        "type": "minecraft:jigsaw",
        "biomes": f"#canopycavern:has_structure/{vid}",
        "liquid_settings": "ignore_waterlogging",
        "max_distance_from_center": 72,
        "size": 4,
        "spawn_overrides": {},
        "start_height": {"type": "minecraft:uniform", "min_inclusive": {"absolute": 8}, "max_inclusive": {"absolute": 28}},
        "start_pool": f"canopycavern:{vid}/start",
        "step": "underground_structures",
        "terrain_adaptation": "encapsulate",
        "use_expansion_hack": False,
    })


# ---------------------------------------------------------------------------
# Redesigned & New Multi-Room Exploration Structures (4)
# ---------------------------------------------------------------------------
def build_peak_watchtower_ruin():
    """Architectural 3-story alpine stone & timber watchtower with overhanging hoarding gallery + annex."""
    sb = StructureBuilder(13, 18, 13, fill_block="minecraft:air")
    # Battered stone foundation plinth (1..11, 0..1, 1..11)
    sb.fill(1, 0, 1, 11, 0, 11, "minecraft:stone_bricks")
    sb.fill(2, 1, 2, 10, 1, 10, "minecraft:cobblestone")
    # Entrance archway steps z=1
    sb.stairs(6, 1, 1, "minecraft:stone_brick_stairs", "south")
    sb.stairs(5, 1, 1, "minecraft:stone_brick_stairs", "south")
    sb.stairs(7, 1, 1, "minecraft:stone_brick_stairs", "south")

    # Ground Tower Core (3..9, y=1..6, 3..9) with corner buttresses
    sb.hollow_box(3, 1, 3, 9, 6, 9, "minecraft:stone_bricks", "minecraft:air")
    sb.fill(3, 1, 3, 9, 1, 9, "minecraft:cobblestone")
    for cx, cz in [(3, 3), (9, 3), (3, 9), (9, 9)]:
        for y in range(1, 14):
            sb.set(cx, y, cz, "minecraft:cobbled_deepslate")
    # Wide arched ground doorway at (5..7, 2..4, 3) so interior is bright, walkable, never boxed!
    for dx in (5, 6, 7):
        for dy in (2, 3):
            sb.set(dx, dy, 3, "minecraft:air")
    sb.set(6, 4, 3, "minecraft:air")
    sb.lantern(4, 3, 2, hanging=False)
    sb.lantern(8, 3, 2, hanging=False)

    # Overhanging Timber Hoarding Gallery (2..10, y=6..10, 2..10)
    sb.hollow_box(2, 6, 2, 10, 10, 10, "minecraft:spruce_planks", "minecraft:air")
    # Reinforce the gallery floors; restore the ladder after finishing the deck.
    sb.fill(4, 6, 4, 8, 6, 8, "minecraft:spruce_planks")
    sb.fill(4, 10, 4, 8, 10, 8, "minecraft:spruce_planks")
    for cx, cz in [(2, 2), (10, 2), (2, 10), (10, 10)]:
        for y in range(7, 11):
            sb.set(cx, y, cz, ("minecraft:spruce_log", {"axis": "y"}))
    for wx in (4, 6, 8):
        sb.set(wx, 8, 2, "minecraft:glass_pane")
        sb.set(wx, 8, 10, "minecraft:glass_pane")
    for wz in (4, 6, 8):
        sb.set(2, 8, wz, "minecraft:glass_pane")
        sb.set(10, 8, wz, "minecraft:glass_pane")

    # Crenelated Lookout & Signal Spire (y=10..17, open deck above y=10 ceiling!)
    sb.fill(3, 10, 3, 9, 10, 9, "minecraft:stone_bricks")
    for i in range(3, 10):
        for y in (11,):
            sb.set(i, y, 3, "minecraft:stone_bricks")
            sb.set(i, y, 9, "minecraft:stone_bricks")
            sb.set(3, y, i, "minecraft:stone_bricks")
            sb.set(9, y, i, "minecraft:stone_bricks")
    for i in range(3, 10, 2):
        sb.set(i, 12, 3, "minecraft:stone_brick_wall")
        sb.set(i, 12, 9, "minecraft:stone_brick_wall")
        sb.set(3, 12, i, "minecraft:stone_brick_wall")
        sb.set(9, 12, i, "minecraft:stone_brick_wall")
    # Signal Spire Roof supported on 4 corner pillars (4..8)
    for cx, cz in [(4, 4), (8, 4), (4, 8), (8, 8)]:
        for y in range(11, 15):
            sb.set(cx, y, cz, ("minecraft:spruce_log", {"axis": "y"}))
    sb.fill(3, 14, 3, 9, 14, 9, "minecraft:deepslate_tile_slab")
    sb.fill(4, 15, 4, 8, 15, 8, "minecraft:deepslate_tiles")
    sb.fill(5, 16, 5, 7, 16, 7, "minecraft:deepslate_tile_slab")
    sb.set(6, 17, 6, "minecraft:lightning_rod")
    # Signal hearth + Bell on deck
    sb.set(6, 11, 6, "minecraft:campfire")
    sb.set(5, 12, 5, ("minecraft:bell", {"attachment": "single_wall", "facing": "north"}))
    # Loot chests + Furnace facing into open tower room
    sb.chest(4, 2, 7, "north", "canopycavern:chests/peak_watchtower")
    sb.chest(4, 7, 5, "south", "canopycavern:chests/peak_watchtower")
    sb.set(5, 2, 7, ("minecraft:furnace", {"facing": "north", "lit": "true"}))
    sb.bed(4, 7, 7, "minecraft:blue_bed", "south")
    sb.lantern(6, 5, 6, hanging=True)
    sb.lantern(6, 9, 6, hanging=True)

    # Jigsaw annex connector at outer x=12 + archway + Sentinel guard!
    sb.set(9, 2, 6, "minecraft:air")
    sb.set(9, 3, 6, "minecraft:air")
    sb.set(10, 1, 6, "minecraft:cobblestone")
    sb.set(11, 1, 6, "minecraft:cobblestone")
    sb.set(12, 1, 6, "minecraft:cobblestone")
    sb.jigsaw(12, 2, 6, "east_up", "canopycavern:wing", "canopycavern:wing", "canopycavern:peak_watchtower_ruin/wings", "minecraft:air", "aligned")
    sb.jigsaw(6, 1, 4, "up_north", "minecraft:bottom", "minecraft:bottom", "canopycavern:common/village_sentinel", "minecraft:cobblestone", "rollable")
    for y in range(2, 12):
        sb.set(9, y, 8, "minecraft:stone_bricks")
        sb.set(8, y, 8, ("minecraft:ladder", {"facing": "west", "waterlogged": "false"}))
    for y in (12, 13):
        sb.set(8, y, 8, "minecraft:air")
        sb.set(8, y, 7, "minecraft:air")

    sb.save("peak_watchtower_ruin.nbt")

    # Side Stable / Supply Annex Wing (7x6x7)
    wing = StructureBuilder(7, 6, 7, fill_block="minecraft:air")
    wing.hollow_box(0, 0, 0, 6, 4, 6, "minecraft:spruce_planks", "minecraft:air")
    wing.fill(0, 0, 0, 6, 0, 6, "minecraft:cobblestone")
    for cx, cz in [(0, 0), (6, 0), (0, 6), (6, 6)]:
        wing.fill(cx, 1, cz, cx, 4, cz, ("minecraft:spruce_log", {"axis": "y"}))
    wing.fill(0, 5, 0, 6, 5, 6, "minecraft:deepslate_tile_slab")
    wing.set(0, 1, 3, "minecraft:air")
    wing.set(0, 2, 3, "minecraft:air")
    wing.chest(5, 1, 3, "north", "canopycavern:chests/peak_watchtower")
    wing.set(4, 1, 5, "minecraft:hay_block")
    wing.set(2, 1, 5, "minecraft:barrel")
    wing.lantern(3, 3, 3, hanging=True)
    wing.jigsaw(0, 1, 3, "west_up", "canopycavern:wing", "canopycavern:wing", "minecraft:empty", "minecraft:air", "aligned")
    wing.save("peak_watchtower_ruin_annex.nbt")

    write_json("worldgen/template_pool/peak_watchtower_ruin/start.json", {
        "elements": [{"element": {"element_type": "minecraft:single_pool_element", "location": "canopycavern:peak_watchtower_ruin", "processors": {"processors": []}, "projection": "rigid"}, "weight": 1}],
        "fallback": "minecraft:empty",
    })
    write_json("worldgen/template_pool/peak_watchtower_ruin/wings.json", {
        "elements": [{"element": {"element_type": "minecraft:single_pool_element", "location": "canopycavern:peak_watchtower_ruin_annex", "processors": {"processors": []}, "projection": "rigid"}, "weight": 1}],
        "fallback": "minecraft:empty",
    })
    write_json("worldgen/structure/peak_watchtower_ruin.json", {
        "type": "minecraft:jigsaw",
        "biomes": "#canopycavern:has_structure/peak_watchtower_ruin",
        "max_distance_from_center": 64,
        "project_start_to_heightmap": "WORLD_SURFACE_WG",
        "size": 3,
        "spawn_overrides": {},
        "start_height": {"absolute": 0},
        "start_pool": "canopycavern:peak_watchtower_ruin/start",
        "step": "surface_structures",
        "terrain_adaptation": "beard_thin",
        "use_expansion_hack": False,
    })


def build_cavern_shrine():
    """Sunken Vaulted Sanctum + Jigsaw Reliquary Cloister wings."""
    sb = StructureBuilder(13, 10, 13, fill_block="minecraft:air")
    sb.hollow_box(0, 0, 0, 12, 9, 12, "minecraft:deepslate_bricks", "minecraft:air")
    sb.fill(1, 0, 1, 11, 0, 11, "minecraft:mossy_stone_bricks")
    # Tiered central dais + water channels
    sb.fill(4, 1, 4, 8, 1, 8, "minecraft:polished_deepslate")
    for i in range(4, 9):
        sb.set(i, 1, 4, "minecraft:water")
        sb.set(i, 1, 8, "minecraft:water")
    sb.fill(5, 2, 5, 7, 2, 7, "minecraft:chiseled_deepslate")
    # Amethyst altar spire
    sb.set(6, 3, 6, "minecraft:amethyst_block")
    sb.set(6, 4, 6, "minecraft:budding_amethyst")
    sb.set(6, 5, 6, ("minecraft:amethyst_cluster", {"facing": "up", "waterlogged": "false"}))
    # Ribbed Vaulted Pillars & glowing ceiling ribs
    for cx, cz in [(2, 2), (10, 2), (2, 10), (10, 10)]:
        for y in range(1, 8):
            sb.set(cx, y, cz, "minecraft:chiseled_stone_bricks" if y in (2, 6) else "minecraft:deepslate_tiles")
        sb.set(cx, 7, cz, "minecraft:sea_lantern")
    for x in range(1, 12):
        sb.set(x, 8, 6, "minecraft:deepslate_tile_slab")
        sb.set(6, 8, x, "minecraft:deepslate_tile_slab")
    sb.lantern(6, 7, 3, hanging=True)
    sb.lantern(6, 7, 9, hanging=True)

    # Shrines treasure chest & moss gardens
    sb.chest(6, 3, 5, "north", "canopycavern:chests/cavern_shrine")
    sb.chest(2, 1, 6, "east", "canopycavern:chests/cavern_shrine")
    sb.set(3, 1, 3, "minecraft:moss_block")
    sb.set(3, 2, 3, "minecraft:spore_blossom" if False else "minecraft:flowering_azalea")
    sb.set(9, 1, 9, "minecraft:moss_block")
    sb.set(9, 2, 9, "minecraft:flowering_azalea")

    # Dual symmetrical archways with Jigsaw wing connectors!
    for wx, ori in [(0, "west_up"), (12, "east_up")]:
        for dy in range(1, 5):
            for dz in range(5, 8):
                sb.set(wx, dy, dz, "minecraft:air")
        sb.jigsaw(wx, 1, 6, ori, "canopycavern:wing", "canopycavern:wing", "canopycavern:cavern_shrine/wings", "minecraft:air", "aligned")
    sb.save("cavern_shrine.nbt")

    wing = StructureBuilder(7, 7, 7, fill_block="minecraft:air")
    wing.hollow_box(0, 0, 0, 6, 6, 6, "minecraft:deepslate_bricks", "minecraft:air")
    wing.fill(1, 0, 1, 5, 0, 5, "minecraft:moss_block")
    for dy in range(1, 5):
        for dz in range(2, 5):
            wing.set(0, dy, dz, "minecraft:air")
    wing.set(4, 1, 3, "minecraft:amethyst_block")
    wing.set(4, 2, 3, "minecraft:amethyst_cluster")
    wing.chest(5, 1, 3, "north", "canopycavern:chests/cavern_shrine")
    wing.lantern(3, 5, 3, hanging=True)
    wing.jigsaw(0, 1, 3, "west_up", "canopycavern:wing", "canopycavern:wing", "minecraft:empty", "minecraft:air", "aligned")
    wing.save("cavern_shrine_cloister.nbt")

    write_json("worldgen/template_pool/cavern_shrine/start.json", {
        "elements": [{"element": {"element_type": "minecraft:single_pool_element", "location": "canopycavern:cavern_shrine", "processors": {"processors": []}, "projection": "rigid"}, "weight": 1}],
        "fallback": "minecraft:empty",
    })
    write_json("worldgen/template_pool/cavern_shrine/wings.json", {
        "elements": [{"element": {"element_type": "minecraft:single_pool_element", "location": "canopycavern:cavern_shrine_cloister", "processors": {"processors": []}, "projection": "rigid"}, "weight": 1}],
        "fallback": "minecraft:empty",
    })
    write_json("worldgen/structure/cavern_shrine.json", {
        "type": "minecraft:jigsaw",
        "biomes": "#canopycavern:has_structure/cavern_shrine",
        "liquid_settings": "ignore_waterlogging",
        "max_distance_from_center": 64,
        "size": 3,
        "spawn_overrides": {},
        "start_height": {"type": "minecraft:uniform", "min_inclusive": {"absolute": -36}, "max_inclusive": {"absolute": -8}},
        "start_pool": "canopycavern:cavern_shrine/start",
        "step": "underground_structures",
        "terrain_adaptation": "encapsulate",
        "use_expansion_hack": False,
    })
    write_json("tags/worldgen/biome/has_structure/cavern_shrine.json", {
        "replace": False,
        "values": ["canopycavern:verdant_grotto", "canopycavern:amber_caverns", "#minecraft:is_overworld"],
    })


def build_canopy_treetop_bastion():
    """New Elevated Treetop Timber Bastion in Mossy Canopy & Forests."""
    sb = StructureBuilder(13, 15, 13, fill_block="minecraft:air")
    # 4 sturdy ancient log stilts reaching y=0..6
    for sx, sz in [(2, 2), (10, 2), (2, 10), (10, 10)]:
        for x in range(sx - 1, sx + 2):
            for z in range(sz - 1, sz + 2):
                sb.set(x, 0, z, "minecraft:mossy_cobblestone")
        for y in range(1, 11):
            sb.set(sx, y, sz, ("minecraft:dark_oak_log", {"axis": "y"}))
        # buttress braces at y=1..2 and y=5
        sb.stairs(sx + (1 if sx == 2 else -1), 5, sz, "minecraft:dark_oak_stairs", "west" if sx == 2 else "east", "top")

    # Central access ladder shaft from ground (6, 0..6, 6)
    for y in range(0, 7):
        sb.set(6, y, 6, ("minecraft:dark_oak_log", {"axis": "y"}))
        sb.set(5, y, 6, ("minecraft:ladder", {"facing": "west", "waterlogged": "false"}))

    # Elevated Bastion Deck at y=6 (1..11, 1..11) + fence balustrade
    sb.fill(1, 6, 1, 11, 6, 11, "minecraft:spruce_planks")
    sb.set(5, 6, 6, ("minecraft:ladder", {"facing": "west", "waterlogged": "false"}))
    for i in range(1, 12):
        sb.set(i, 7, 1, "minecraft:dark_oak_fence")
        sb.set(i, 7, 11, "minecraft:dark_oak_fence")
        sb.set(1, 7, i, "minecraft:dark_oak_fence")
        sb.set(11, 7, i, "minecraft:dark_oak_fence")

    # Ground Flagstone Courtyard beneath Stilts + Outdoor Sentinel Post (y=1)
    sb.fill(4, 0, 2, 8, 0, 10, "minecraft:mossy_cobblestone")
    sb.lantern(4, 1, 2, hanging=False)
    sb.lantern(8, 1, 2, hanging=False)
    sb.jigsaw(6, 0, 3, "up_north", "minecraft:bottom", "minecraft:bottom", "canopycavern:common/village_sentinel", "minecraft:mossy_cobblestone", "rollable")

    # Upper Pavilion Keep (3..9, y=6..10, 3..9; floor stays y=6, room y=7..9 is open!)
    sb.hollow_box(3, 6, 3, 9, 10, 9, "minecraft:oak_planks", "minecraft:air")
    sb.fill(3, 6, 3, 9, 6, 9, "minecraft:spruce_planks")
    sb.set(5, 6, 6, ("minecraft:ladder", {"facing": "west", "waterlogged": "false"}))
    # Open 3-wide front archway + wide side deck arch so sentinels patrol freely
    for dx in (5, 6, 7):
        sb.set(dx, 7, 3, "minecraft:air")
        sb.set(dx, 8, 3, "minecraft:air")
    sb.set(3, 7, 6, "minecraft:air")
    sb.set(3, 8, 6, "minecraft:air")
    sb.set(9, 7, 6, "minecraft:air")
    sb.set(9, 8, 6, "minecraft:air")
    for wx in (4, 8):
        sb.set(wx, 8, 3, "minecraft:glass_pane")
        sb.set(wx, 8, 9, "minecraft:glass_pane")
    # Vaulted Pitched Roof + Mossy Top Crest (y=11..14)
    for z in range(2, 11):
        sb.stairs(2, 11, z, "minecraft:spruce_stairs", "east")
        sb.stairs(10, 11, z, "minecraft:spruce_stairs", "west")
        sb.stairs(3, 12, z, "minecraft:spruce_stairs", "east")
        sb.stairs(9, 12, z, "minecraft:spruce_stairs", "west")
        sb.stairs(4, 13, z, "minecraft:spruce_stairs", "east")
        sb.stairs(8, 13, z, "minecraft:spruce_stairs", "west")
        sb.fill(5, 13, z, 7, 13, z, "minecraft:moss_block")
        sb.fill(5, 14, z, 7, 14, z, "minecraft:spruce_slab")

    # Interior treasures & Sentinel defender
    sb.chest(4, 7, 8, "north", "canopycavern:chests/canopy_bastion")
    sb.chest(8, 7, 8, "north", "canopycavern:chests/canopy_bastion")
    sb.set(7, 7, 8, "minecraft:brewing_stand")
    sb.set(5, 7, 8, "minecraft:fletching_table")
    sb.lantern(6, 12, 6, hanging=True)
    sb.lantern(2, 8, 2, hanging=False)
    sb.lantern(10, 8, 10, hanging=False)
    sb.jigsaw(6, 6, 4, "up_north", "minecraft:bottom", "minecraft:bottom", "canopycavern:common/village_sentinel", "minecraft:spruce_planks", "rollable")
    sb.set(11, 7, 6, "minecraft:air")
    sb.set(12, 6, 6, "minecraft:spruce_planks")
    sb.jigsaw(12, 7, 6, "east_up", "canopycavern:wing", "canopycavern:wing", "canopycavern:canopy_treetop_bastion/wings", "minecraft:air", "aligned")
    sb.save("canopy_treetop_bastion.nbt")

    # Lookout Bridge Annex (9x7x7)
    bridge = StructureBuilder(9, 7, 7, fill_block="minecraft:air")
    bridge.fill(0, 0, 1, 8, 0, 5, "minecraft:spruce_planks")
    for x in range(0, 9):
        bridge.set(x, 1, 1, "minecraft:dark_oak_fence")
        bridge.set(x, 1, 5, "minecraft:dark_oak_fence")
    bridge.fill(4, 0, 0, 8, 0, 6, "minecraft:spruce_planks")
    for cx, cz in [(4, 0), (8, 0), (4, 6), (8, 6)]:
        for y in range(1, 5):
            bridge.set(cx, y, cz, ("minecraft:dark_oak_log", {"axis": "y"}))
    bridge.fill(4, 5, 0, 8, 5, 6, "minecraft:moss_block")
    bridge.fill(5, 6, 1, 7, 6, 5, "minecraft:spruce_slab")
    bridge.chest(7, 1, 3, "west", "canopycavern:chests/canopy_bastion")
    bridge.lantern(6, 4, 3, hanging=True)
    bridge.jigsaw(0, 1, 3, "west_up", "canopycavern:wing", "canopycavern:wing", "minecraft:empty", "minecraft:air", "aligned")
    bridge.save("canopy_treetop_bastion_bridge.nbt")

    write_json("worldgen/template_pool/canopy_treetop_bastion/start.json", {
        "elements": [{"element": {"element_type": "minecraft:single_pool_element", "location": "canopycavern:canopy_treetop_bastion", "processors": {"processors": []}, "projection": "rigid"}, "weight": 1}],
        "fallback": "minecraft:empty",
    })
    write_json("worldgen/template_pool/canopy_treetop_bastion/wings.json", {
        "elements": [{"element": {"element_type": "minecraft:single_pool_element", "location": "canopycavern:canopy_treetop_bastion_bridge", "processors": {"processors": []}, "projection": "rigid"}, "weight": 1}],
        "fallback": "minecraft:empty",
    })
    write_json("tags/worldgen/biome/has_structure/canopy_treetop_bastion.json", {
        "replace": False,
        "values": ["canopycavern:mossy_canopy", "#minecraft:is_forest"],
    })
    write_json("worldgen/structure/canopy_treetop_bastion.json", {
        "type": "minecraft:jigsaw",
        "biomes": "#canopycavern:has_structure/canopy_treetop_bastion",
        "max_distance_from_center": 64,
        "project_start_to_heightmap": "WORLD_SURFACE_WG",
        "size": 3,
        "spawn_overrides": {},
        "start_height": {"absolute": 0},
        "start_pool": "canopycavern:canopy_treetop_bastion/start",
        "step": "surface_structures",
        "terrain_adaptation": "beard_thin",
        "use_expansion_hack": False,
    })
    write_json("worldgen/structure_set/canopy_treetop_bastions.json", {
        "placement": {"type": "minecraft:random_spread", "salt": 91827364, "separation": 8, "spacing": 22},
        "structures": [{"structure": "canopycavern:canopy_treetop_bastion", "weight": 1}],
    })


def build_echoing_mineshaft_hub():
    """New Subterranean Multi-Room Echoing Mineshaft Hub in deep caves."""
    sb = StructureBuilder(13, 9, 13, fill_block="minecraft:air")
    sb.hollow_box(0, 0, 0, 12, 8, 12, "minecraft:cobbled_deepslate", "minecraft:air")
    sb.fill(1, 0, 1, 11, 0, 11, "minecraft:polished_deepslate")
    # Timber & deepslate quarry arches + minecart cross rails
    for x in range(1, 12):
        sb.set(x, 1, 6, ("minecraft:rail", {"shape": "east_west", "waterlogged": "false"}))
    for z in range(1, 12):
        sb.set(6, 1, z, ("minecraft:rail", {"shape": "north_south", "waterlogged": "false"}))
    for px, pz in [(2, 2), (10, 2), (2, 10), (10, 10), (4, 4), (8, 4), (4, 8), (8, 8)]:
        for y in range(1, 7):
            sb.set(px, y, pz, ("minecraft:dark_oak_log", {"axis": "y"}))
    sb.fill(2, 7, 2, 10, 7, 10, "minecraft:dark_oak_planks")
    sb.fill(4, 7, 4, 8, 7, 8, "minecraft:deepslate_tiles")
    # Ore vein displays & blast furnaces
    sb.set(2, 1, 3, "minecraft:raw_copper_block")
    sb.set(2, 1, 9, "minecraft:amethyst_block")
    sb.set(10, 1, 3, ("minecraft:blast_furnace", {"facing": "west", "lit": "true"}))
    sb.chest(9, 1, 9, "north", "canopycavern:chests/echoing_mineshaft")
    sb.chest(3, 1, 9, "east", "canopycavern:chests/echoing_mineshaft")
    sb.lantern(6, 6, 6, hanging=True)
    sb.lantern(3, 6, 6, hanging=True)
    sb.lantern(9, 6, 6, hanging=True)
    # 4 Jigsaw tunnel connectors
    for wx, wz, ori in [(0, 6, "west_up"), (12, 6, "east_up"), (6, 0, "north_up"), (6, 12, "south_up")]:
        for dy in range(1, 5):
            if wx in (0, 12):
                for dz in range(5, 8):
                    sb.set(wx, dy, dz, "minecraft:air")
            else:
                for dx in range(5, 8):
                    sb.set(dx, dy, wz, "minecraft:air")
        sb.jigsaw(wx, 1, wz, ori, "canopycavern:shaft", "canopycavern:shaft", "canopycavern:echoing_mineshaft_hub/tunnels", "minecraft:air", "aligned")
    sb.save("echoing_mineshaft_hub.nbt")

    # Tunnel Wing (11x7x7)
    tun = StructureBuilder(11, 7, 7, fill_block="minecraft:air")
    tun.hollow_box(0, 0, 0, 10, 6, 6, "minecraft:cobbled_deepslate", "minecraft:air")
    tun.fill(1, 0, 1, 9, 0, 5, "minecraft:tuff")
    for dy in range(1, 5):
        for dz in range(2, 5):
            tun.set(0, dy, dz, "minecraft:air")
            tun.set(10, dy, dz, "minecraft:air")
    for x in range(1, 10):
        tun.set(x, 1, 3, ("minecraft:rail", {"shape": "east_west", "waterlogged": "false"}))
        if x % 3 == 0:
            tun.fill(x, 1, 1, x, 4, 1, "minecraft:dark_oak_fence")
            tun.fill(x, 1, 5, x, 4, 5, "minecraft:dark_oak_fence")
            tun.fill(x, 5, 1, x, 5, 5, "minecraft:dark_oak_planks")
            tun.lantern(x, 4, 3, hanging=True)
    tun.chest(5, 1, 2, "west", "canopycavern:chests/echoing_mineshaft")
    tun.jigsaw(0, 1, 3, "west_up", "canopycavern:shaft", "canopycavern:shaft", "canopycavern:echoing_mineshaft_hub/tunnels", "minecraft:air", "aligned")
    tun.jigsaw(10, 1, 3, "east_up", "canopycavern:shaft", "canopycavern:shaft", "canopycavern:echoing_mineshaft_hub/tunnels", "minecraft:air", "aligned")
    tun.save("echoing_mineshaft_tunnel.nbt")

    # Dead-end Ore Vault Chamber (7x7x7)
    cap = StructureBuilder(7, 7, 7, fill_block="minecraft:air")
    cap.hollow_box(0, 0, 0, 6, 6, 6, "minecraft:deepslate_bricks", "minecraft:air")
    cap.fill(1, 0, 1, 5, 0, 5, "minecraft:polished_deepslate")
    for dy in range(1, 5):
        for dz in range(2, 5):
            cap.set(0, dy, dz, "minecraft:air")
    cap.set(5, 1, 3, "minecraft:amethyst_block")
    cap.set(5, 2, 3, "minecraft:budding_amethyst")
    cap.chest(4, 1, 3, "west", "canopycavern:chests/echoing_mineshaft")
    cap.lantern(3, 5, 3, hanging=True)
    cap.jigsaw(0, 1, 3, "west_up", "canopycavern:shaft", "canopycavern:shaft", "minecraft:empty", "minecraft:air", "aligned")
    cap.save("echoing_mineshaft_vault.nbt")

    write_json("worldgen/template_pool/echoing_mineshaft_hub/start.json", {
        "elements": [{"element": {"element_type": "minecraft:single_pool_element", "location": "canopycavern:echoing_mineshaft_hub", "processors": {"processors": []}, "projection": "rigid"}, "weight": 1}],
        "fallback": "minecraft:empty",
    })
    write_json("worldgen/template_pool/echoing_mineshaft_hub/tunnels.json", {
        "elements": [{"element": {"element_type": "minecraft:single_pool_element", "location": "canopycavern:echoing_mineshaft_tunnel", "processors": {"processors": []}, "projection": "rigid"}, "weight": 1}],
        "fallback": "canopycavern:echoing_mineshaft_hub/caps",
    })
    write_json("worldgen/template_pool/echoing_mineshaft_hub/caps.json", {
        "elements": [{"element": {"element_type": "minecraft:single_pool_element", "location": "canopycavern:echoing_mineshaft_vault", "processors": {"processors": []}, "projection": "rigid"}, "weight": 1}],
        "fallback": "minecraft:empty",
    })
    write_json("tags/worldgen/biome/has_structure/echoing_mineshaft_hub.json", {
        "replace": False,
        "values": ["canopycavern:amber_caverns", "canopycavern:verdant_grotto", "#minecraft:is_overworld"],
    })
    write_json("worldgen/structure/echoing_mineshaft_hub.json", {
        "type": "minecraft:jigsaw",
        "biomes": "#canopycavern:has_structure/echoing_mineshaft_hub",
        "liquid_settings": "ignore_waterlogging",
        "max_distance_from_center": 80,
        "size": 4,
        "spawn_overrides": {},
        "start_height": {"type": "minecraft:uniform", "min_inclusive": {"absolute": -32}, "max_inclusive": {"absolute": 8}},
        "start_pool": "canopycavern:echoing_mineshaft_hub/start",
        "step": "underground_structures",
        "terrain_adaptation": "encapsulate",
        "use_expansion_hack": False,
    })
    write_json("worldgen/structure_set/echoing_mineshaft_hubs.json", {
        "placement": {"type": "minecraft:random_spread", "salt": 56473829, "separation": 9, "spacing": 24},
        "structures": [{"structure": "canopycavern:echoing_mineshaft_hub", "weight": 1}],
    })


def build_all():
    build_common_entity_templates()
    build_peak_watchtower_ruin()
    build_cavern_shrine()
    build_canopy_treetop_bastion()
    build_echoing_mineshaft_hub()

    # 3 surface Villager Civilizations + 1 underground Grotto Outpost Town
    build_village_theme(
        "crystal_citadel",
        ["canopycavern:crystal_steppe"],
        {
            "plinth": "minecraft:deepslate_bricks",
            "wall": "minecraft:calcite",
            "accent": "minecraft:smooth_basalt",
            "pillar": "minecraft:stripped_spruce_log",
            "floor": "minecraft:spruce_planks",
            "road": "minecraft:deepslate_tiles",
            "grass": "minecraft:grass_block",
            "roof_stairs": "minecraft:oxidized_cut_copper_stairs",
            "roof_slab": "minecraft:oxidized_cut_copper_slab",
            "roof_solid": "minecraft:oxidized_cut_copper",
            "step_block": "minecraft:deepslate_brick_stairs",
            "sill_slab": "minecraft:spruce_slab",
            "fence": "minecraft:spruce_fence",
            "door": "minecraft:spruce_door",
            "pane": "minecraft:light_blue_stained_glass_pane",
            "bed": "minecraft:cyan_bed",
            "street_pool": "canopycavern:crystal_citadel/streets",
            "building_pool": "canopycavern:crystal_citadel/buildings",
        },
        landmark="crystal",
        villager_pool="canopycavern:common/temperate_villagers",
        spacing_seed=11,
    )

    build_village_theme(
        "peak_citadel",
        ["canopycavern:whispering_peaks"],
        {
            "plinth": "minecraft:stone_bricks",
            "wall": "minecraft:spruce_planks",
            "accent": "minecraft:cobbled_deepslate",
            "pillar": "minecraft:spruce_log",
            "floor": "minecraft:oak_planks",
            "road": "minecraft:cobblestone",
            "grass": "minecraft:grass_block",
            "roof_stairs": "minecraft:deepslate_tile_stairs",
            "roof_slab": "minecraft:deepslate_tile_slab",
            "roof_solid": "minecraft:deepslate_tiles",
            "step_block": "minecraft:stone_brick_stairs",
            "sill_slab": "minecraft:spruce_slab",
            "fence": "minecraft:spruce_fence",
            "door": "minecraft:spruce_door",
            "pane": "minecraft:glass_pane",
            "bed": "minecraft:blue_bed",
            "street_pool": "canopycavern:peak_citadel/streets",
            "building_pool": "canopycavern:peak_citadel/buildings",
        },
        landmark="peak",
        villager_pool="canopycavern:common/alpine_villagers",
        spacing_seed=22,
    )

    build_village_theme(
        "canopy_village",
        ["canopycavern:mossy_canopy", "minecraft:flower_forest", "minecraft:old_growth_birch_forest"],
        {
            "plinth": "minecraft:mossy_cobblestone",
            "wall": "minecraft:oak_planks",
            "accent": "minecraft:mossy_stone_bricks",
            "pillar": "minecraft:dark_oak_log",
            "floor": "minecraft:oak_planks",
            "road": "minecraft:dirt_path",
            "grass": "minecraft:grass_block",
            "roof_stairs": "minecraft:spruce_stairs",
            "roof_slab": "minecraft:spruce_slab",
            "roof_solid": "minecraft:spruce_planks",
            "step_block": "minecraft:mossy_stone_brick_stairs",
            "sill_slab": "minecraft:oak_slab",
            "fence": "minecraft:dark_oak_fence",
            "door": "minecraft:oak_door",
            "pane": "minecraft:glass_pane",
            "bed": "minecraft:green_bed",
            "street_pool": "canopycavern:canopy_village/streets",
            "building_pool": "canopycavern:canopy_village/buildings",
        },
        landmark="canopy",
        villager_pool="canopycavern:common/temperate_villagers",
        spacing_seed=33,
    )

    build_underground_grotto_town()

    # Combined Village structure set (surface & underground biome-specific towns + guards)
    write_json("worldgen/structure_set/villages.json", {
        "placement": {
            "type": "minecraft:random_spread",
            "salt": 42081519,
            "separation": 7,
            "spacing": 22,
        },
        "structures": [
            {"structure": "canopycavern:crystal_citadel", "weight": 2},
            {"structure": "canopycavern:peak_citadel", "weight": 2},
            {"structure": "canopycavern:canopy_village", "weight": 2},
            {"structure": "canopycavern:grotto_outpost_town", "weight": 1},
        ],
    })
    print("Generated all 8 architectural structures + Multi-Piece Jigsaw pools + Villager Civilizations!")


if __name__ == "__main__":
    build_all()
