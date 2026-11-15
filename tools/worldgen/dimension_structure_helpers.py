#!/usr/bin/env python3
from __future__ import annotations
"""
Shared architectural builder, entity/socket validators, and MC 26.3 data writers
for Canopy Cavern's Nether and The End Jigsaw structure suites.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
import generate_v03_structures as v3
import generate_v04_ocean_and_villages as v4

RESOURCES = Path(__file__).resolve().parents[2] / "src/main/resources"
CANOPY_DATA = RESOURCES / "data/canopycavern"
MINECRAFT_DATA = RESOURCES / "data/minecraft"

EXTRA_FULL_CUBES = {
    "minecraft:blackstone",
    "minecraft:polished_blackstone",
    "minecraft:polished_blackstone_bricks",
    "minecraft:cracked_polished_blackstone_bricks",
    "minecraft:chiseled_polished_blackstone",
    "minecraft:gilded_blackstone",
    "minecraft:crying_obsidian",
    "minecraft:obsidian",
    "minecraft:nether_bricks",
    "minecraft:cracked_nether_bricks",
    "minecraft:chiseled_nether_bricks",
    "minecraft:red_nether_bricks",
    "minecraft:basalt",
    "minecraft:polished_basalt",
    "minecraft:smooth_basalt",
    "minecraft:soul_soil",
    "minecraft:soul_sand",
    "minecraft:bone_block",
    "minecraft:crimson_stem",
    "minecraft:shroomlight",
    "minecraft:glowstone",
    "minecraft:waxed_copper_grate",
    "minecraft:waxed_oxidized_copper_grate",
    "minecraft:waxed_oxidized_copper",
    "minecraft:purpur_block",
    "minecraft:purpur_pillar",
    "minecraft:end_stone",
    "minecraft:end_stone_bricks",
    "minecraft:amethyst_block",
    "minecraft:sea_lantern",
    "minecraft:tinted_glass",
}


class ExtradimensionalBuilder(v4.V4StructureBuilder):
    """Non-boxy architectural builder for Nether and End modular Jigsaw structures."""

    def __init__(self, sx: int, sy: int, sz: int, fill_block: str = "minecraft:air"):
        super().__init__(sx, sy, sz, fill_block=fill_block)
        self.oob_writes: list[tuple[int, int, int, str]] = []

    def set(self, x: int, y: int, z: int, spec, nbt: dict | None = None):
        if not (0 <= x < self.sx and 0 <= y < self.sy and 0 <= z < self.sz):
            bid = spec[0] if isinstance(spec, tuple) else spec
            self.oob_writes.append((x, y, z, str(bid)))
            return
        super().set(x, y, z, spec, nbt)

    @staticmethod
    def is_solid_cube(bid: str) -> bool:
        return bid in EXTRA_FULL_CUBES or v3.StructureBuilder._is_full_face_solid(bid)

    def _compute_connected_props(self, x: int, y: int, z: int, bid: str, props: tuple):
        if bid.endswith("_wall"):
            base = {"waterlogged": "false"}
            above_id = self.grid.get((x, y + 1, z), ("minecraft:air", ()))[0]
            has_n = self._wall_connects(x, y, z - 1)
            has_s = self._wall_connects(x, y, z + 1)
            has_e = self._wall_connects(x + 1, y, z)
            has_w = self._wall_connects(x - 1, y, z)
            straight_ns = has_n and has_s and not has_e and not has_w
            straight_ew = has_e and has_w and not has_n and not has_s
            needs_post = (above_id != "minecraft:air") or (not straight_ns and not straight_ew)
            base["up"] = "true" if needs_post else "false"
            for d_name, flag in (("north", has_n), ("south", has_s), ("east", has_e), ("west", has_w)):
                if not flag:
                    base[d_name] = "none"
                elif above_id.endswith("_wall") or self.is_solid_cube(above_id):
                    base[d_name] = "tall"
                else:
                    base[d_name] = "low"
            return tuple(sorted(base.items()))
        if bid.endswith("_fence") or bid == "minecraft:iron_bars":
            base = {"waterlogged": "false"}
            for d_name, (dx, dz) in (("north", (0, -1)), ("south", (0, 1)), ("east", (1, 0)), ("west", (-1, 0))):
                nid = self.grid.get((x + dx, y, z + dz), ("minecraft:air", ()))[0]
                connects = nid == bid or self.is_solid_cube(nid)
                base[d_name] = "true" if connects else "false"
            return tuple(sorted(base.items()))
        return super()._compute_connected_props(x, y, z, bid, props)

    def _wall_connects(self, x: int, y: int, z: int) -> bool:
        nid = self.grid.get((x, y, z), ("minecraft:air", ()))[0]
        return nid.endswith("_wall") or nid.endswith("_fence_gate") or self.is_solid_cube(nid)

    def pillar(self, x: int, y0: int, y1: int, z: int, block_id: str, axis: str = "y"):
        spec = (block_id, {"axis": axis}) if block_id in ("minecraft:purpur_pillar", "minecraft:crimson_stem", "minecraft:bone_block", "minecraft:polished_basalt") else block_id
        for y in range(y0, y1 + 1):
            self.set(x, y, z, spec)

    def soul_lantern(self, x: int, y: int, z: int, hanging: bool = False):
        self.set(x, y, z, ("minecraft:soul_lantern", {"hanging": "true" if hanging else "false", "waterlogged": "false"}))

    def iron_chain_lantern(self, x: int, ceiling_y: int, z: int, chain_len: int = 1, lantern_id: str = "minecraft:soul_lantern"):
        for dy in range(1, chain_len + 1):
            self.set(x, ceiling_y - dy, z, ("minecraft:iron_chain", {"axis": "y", "waterlogged": "false"}))
        self.set(x, ceiling_y - chain_len - 1, z, (lantern_id, {"hanging": "true", "waterlogged": "false"}))

    def end_rod(self, x: int, y: int, z: int, facing: str = "up"):
        self.set(x, y, z, ("minecraft:end_rod", {"facing": facing}))

    def grate(self, x: int, y: int, z: int, block_id: str = "minecraft:waxed_copper_grate"):
        self.set(x, y, z, (block_id, {"waterlogged": "false"}))

    def soul_campfire_hearth(self, x: int, y: int, z: int):
        self.set(x, y - 1, z, "minecraft:soul_soil")
        self.set(x, y, z, ("minecraft:soul_campfire", {"facing": "north", "lit": "true", "signal_fire": "false", "waterlogged": "false"}))

    def chamfered_rect(self, x0: int, z0: int, x1: int, z1: int, y: int, block_id: str):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if (x in (x0, x1)) and (z in (z0, z1)):
                    continue
                self.set(x, y, z, block_id)

    def stepped_vault_roof(self, x0: int, z0: int, x1: int, z1: int, y_base: int, stair_id: str, slab_id: str, ridge_id: str, accent_id: str):
        """Multi-tiered overhanging stepped roof eliminating flat cubic box silhouettes."""
        layer = 0
        while x0 + layer <= x1 - layer and z0 + layer <= z1 - layer:
            ax0, ax1 = x0 + layer, x1 - layer
            az0, az1 = z0 + layer, z1 - layer
            y = y_base + layer
            if ax1 - ax0 <= 1 and az1 - az0 <= 1:
                for x in range(ax0, ax1 + 1):
                    for z in range(az0, az1 + 1):
                        self.set(x, y, z, ridge_id)
                cx, cz = (ax0 + ax1) // 2, (az0 + az1) // 2
                self.set(cx, y + 1, cz, accent_id)
                self.slab(cx, y + 2, cz, slab_id, "bottom")
                break
            for x in range(ax0, ax1 + 1):
                for z in range(az0, az1 + 1):
                    if (x in (ax0, ax1)) and (z in (az0, az1)) and (ax1 - ax0 >= 4):
                        self.slab(x, y, z, slab_id, "bottom")
                    elif x == ax0:
                        self.stairs(x, y, z, stair_id, "east", half="bottom")
                    elif x == ax1:
                        self.stairs(x, y, z, stair_id, "west", half="bottom")
                    elif z == az0:
                        self.stairs(x, y, z, stair_id, "south", half="bottom")
                    elif z == az1:
                        self.stairs(x, y, z, stair_id, "north", half="bottom")
                    else:
                        self.set(x, y, z, ridge_id)
            layer += 1

    def build_straight_staircase(
        self,
        x_start: int,
        z: int,
        y_upper_floor: int,
        dx: int,
        stair_id: str,
        support_block: str,
        headroom: int = 4,
    ):
        """
        Builds a continuous unobstructed staircase ascending in direction `dx` (+1 or -1)
        from y=1 up to y=y_upper_floor, ending flush against solid landing `x_start + y_upper_floor * dx`.
        """
        facing = "east" if dx > 0 else "west"
        for i in range(y_upper_floor):
            sx = x_start + i * dx
            sy = 1 + i
            if sy > 1:
                self.set(sx, sy - 1, z, support_block)
            self.stairs(sx, sy, z, stair_id, facing, half="bottom")
            for clr_y in range(sy + 1, sy + headroom + 1):
                self.set(sx, clr_y, z, "minecraft:air")
        land_x = x_start + y_upper_floor * dx
        self.set(land_x, y_upper_floor, z, support_block)
        for clr_y in range(y_upper_floor + 1, y_upper_floor + headroom + 1):
            self.set(land_x, clr_y, z, "minecraft:air")

    def open_arch_portal_z(self, cx: int, y_floor: int, z: int, half_w: int, height: int, arch_stair: str, jamb_block: str, cap_block: str):
        for x in range(cx - half_w - 1, cx + half_w + 2):
            for dy in range(0, height + 2):
                if x in (cx - half_w - 1, cx + half_w + 1) or dy >= height:
                    self.set(x, y_floor + dy, z, cap_block if dy >= height else jamb_block)
                else:
                    self.set(x, y_floor + dy, z, "minecraft:air")
        self.stairs(cx - half_w, y_floor + height - 1, z, arch_stair, "east", half="top")
        self.stairs(cx + half_w, y_floor + height - 1, z, arch_stair, "west", half="top")

    def open_arch_portal_x(self, x: int, y_floor: int, cz: int, half_w: int, height: int, arch_stair: str, jamb_block: str, cap_block: str):
        for z in range(cz - half_w - 1, cz + half_w + 2):
            for dy in range(0, height + 2):
                if z in (cz - half_w - 1, cz + half_w + 1) or dy >= height:
                    self.set(x, y_floor + dy, z, cap_block if dy >= height else jamb_block)
                else:
                    self.set(x, y_floor + dy, z, "minecraft:air")
        self.stairs(x, y_floor + height - 1, cz - half_w, arch_stair, "south", half="top")
        self.stairs(x, y_floor + height - 1, cz + half_w, arch_stair, "north", half="top")

    def add_nether_mob(self, x: int, y: int, z: int, entity_id: str, extra: dict | None = None):
        self.clear_headroom(x, y, z, 3)
        nbt = {"PersistenceRequired": v3.nbt_byte(1)}
        if extra:
            nbt.update(extra)
        self.add_entity(x + 0.5, float(y), z + 0.5, entity_id, nbt)

    def add_piglin_brute(self, x: int, y: int, z: int):
        self.add_nether_mob(x, y, z, "minecraft:piglin_brute", {"CannotHunt": v3.nbt_byte(1)})

    def add_piglin_guard(self, x: int, y: int, z: int):
        self.add_nether_mob(x, y, z, "minecraft:piglin", {"CannotHunt": v3.nbt_byte(1)})

    def add_wither_skeleton(self, x: int, y: int, z: int):
        self.add_nether_mob(x, y, z, "minecraft:wither_skeleton")

    def add_blaze_guard(self, x: int, y: int, z: int):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for dy in range(0, 4):
                    self.set(x + dx, y + dy, z + dz, "minecraft:air")
        self.add_nether_mob(x, y, z, "minecraft:blaze")

    def add_shulker_guard(self, x: int, y: int, z: int, color: int = 16):
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for dy in range(0, 3):
                    self.set(x + dx, y + dy, z + dz, "minecraft:air")
        self.add_entity(
            x + 0.5,
            float(y),
            z + 0.5,
            "minecraft:shulker",
            {
                "AttachFace": v3.nbt_byte(0),
                "Peek": v3.nbt_byte(0),
                "Color": v3.nbt_byte(color),
                "PersistenceRequired": v3.nbt_byte(1),
            },
        )

    def validate_extra(self, label: str, max_guards: int = 4):
        """Validates bounds, chests, sconces, entities, headroom, and zero hazards."""
        if self.oob_writes:
            raise AssertionError(f"{label}: {len(self.oob_writes)} out-of-bounds block writes clipped (first={self.oob_writes[0]})!")
        self.validate(label, require_outdoor_sentinel=False)
        if len(self.entities) > max_guards:
            raise AssertionError(f"{label}: guard count {len(self.entities)} exceeds Vanilla-Plus cap {max_guards}!")
        for (ax, ay, az), (bid, props) in self.grid.items():
            if bid == "minecraft:soul_lantern":
                hanging = dict(props).get("hanging", "false") == "true"
                sup_y = ay + 1 if hanging else ay - 1
                sup = self.grid.get((ax, sup_y, az), ("minecraft:air", ()))[0]
                if sup in ("minecraft:air", "minecraft:water", "minecraft:lava", "minecraft:structure_void"):
                    raise AssertionError(f"{label}: soul_lantern (hanging={hanging}) at {(ax, ay, az)} lacks support ({sup})!")
            elif bid == "minecraft:end_rod":
                facing = dict(props).get("facing", "up")
                offs = {"up": (0, -1, 0), "down": (0, 1, 0), "north": (0, 0, 1), "south": (0, 0, -1), "east": (-1, 0, 0), "west": (1, 0, 0)}
                dx, dy, dz = offs.get(facing, (0, -1, 0))
                sup = self.grid.get((ax + dx, ay + dy, az + dz), ("minecraft:air", ()))[0]
                if sup == "minecraft:air":
                    raise AssertionError(f"{label}: end_rod at {(ax, ay, az)} facing={facing} floats without backing!")


def write_loot_table(name: str, pools: list[dict]):
    v4.write_ns_json(
        CANOPY_DATA,
        f"loot_table/chests/{name}.json",
        {
            "type": "minecraft:chest",
            "random_sequence": f"canopycavern:chests/{name}",
            "pools": pools,
        },
    )


def loot_item(name: str, weight: int = 1, count_min: int | None = None, count_max: int | None = None,
              enchant_levels: tuple[int, int] | None = None, potion_id: str | None = None) -> dict:
    entry: dict = {"type": "minecraft:item", "name": name, "weight": weight}
    mods = []
    if count_min is not None and count_max is not None:
        if count_min == count_max:
            mods.append({"type": "minecraft:set_count", "count": count_min})
        else:
            mods.append({"type": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": count_min, "max": count_max}})
    if enchant_levels is not None:
        mods.append({
            "type": "minecraft:enchant_with_levels",
            "levels": {"type": "minecraft:uniform", "min": enchant_levels[0], "max": enchant_levels[1]},
            "options": "#minecraft:on_random_loot",
        })
    if potion_id is not None:
        mods.append({"type": "minecraft:set_potion", "id": potion_id})
    if len(mods) == 1:
        entry["modifier"] = mods[0]
    elif len(mods) > 1:
        entry["modifier"] = mods
    return entry


def write_jigsaw_pool(rel_name: str, entries: list[tuple[str, int, str]], fallback: str = "minecraft:empty"):
    v4.write_ns_json(
        CANOPY_DATA,
        f"worldgen/template_pool/{rel_name}.json",
        {
            "elements": [
                {
                    "element": {
                        "element_type": "minecraft:single_pool_element",
                        "location": loc,
                        "processors": {"processors": []},
                        "projection": proj,
                    },
                    "weight": weight,
                }
                for loc, weight, proj in entries
            ],
            "fallback": fallback,
        },
    )


def write_biome_tag(structure_id: str, biomes: list[str]):
    v4.write_ns_json(
        CANOPY_DATA,
        f"tags/worldgen/biome/has_structure/{structure_id}.json",
        {"replace": False, "values": biomes},
    )


def write_structure_set(structure_id: str, spacing: int, separation: int, salt: int):
    v4.write_ns_json(
        CANOPY_DATA,
        f"worldgen/structure_set/{structure_id}.json",
        {
            "placement": {
                "type": "minecraft:random_spread",
                "spacing": spacing,
                "separation": separation,
                "salt": salt,
            },
            "structures": [{"structure": f"canopycavern:{structure_id}", "weight": 1}],
        },
    )
