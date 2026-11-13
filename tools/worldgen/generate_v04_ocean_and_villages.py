#!/usr/bin/env python3
from __future__ import annotations
"""
Generates v0.4.0 Ocean Mega-Structures, Loot Tables, Biome/Structure Tags,
and Luxury Revamped Vanilla Villager Civilization structures & template pools
for all 5 vanilla village themes (plains, desert, savanna, snowy, taiga).
"""

import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import generate_v03_structures as v3  # Reuse proven NbtTyped / StructureBuilder / NBT encoder

RESOURCES = Path(__file__).resolve().parents[2] / "src/main/resources"
CANOPY_DATA = RESOURCES / "data/canopycavern"
MINECRAFT_DATA = RESOURCES / "data/minecraft"
VANILLA_JAR = Path.home() / ".gradle/caches/fabric-loom/26.3/minecraft-common.jar"


def write_ns_json(root: Path, rel_path: str, payload: dict):
    out = root / rel_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")


class V4StructureBuilder(v3.StructureBuilder):
    """Extends StructureBuilder with pillar, gable/pyramid roof, villager, and sentinel helpers."""

    def clear_headroom(self, bx: int, by: int, bz: int, height: int = 2):
        for dy in range(height):
            self.set(bx, by + dy, bz, "minecraft:air")

    def add_sentinel(self, x: int, y: int, z: int, in_water: bool = False):
        if not in_water:
            self.clear_headroom(x, y, z, 2)
        self.add_entity(x + 0.5, float(y), z + 0.5, "canopycavern:village_sentinel")

    def add_golem(self, x: int, y: int, z: int):
        for dx in (-1, 0, 1):
            for dy in (0, 1, 2):
                for dz in (-1, 0, 1):
                    self.set(x + dx, y + dy, z + dz, "minecraft:air")
        self.add_entity(x + 0.5, float(y), z + 0.5, "minecraft:iron_golem")

    def add_villager(self, x: int, y: int, z: int, v_type: str, profession: str):
        self.clear_headroom(x, y, z, 2)
        self.add_entity(x + 0.5, float(y), z + 0.5, "minecraft:villager", {
            "PersistenceRequired": v3.nbt_byte(0),
            "VillagerData": {
                "level": 2,
                "profession": profession,
                "type": v_type,
            },
        })

    def add_guardian(self, x: int, y: int, z: int, elder: bool = False):
        # Ensure water space so underwater guardians spawn immersed even near shelves
        self.set(x, y, z, "minecraft:water")
        self.set(x, y + 1, z, "minecraft:water")
        ent_id = "minecraft:elder_guardian" if elder else "minecraft:guardian"
        self.add_entity(x + 0.5, float(y), z + 0.5, ent_id)

    def add_drowned(self, x: int, y: int, z: int):
        self.set(x, y, z, "minecraft:water")
        self.set(x, y + 1, z, "minecraft:water")
        self.add_entity(x + 0.5, float(y), z + 0.5, "minecraft:drowned")

    def pane_x(self, x: int, y0: int, y1: int, z: int, pane_id: str):
        for y in range(y0, y1 + 1):
            self.set(x, y, z, pane_id)

    def arch_opening(self, x0: int, x1: int, y0: int, y1: int, z: int, stair_id: str):
        """Carves a wide walk-through stone/wood arch along X at Z."""
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                self.set(x, y, z, "minecraft:air")
        self.stairs(x0, y1, z, stair_id, "west", half="top")
        self.stairs(x1, y1, z, stair_id, "east", half="top")

    def arch_opening_z(self, x: int, y0: int, y1: int, z0: int, z1: int, stair_id: str):
        for z in range(z0, z1 + 1):
            for y in range(y0, y1 + 1):
                self.set(x, y, z, "minecraft:air")
        self.stairs(x, y1, z0, stair_id, "north", half="top")
        self.stairs(x, y1, z1, stair_id, "south", half="top")

    def pitched_gable_roof(self, x0: int, x1: int, y_eave: int, z0: int, z1: int,
                           stair_id: str, ridge_id: str, slab_id: str, gable_fill_id: str | None = None):
        """Steep architectural overhanging pitched roof running along Z-axis (gables at Z ends)."""
        half_w = (x1 - x0) // 2
        for step in range(half_w + 1):
            lx = x0 + step
            rx = x1 - step
            y = y_eave + step
            for z in range(z0 - 1, z1 + 2):
                if lx == rx:
                    self.set(lx, y, z, ridge_id)
                    self.slab(lx, y + 1, z, slab_id, "bottom")
                else:
                    self.stairs(lx, y, z, stair_id, "east", half="bottom")
                    self.stairs(rx, y, z, stair_id, "west", half="bottom")
                    # Decorative upside-down eave cornice trim on outermost overhang
                    if step == 0 and (z == z0 - 1 or z == z1 + 1):
                        self.stairs(lx, y - 1, z, stair_id, "east", half="top")
                        self.stairs(rx, y - 1, z, stair_id, "west", half="top")
            if gable_fill_id and lx < rx - 1:
                for gz in (z0, z1):
                    for ix in range(lx + 1, rx):
                        self.set(ix, y, gz, gable_fill_id)

    def hipped_pyramid_roof(self, x0: int, x1: int, y_base: int, z0: int, z1: int,
                            block_id: str, stair_id: str, slab_id: str):
        """Multi-tiered luxury hipped/pyramidal pavilion roof with stair edges."""
        layer = 0
        while x0 + layer <= x1 - layer and z0 + layer <= z1 - layer:
            ax0, ax1 = x0 + layer, x1 - layer
            az0, az1 = z0 + layer, z1 - layer
            y = y_base + layer
            if ax0 == ax1 and az0 == az1:
                self.set(ax0, y, az0, block_id)
                self.set(ax0, y + 1, az0, "minecraft:lightning_rod")
                break
            for x in range(ax0, ax1 + 1):
                for z in range(az0, az1 + 1):
                    if x == ax0:
                        self.stairs(x, y, z, stair_id, "east", half="bottom")
                    elif x == ax1:
                        self.stairs(x, y, z, stair_id, "west", half="bottom")
                    elif z == az0:
                        self.stairs(x, y, z, stair_id, "south", half="bottom")
                    elif z == az1:
                        self.stairs(x, y, z, stair_id, "north", half="bottom")
                    else:
                        self.set(x, y, z, block_id)
            if ax1 - ax0 <= 2 and az1 - az0 <= 2:
                # Cap crown
                for x in range(ax0, ax1 + 1):
                    for z in range(az0, az1 + 1):
                        self.slab(x, y + 1, z, slab_id, "bottom")
                self.set((ax0 + ax1) // 2, y + 1, (az0 + az1) // 2, "minecraft:sea_lantern" if "copper" in block_id else block_id)
                break
            layer += 1

    def validate(self, label: str, require_outdoor_sentinel: bool = False):
        """Verifies every entity has solid footing and clear headroom/water."""
        for ent in self.entities:
            bx, by, bz = [int(v.value if isinstance(v, v3.NbtTyped) else v) for v in ent["blockPos"].value]
            eid = ent["nbt"]["id"]
            if by <= 0:
                raise AssertionError(f"{label}: entity {eid} at y={by} lacks floor beneath!")
            below = self.grid.get((bx, by - 1, bz), ("minecraft:air", ()))[0]
            if eid in ("minecraft:guardian", "minecraft:elder_guardian", "minecraft:drowned"):
                continue
            if below in ("minecraft:air", "minecraft:water", "minecraft:lava", "minecraft:structure_void",
                         "minecraft:campfire", "minecraft:soul_campfire", "minecraft:magma_block", "minecraft:cactus"):
                raise AssertionError(f"{label}: land entity {eid} at {(bx, by, bz)} has unsafe below={below}")
            at_pos = self.grid.get((bx, by, bz), ("minecraft:air", ()))[0]
            above = self.grid.get((bx, by + 1, bz), ("minecraft:air", ()))[0]
            if at_pos != "minecraft:air" or above != "minecraft:air":
                raise AssertionError(f"{label}: entity {eid} suffocating at {(bx, by, bz)} ({at_pos}, {above})")
            if eid == "minecraft:iron_golem":
                for dx in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        g_floor = self.grid.get((bx + dx, by - 1, bz + dz), ("minecraft:air", ()))[0]
                        if g_floor in ("minecraft:air", "minecraft:water", "minecraft:lava", "minecraft:structure_void"):
                            raise AssertionError(f"{label}: iron_golem missing 3x3 floor support at {(bx+dx, by-1, bz+dz)} ({g_floor})")
                        for dy in (0, 1, 2):
                            cell = self.grid.get((bx + dx, by + dy, bz + dz), ("minecraft:air", ()))[0]
                            if cell != "minecraft:air":
                                raise AssertionError(f"{label}: iron_golem hitbox obstructed at {(bx+dx, by+dy, bz+dz)} by {cell}")
        if require_outdoor_sentinel:
            sentinels = [e for e in self.entities if e["nbt"]["id"] == "canopycavern:village_sentinel"]
            if len(sentinels) < 2:
                raise AssertionError(f"{label}: expected >=2 sentinels, found {len(sentinels)}")
            for e in sentinels:
                by_s = int(e["blockPos"].value[1])
                if by_s > 2 and "reef_lighthouse_keep" not in label:
                    raise AssertionError(f"{label}: sentinel at elevated y={by_s}; keep sentinels at ground level!")
        # Validate every horizontal appliance / container faces open air (never backwards into a wall!)
        facing_dirs = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
        appliances = {"minecraft:smoker", "minecraft:blast_furnace", "minecraft:furnace", "minecraft:lectern", "minecraft:chest"}
        for (ax, ay, az), (bid, props) in self.grid.items():
            if bid in appliances:
                prop_dict = dict(props)
                f = prop_dict.get("facing")
                if f not in facing_dirs:
                    raise AssertionError(f"{label}: {bid} at {(ax, ay, az)} missing explicit facing property!")
                dx, dz = facing_dirs[f]
                front = self.grid.get((ax + dx, ay, az + dz), ("minecraft:air", ()))[0]
                if front not in ("minecraft:air", "minecraft:water", "minecraft:structure_void"):
                    raise AssertionError(f"{label}: {bid} at {(ax, ay, az)} facing={f} blocked by {front}!")
            elif bid == "minecraft:bell":
                att = dict(props).get("attachment", "floor")
                if att == "ceiling":
                    sup = self.grid.get((ax, ay + 1, az), ("minecraft:air", ()))[0]
                    if sup in ("minecraft:air", "minecraft:water", "minecraft:structure_void"):
                        raise AssertionError(f"{label}: ceiling bell at {(ax, ay, az)} has air above ({sup})!")
            elif bid == "minecraft:lantern":
                hanging = dict(props).get("hanging", "false") == "true"
                sup_y = ay + 1 if hanging else ay - 1
                sup = self.grid.get((ax, sup_y, az), ("minecraft:air", ()))[0]
                if sup in ("minecraft:air", "minecraft:water", "minecraft:structure_void"):
                    raise AssertionError(f"{label}: lantern (hanging={hanging}) at {(ax, ay, az)} lacks support at y={sup_y} ({sup})!")
            elif bid == "minecraft:ladder":
                f = dict(props).get("facing")
                if f in facing_dirs:
                    dx, dz = facing_dirs[f]
                    back = self.grid.get((ax - dx, ay, az - dz), ("minecraft:air", ()))[0]
                    if back in ("minecraft:air", "minecraft:water", "minecraft:structure_void"):
                        raise AssertionError(f"{label}: ladder at {(ax, ay, az)} facing={f} lacks solid back wall ({back})!")

    def verify_watertight(self, label: str, dry_seeds: list[tuple[int, int, int]], allowed_portals: set[tuple[int, int, int]] = frozenset()):
        """6-neighbor flood-fill from dry interior seeds to verify no dry air leaks to water/void/OOB."""
        from collections import deque
        visited = set()
        queue = deque()
        for seed in dry_seeds:
            sx, sy, sz = seed
            if not (0 <= sx < self.sx and 0 <= sy < self.sy and 0 <= sz < self.sz):
                raise AssertionError(f"{label}: seed {seed} out of bounds!")
            bid = self.grid.get(seed, ("minecraft:structure_void", ()))[0]
            if bid in ("minecraft:structure_void", "minecraft:water", "minecraft:lava"):
                raise AssertionError(f"{label}: dry seed {seed} is not dry ({bid})!")
            visited.add(seed)
            queue.append(seed)

        while queue:
            x, y, z = queue.popleft()
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                nx, ny, nz = x + dx, y + dy, z + dz
                if not (0 <= nx < self.sx and 0 <= ny < self.sy and 0 <= nz < self.sz):
                    if (x, y, z) in allowed_portals:
                        continue
                    raise AssertionError(f"{label}: dry cavity leaks out-of-bounds from {(x, y, z)} -> {(nx, ny, nz)}")
                nbid, nprops = self.grid.get((nx, ny, nz), ("minecraft:structure_void", ()))
                if nbid in ("minecraft:structure_void", "minecraft:water", "minecraft:lava"):
                    if (x, y, z) in allowed_portals:
                        continue
                    raise AssertionError(f"{label}: water leak! Dry cell {(x, y, z)} touches {nbid} at {(nx, ny, nz)}")
                is_closed_door = nbid.endswith("_door") and dict(nprops).get("open", "false") == "false"
                if self._is_full_face_solid(nbid) or is_closed_door:
                    continue
                if (nx, ny, nz) not in visited:
                    visited.add((nx, ny, nz))
                    queue.append((nx, ny, nz))

    def shift_vertical(self, shift_y: int):
        self.grid = {(x, y + shift_y, z): value for (x, y, z), value in self.grid.items()}
        self.block_nbts = {(x, y + shift_y, z): nbt
                           for (x, y, z), nbt in self.block_nbts.items()}
        self.sy += shift_y
        for ent in self.entities:
            px, py, pz = ent["pos"].value
            bx, by, bz = ent["blockPos"].value
            ent["pos"] = v3.nbt_double_list([px, py + float(shift_y), pz])
            ent["blockPos"] = v3.nbt_int_list([bx, by + shift_y, bz])

    def extend_seabed_foundation(self, shift_y: int = 6, pier_block: str = "minecraft:polished_deepslate", foot_block: str = "minecraft:basalt"):
        """Shifts structure up by shift_y and extrudes sturdy tapered piers from lowest solid down to y=0."""
        self.shift_vertical(shift_y)
        lowest_solid = {}
        for (x, y, z), (block_id, _) in self.grid.items():
            if block_id not in ("minecraft:air", "minecraft:structure_void", "minecraft:water", "minecraft:lava"):
                lowest_solid[x, z] = min(y, lowest_solid.get((x, z), y))
        # Extrude vertical pier/skirt down to y=0 beneath every structural footprint column
        for (x, z), ly in lowest_solid.items():
            # Include thin horizontal tunnel bridges too, tapering lightly for natural mound look
            for yy in range(0, ly):
                blk = foot_block if yy <= 2 else pier_block
                if (x, yy, z) not in self.grid:
                    self.set(x, yy, z, blk)
        # Subtle radial rock skirt at y=0..2 around outer base
        base_cols = list(lowest_solid.items())
        for (x, z), ly in base_cols:
            if ly <= shift_y + 3:
                for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nx, nz = x + dx, z + dz
                    if 0 <= nx < self.sx and 0 <= nz < self.sz and (nx, nz) not in lowest_solid:
                        for yy in range(0, 2):
                            if (nx, yy, nz) not in self.grid:
                                self.set(nx, yy, nz, foot_block)


# ===========================================================================
# 1. OCEAN MEGA-STRUCTURES (v0.4.0 Centerpiece)
# ===========================================================================
def build_sunken_citadel_vault():
    # Central Vault Cathedral (29 x 23 x 29)
    sb = V4StructureBuilder(29, 23, 29, fill_block="minecraft:structure_void")

    # Monumental dark prismarine stepped island plinth & outer forecourt floor (organic chamfered skirt)
    cx_v, cz_v = 14, 14
    for x in range(1, 28):
        for z in range(1, 28):
            manh = abs(x - cx_v) + abs(z - cz_v)
            if manh <= 22:
                sb.set(x, 0, z, "minecraft:dark_prismarine")
            if 2 <= x <= 26 and 2 <= z <= 26 and manh <= 21:
                sb.set(x, 1, z, "minecraft:dark_prismarine")
    sb.fill(3, 2, 3, 25, 2, 25, "minecraft:prismarine_bricks")

    # 4 Graceful Slender Aquatic Corner Obelisk Spires (prismarine walls + copper + sea lanterns)
    for cx, cz in [(2, 2), (26, 2), (2, 26), (26, 26)]:
        sb.fill(cx - 1, 0, cz - 1, cx + 1, 3, cz + 1, "minecraft:dark_prismarine")
        sb.fill(cx, 4, cz, cx, 10, cz, "minecraft:prismarine_bricks")
        for ox, oz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            for wy in range(4, 9):
                sb.set(cx + ox, wy, cz + oz, "minecraft:prismarine_wall")
        sb.set(cx, 11, cz, "minecraft:sea_lantern")
        sb.fill(cx, 12, cz, cx, 13, cz, "minecraft:oxidized_copper")
        sb.set(cx, 14, cz, "minecraft:lightning_rod")

    # Outer flooded grand colonnade arches around the sanctum
    for p in (4, 8, 12, 16, 20, 24):
        for y in range(3, 9):
            sb.set(p, y, 2, "minecraft:dark_prismarine")
            sb.set(p, y, 26, "minecraft:dark_prismarine")
            sb.set(2, y, p, "minecraft:dark_prismarine")
            sb.set(26, y, p, "minecraft:dark_prismarine")
        sb.set(p, 8, 2, "minecraft:sea_lantern")
        sb.set(p, 8, 26, "minecraft:sea_lantern")
        sb.set(2, 8, p, "minecraft:sea_lantern")
        sb.set(26, 8, p, "minecraft:sea_lantern")
    for i in range(3, 26):
        sb.set(i, 9, 2, "minecraft:oxidized_cut_copper")
        sb.set(i, 9, 26, "minecraft:oxidized_cut_copper")
        sb.set(2, 9, i, "minecraft:oxidized_cut_copper")
        sb.set(26, 9, i, "minecraft:oxidized_cut_copper")

    # Central Sealed DRY Sanctum Citadel Hall (x=6..22, y=3..11, z=6..22)
    sb.hollow_box(6, 3, 6, 22, 11, 22, "minecraft:dark_prismarine", fill_spec="minecraft:air")
    # Interior vaulted corbel ring at y=11 (max==7) so sloped pyramid roof joins seamlessly without gaps
    for x in range(7, 22):
        for z in range(7, 22):
            if max(abs(x - cx_v), abs(z - cz_v)) == 7:
                sb.set(x, 11, z, "minecraft:dark_prismarine")
            else:
                sb.set(x, 11, z, "minecraft:air")
    # Panoramic Cyan Glass Arch Windows along dry vault walls (keeps air inside 100% sealed!)
    for d in (8, 9, 11, 12, 16, 17, 19, 20):
        for y in range(5, 10):
            sb.set(d, y, 6, "minecraft:cyan_stained_glass")
            sb.set(d, y, 22, "minecraft:cyan_stained_glass")
            sb.set(6, y, d, "minecraft:cyan_stained_glass")
            sb.set(22, y, d, "minecraft:cyan_stained_glass")
    # Oxidized copper buttress ribs
    for rx in (6, 10, 14, 18, 22):
        for y in range(3, 12):
            sb.set(rx, y, 6, "minecraft:oxidized_copper")
            sb.set(rx, y, 22, "minecraft:oxidized_copper")
            sb.set(6, y, rx, "minecraft:oxidized_copper")
            sb.set(22, y, rx, "minecraft:oxidized_copper")

    # Smooth Mitered Stair-Clad Pyramid Roof + Watertight Vaulted Backing + Copper Crown (y=12..21)
    for dy in range(6):
        r = 8 - dy
        y = 12 + dy
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                x, z = cx_v + dx, cz_v + dz
                m = max(abs(dx), abs(dz))
                if m == r:
                    is_rib = (dx == 0 or dz == 0 or abs(dx) == abs(dz))
                    st_id = "minecraft:oxidized_cut_copper_stairs" if is_rib else "minecraft:dark_prismarine_stairs"
                    if dx == -r and dz == -r:
                        sb.stairs(x, y, z, st_id, "south", "bottom", "outer_left")
                    elif dx == r and dz == -r:
                        sb.stairs(x, y, z, st_id, "south", "bottom", "outer_right")
                    elif dx == -r and dz == r:
                        sb.stairs(x, y, z, st_id, "north", "bottom", "outer_right")
                    elif dx == r and dz == r:
                        sb.stairs(x, y, z, st_id, "north", "bottom", "outer_left")
                    elif dx == -r:
                        sb.stairs(x, y, z, st_id, "east", "bottom")
                    elif dx == r:
                        sb.stairs(x, y, z, st_id, "west", "bottom")
                    elif dz == -r:
                        sb.stairs(x, y, z, st_id, "south", "bottom")
                    else:
                        sb.stairs(x, y, z, st_id, "north", "bottom")
                elif m in (r - 1, r - 2) and m >= 2:
                    sb.set(x, y, z, "minecraft:oxidized_copper" if (dx == 0 or dz == 0) else "minecraft:dark_prismarine")
                elif dy == 5 and m <= 1:
                    sb.set(x, y, z, "minecraft:cyan_stained_glass")
                else:
                    sb.set(x, y, z, "minecraft:air")

    # Crown Cupola (y=18..22)
    for x in range(12, 17):
        for z in range(12, 17):
            m = max(abs(x - cx_v), abs(z - cz_v))
            if m == 2:
                sb.slab(x, 18, z, "minecraft:oxidized_cut_copper_slab", "bottom")
            elif m == 1:
                sb.set(x, 18, z, "minecraft:oxidized_copper")
    sb.set(14, 18, 14, "minecraft:gold_block")
    sb.set(14, 19, 14, "minecraft:sea_lantern")
    sb.set(14, 20, 14, "minecraft:lightning_rod")

    # Richly Detailed Dry Interior Sanctum (floor y=3, air y=4..16)
    sb.fill(7, 3, 7, 21, 3, 21, "minecraft:prismarine_bricks")
    sb.fill(11, 3, 11, 17, 3, 17, "minecraft:oxidized_chiseled_copper")
    sb.fill(13, 4, 13, 15, 4, 15, "minecraft:dark_prismarine")
    # Central Sacred Altar Monument + Hanging Chandelier attached directly to cyan_stained_glass skylight at y=17
    sb.set(14, 5, 14, "minecraft:gold_block")
    sb.set(14, 6, 14, "minecraft:sea_lantern")
    sb.set(14, 7, 14, "minecraft:emerald_block")
    for ch_y in range(12, 17):
        sb.set(14, ch_y, 14, "minecraft:iron_chain")
    sb.set(14, 10, 14, "minecraft:sea_lantern")
    for ox, oz in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        sb.set(14 + ox, 11, 14 + oz, "minecraft:sea_lantern")
    # Mezzanine Balcony Ring (y=8) + North Access Stairs up to Mezzanine
    for x in range(7, 22):
        for z in range(7, 22):
            if x <= 9 or x >= 19 or z <= 9 or z >= 19:
                if (x, z) not in [(14, 9), (14, 19), (9, 14), (19, 14)]:
                    sb.set(x, 8, z, "minecraft:dark_prismarine_slab")
    for step in range(4):
        sx = 11 + step
        if step > 0:
            sb.fill(sx, 4, 8, sx, 4 + step - 1, 8, "minecraft:dark_prismarine")
        sb.stairs(sx, 4 + step, 8, "minecraft:prismarine_brick_stairs", "east")
    for hx in (12, 13, 14):
        sb.set(hx, 8, 8, "minecraft:air")
    sb.set(15, 8, 8, "minecraft:prismarine_bricks")
    # 4 Dry Treasure Vault Chests + Craft/Brewing Shrine
    sb.chest(11, 4, 11, "south", "canopycavern:chests/sunken_citadel")
    sb.chest(17, 4, 11, "south", "canopycavern:chests/sunken_citadel")
    sb.chest(11, 4, 17, "north", "canopycavern:chests/sunken_citadel")
    sb.chest(17, 4, 17, "north", "canopycavern:chests/sunken_citadel")
    sb.set(9, 4, 14, "minecraft:brewing_stand")
    sb.set(19, 4, 14, "minecraft:enchanting_table")
    # Sculpted South Airlock Vestibule Portal (watertight warped_door at z=22 + prismarine portico out to z=24)
    sb.fill(13, 3, 23, 15, 3, 24, "minecraft:prismarine_bricks")
    for px in (12, 16):
        sb.fill(px, 3, 23, px, 7, 23, "minecraft:oxidized_copper")
        sb.set(px, 5, 24, "minecraft:sea_lantern")
    sb.fill(13, 6, 22, 15, 7, 22, "minecraft:cyan_stained_glass")
    sb.fill(13, 4, 22, 15, 5, 22, "minecraft:prismarine_bricks")
    sb.door(14, 4, 22, "minecraft:warped_door", "south")
    sb.fill(13, 8, 23, 15, 8, 23, "minecraft:oxidized_cut_copper_slab")

    # Flooded Outer Portico Guardians + Elder Sentinel Boss
    sb.add_guardian(4, 5, 4, elder=False)
    sb.add_guardian(24, 5, 4, elder=False)
    sb.add_guardian(4, 5, 24, elder=False)
    sb.add_guardian(24, 5, 24, elder=False)
    sb.add_guardian(14, 6, 26, elder=True)

    # 3 Jigsaw Connectors on Outer Wings
    sb.jigsaw(0, 3, 14, "west_up", "canopycavern:citadel_wing", "canopycavern:citadel_wing",
              "canopycavern:sunken_citadel_vault/wings", "minecraft:water", "aligned")
    sb.jigsaw(28, 3, 14, "east_up", "canopycavern:citadel_wing", "canopycavern:citadel_wing",
              "canopycavern:sunken_citadel_vault/wings", "minecraft:water", "aligned")
    sb.jigsaw(14, 3, 0, "north_up", "canopycavern:citadel_wing", "canopycavern:citadel_wing",
              "canopycavern:sunken_citadel_vault/wings", "minecraft:water", "aligned")
    sb.validate("sunken_citadel_vault/central_vault")
    sb.verify_watertight("sunken_citadel_vault/central_vault", [(14, 5, 16)])
    sb.extend_seabed_foundation(6, pier_block="minecraft:dark_prismarine", foot_block="minecraft:cobbled_deepslate")
    sb.save("sunken_citadel_vault/central_vault.nbt")

    # Wing 1: Dry Prismarine Colonnade Sanctuary Wing (15 x 14 x 15)
    wg = V4StructureBuilder(15, 14, 15, fill_block="minecraft:structure_void")
    wg.fill(1, 0, 0, 13, 2, 13, "minecraft:dark_prismarine")
    wg.hollow_box(3, 2, 2, 11, 9, 12, "minecraft:prismarine_bricks", fill_spec="minecraft:air")
    for x in (3, 7, 11):
        for y in range(3, 10):
            wg.set(x, y, 2, "minecraft:oxidized_copper")
            wg.set(x, y, 12, "minecraft:oxidized_copper")
    for y in range(4, 8):
        wg.set(3, y, 7, "minecraft:cyan_stained_glass")
        wg.set(11, y, 7, "minecraft:cyan_stained_glass")
    wg.hipped_pyramid_roof(3, 11, 10, 2, 12, "minecraft:dark_prismarine", "minecraft:dark_prismarine_stairs", "minecraft:oxidized_cut_copper_slab")
    # Flooded welcome path z=0..1 + Sealed Warped Door entrance at z=2
    wg.fill(6, 2, 0, 8, 2, 1, "minecraft:prismarine_bricks")
    wg.set(6, 4, 1, "minecraft:sea_lantern")
    wg.set(8, 4, 1, "minecraft:sea_lantern")
    wg.door(7, 3, 2, "minecraft:warped_door", "north")
    wg.set(7, 5, 2, "minecraft:cyan_stained_glass")
    wg.chest(7, 3, 10, "north", "canopycavern:chests/sunken_citadel")
    wg.chest(5, 3, 7, "east", "canopycavern:chests/sunken_citadel")
    wg.set(9, 3, 7, "minecraft:gold_block")
    wg.set(7, 4, 7, "minecraft:sea_lantern")
    wg.add_guardian(1, 5, 7, elder=False)
    wg.add_guardian(13, 5, 7, elder=False)
    wg.jigsaw(7, 3, 0, "north_up", "canopycavern:citadel_wing", "canopycavern:citadel_wing",
              "minecraft:empty", "minecraft:water", "aligned")
    wg.validate("sunken_citadel_vault/colonnade_wing")
    wg.verify_watertight("sunken_citadel_vault/colonnade_wing", [(7, 4, 7)])
    wg.extend_seabed_foundation(6, pier_block="minecraft:dark_prismarine", foot_block="minecraft:cobbled_deepslate")
    wg.save("sunken_citadel_vault/colonnade_wing.nbt")

    # Wing 2: Trident Spire Treasury Tower (13 x 20 x 13)
    sp = V4StructureBuilder(13, 20, 13, fill_block="minecraft:structure_void")
    sp.fill(1, 0, 0, 11, 2, 11, "minecraft:dark_prismarine")
    sp.hollow_box(3, 2, 3, 9, 13, 9, "minecraft:prismarine_bricks", fill_spec="minecraft:air")
    sp.fill(5, 14, 5, 7, 16, 7, "minecraft:oxidized_copper")
    sp.set(6, 17, 6, "minecraft:sea_lantern")
    sp.set(6, 18, 6, "minecraft:gold_block")
    sp.set(6, 19, 6, "minecraft:lightning_rod")
    for y in range(4, 12, 3):
        sp.set(3, y, 6, "minecraft:tinted_glass")
        sp.set(9, y, 6, "minecraft:tinted_glass")
        sp.set(6, y, 9, "minecraft:sea_lantern")
    # Sealed Warped Door entrance at z=3 + Causeway approach z=0..2
    sp.fill(5, 2, 0, 7, 2, 2, "minecraft:prismarine_bricks")
    sp.set(5, 4, 2, "minecraft:sea_lantern")
    sp.set(7, 4, 2, "minecraft:sea_lantern")
    sp.door(6, 3, 3, "minecraft:warped_door", "north")
    sp.set(6, 5, 3, "minecraft:cyan_stained_glass")
    sp.chest(6, 3, 7, "north", "canopycavern:chests/sunken_citadel")
    sp.add_guardian(2, 6, 10, elder=False)
    sp.add_guardian(10, 6, 10, elder=False)
    sp.jigsaw(6, 3, 0, "north_up", "canopycavern:citadel_wing", "canopycavern:citadel_wing",
              "minecraft:empty", "minecraft:water", "aligned")
    sp.validate("sunken_citadel_vault/sanctum_spire")
    sp.verify_watertight("sunken_citadel_vault/sanctum_spire", [(6, 4, 6)])
    sp.extend_seabed_foundation(6, pier_block="minecraft:dark_prismarine", foot_block="minecraft:cobbled_deepslate")
    sp.save("sunken_citadel_vault/sanctum_spire.nbt")


def build_abyssal_thermal_observatory():
    # Main Geodesic Hydrothermal Observatory Dome (25 x 19 x 25)
    ob = V4StructureBuilder(25, 19, 25, fill_block="minecraft:structure_void")
    cx, cz = 12, 12

    # Organic Radial Geothermal Basalt & Magma Seafloor Mound (y=0..2)
    for x in range(1, 24):
        for z in range(1, 24):
            d2 = (x - cx) ** 2 + (z - cz) ** 2
            if d2 <= 112:
                ob.set(x, 0, z, "minecraft:blackstone" if (x * 7 + z * 11) % 5 == 0 else "minecraft:basalt")
            if d2 <= 94:
                is_vent = (x == cx or z == cz) and (70 <= d2 <= 90)
                ob.set(x, 1, z, "minecraft:magma_block" if is_vent else "minecraft:basalt")
            if d2 <= 74:
                ob.set(x, 2, z, "minecraft:polished_deepslate")

    # True 3D Spherical Underwater Dome Shell (6-connected watertight skin from 26-neighbor boundary!)
    def in_dome(x: int, y: int, z: int) -> bool:
        d2 = (x - cx) ** 2 + (z - cz) ** 2
        if 3 <= y <= 9:
            return d2 <= 66
        if 10 <= y <= 17:
            return d2 + (y - 9) ** 2 <= 66.5
        return False

    for x in range(3, 22):
        for z in range(3, 22):
            if (x - cx) ** 2 + (z - cz) ** 2 <= 66:
                ob.set(x, 3, z, "minecraft:polished_deepslate")
            for y in range(4, 18):
                if not in_dome(x, y, z):
                    continue
                is_skin = any(
                    not in_dome(x + dx, y + dy, z + dz)
                    for dx in (-1, 0, 1)
                    for dy in (-1, 0, 1)
                    for dz in (-1, 0, 1)
                    if (dx or dy or dz)
                )
                if is_skin:
                    is_rib = (x == cx or z == cz or abs(x - cx) == abs(z - cz))
                    if y in (4, 9):
                        ob.set(x, y, z, "minecraft:copper_block" if is_rib else "minecraft:cut_copper")
                    elif is_rib:
                        ob.set(x, y, z, "minecraft:oxidized_copper")
                    else:
                        ob.set(x, y, z, "minecraft:cyan_stained_glass" if y >= 11 else "minecraft:tinted_glass")
                else:
                    ob.set(x, y, z, "minecraft:air")

    ob.set(cx, 17, cz, "minecraft:sea_lantern")
    ob.set(cx, 18, cz, "minecraft:lightning_rod")

    # Punch 3 Seamless Pressurized Docking Tunnel Necks flush out to Jigsaws (0,4,12), (24,4,12), (12,4,0)
    def build_neck_x(x_range):
        for x in x_range:
            rib = (x % 3 == 0)
            for z in range(10, 15):
                ob.set(x, 1, z, "minecraft:basalt")
                ob.set(x, 2, z, "minecraft:polished_deepslate")
                ob.set(x, 3, z, "minecraft:polished_deepslate")
                if z in (10, 14):
                    wall = "minecraft:cut_copper" if rib else "minecraft:glass"
                    for y in (4, 5, 6):
                        ob.set(x, y, z, wall)
                    ob.set(x, 7, z, "minecraft:cut_copper")
                else:
                    for y in (4, 5, 6):
                        ob.set(x, y, z, "minecraft:air")
                    ob.set(x, 7, z, "minecraft:sea_lantern" if (rib and z == 12) else ("minecraft:cut_copper" if rib else "minecraft:glass"))

    def build_neck_z(z_range):
        for z in z_range:
            rib = (z % 3 == 0)
            for x in range(10, 15):
                ob.set(x, 1, z, "minecraft:basalt")
                ob.set(x, 2, z, "minecraft:polished_deepslate")
                ob.set(x, 3, z, "minecraft:polished_deepslate")
                if x in (10, 14):
                    wall = "minecraft:cut_copper" if rib else "minecraft:glass"
                    for y in (4, 5, 6):
                        ob.set(x, y, z, wall)
                    ob.set(x, 7, z, "minecraft:cut_copper")
                else:
                    for y in (4, 5, 6):
                        ob.set(x, y, z, "minecraft:air")
                    ob.set(x, 7, z, "minecraft:sea_lantern" if (rib and x == 12) else ("minecraft:cut_copper" if rib else "minecraft:glass"))

    build_neck_x(range(0, 7))
    build_neck_x(range(18, 25))
    build_neck_z(range(0, 7))

    # Central Thermal Conduit Core (magma heat column encased in glass inside dry hall)
    for y in range(3, 14):
        ob.set(cx, y, cz, "minecraft:magma_block" if y < 6 else "minecraft:sea_lantern")
        for dx, dz in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ob.set(cx + dx, y, cz + dz, "minecraft:tinted_glass")
    # Second Floor Catwalk Mezzanine (y=8) + Walkable Copper Access Stairs along z=16
    for x in range(7, 18):
        for z in range(7, 18):
            d2 = (x - cx) ** 2 + (z - cz) ** 2
            if 14 <= d2 <= 36:
                ob.set(x, 8, z, "minecraft:waxed_cut_copper_slab")
    for step in range(4):
        sx = 10 + step
        if step > 0:
            ob.fill(sx, 4, 16, sx, 4 + step - 1, 16, "minecraft:polished_deepslate")
        ob.stairs(sx, 4 + step, 16, "minecraft:cut_copper_stairs", "east")
    for hx in (11, 12, 13):
        ob.set(hx, 8, 16, "minecraft:air")
    ob.set(14, 8, 16, "minecraft:cut_copper")

    # Laboratory Workstations & 3 Observatory Chests
    ob.chest(9, 4, 9, "south", "canopycavern:chests/thermal_observatory")
    ob.chest(15, 4, 9, "south", "canopycavern:chests/thermal_observatory")
    ob.chest(12, 9, 8, "south", "canopycavern:chests/thermal_observatory")
    ob.set(8, 4, 14, "minecraft:crafting_table")
    ob.set(9, 4, 15, "minecraft:brewing_stand")
    ob.set(15, 4, 14, ("minecraft:lectern", {"facing": "west", "has_book": "false"}))
    ob.bed(15, 4, 15, "minecraft:cyan_bed", "south")
    ob.add_guardian(4, 5, 4, elder=False)
    ob.add_guardian(20, 5, 20, elder=False)

    # 3 Flush Docking Tunnel Connectors (final_state=air so players walk straight into tubes!)
    ob.jigsaw(0, 4, 12, "west_up", "canopycavern:obs_tunnel", "canopycavern:obs_tunnel",
              "canopycavern:abyssal_thermal_observatory/tunnels", "minecraft:air", "aligned")
    ob.jigsaw(24, 4, 12, "east_up", "canopycavern:obs_tunnel", "canopycavern:obs_tunnel",
              "canopycavern:abyssal_thermal_observatory/tunnels", "minecraft:air", "aligned")
    ob.jigsaw(12, 4, 0, "north_up", "canopycavern:obs_tunnel", "canopycavern:obs_tunnel",
              "canopycavern:abyssal_thermal_observatory/tunnels", "minecraft:air", "aligned")

    main_portals = (
        {(0, y, z) for y in (4, 5, 6) for z in (11, 12, 13)}
        | {(24, y, z) for y in (4, 5, 6) for z in (11, 12, 13)}
        | {(x, y, 0) for y in (4, 5, 6) for x in (11, 12, 13)}
    )
    ob.validate("abyssal_thermal_observatory/main_dome")
    ob.verify_watertight("abyssal_thermal_observatory/main_dome", [(12, 5, 15)], main_portals)
    ob.save("abyssal_thermal_observatory/main_dome.nbt")

    # Pressurized Glass-Copper Underwater Tunnel Bridge (7 x 8 x 11) - aligned flush to y=3 floor!
    tu = V4StructureBuilder(7, 8, 11, fill_block="minecraft:structure_void")
    for z in range(11):
        rib = (z % 3 == 0)
        wall = "minecraft:cut_copper" if rib else "minecraft:glass"
        for x in range(1, 6):
            tu.set(x, 2, z, "minecraft:polished_deepslate")
            tu.set(x, 3, z, "minecraft:polished_deepslate")
            if x in (1, 5):
                for y in (4, 5, 6):
                    tu.set(x, y, z, wall)
                tu.set(x, 7, z, "minecraft:cut_copper")
            else:
                for y in (4, 5, 6):
                    tu.set(x, y, z, "minecraft:air")
                tu.set(x, 7, z, "minecraft:sea_lantern" if (rib and x == 3) else ("minecraft:cut_copper" if rib else "minecraft:glass"))
    tu.jigsaw(3, 4, 0, "north_up", "canopycavern:obs_tunnel", "canopycavern:obs_tunnel",
              "minecraft:empty", "minecraft:air", "aligned")
    tu.jigsaw(3, 4, 10, "south_up", "canopycavern:obs_pod", "canopycavern:obs_pod",
              "canopycavern:abyssal_thermal_observatory/pods", "minecraft:air", "aligned")
    tu_portals = {(x, y, z) for x in (2, 3, 4) for y in (4, 5, 6) for z in (0, 10)}
    tu.verify_watertight("abyssal_thermal_observatory/copper_tunnel_bridge", [(3, 5, 5)], tu_portals)
    tu.save("abyssal_thermal_observatory/copper_tunnel_bridge.nbt")

    # Airlock Pod (11 x 11 x 11) - flush y=3 floor & sealed z=0..2 docking collar
    ap = V4StructureBuilder(11, 11, 11, fill_block="minecraft:structure_void")
    ap.fill(1, 1, 1, 9, 3, 9, "minecraft:polished_deepslate")
    ap.hollow_box(2, 3, 2, 8, 8, 8, "minecraft:cut_copper", fill_spec="minecraft:air")
    for p in range(3, 8):
        for y in range(4, 7):
            ap.set(2, y, p, "minecraft:tinted_glass")
            ap.set(8, y, p, "minecraft:tinted_glass")
            ap.set(p, y, 8, "minecraft:tinted_glass")
    ap.fill(3, 8, 3, 7, 8, 7, "minecraft:cyan_stained_glass")
    ap.set(5, 9, 5, "minecraft:sea_lantern")
    # Flush docking collar z=0..2 connecting tunnel to pod
    for z in range(0, 3):
        ap.fill(3, 2, z, 7, 3, z, "minecraft:polished_deepslate")
        ap.fill(3, 4, z, 3, 7, z, "minecraft:cut_copper")
        ap.fill(7, 4, z, 7, 7, z, "minecraft:cut_copper")
        ap.fill(4, 7, z, 6, 7, z, "minecraft:cut_copper")
        ap.fill(4, 4, z, 6, 6, z, "minecraft:air")
    ap.chest(5, 4, 6, "north", "canopycavern:chests/thermal_observatory")
    ap.set(3, 4, 6, "minecraft:crafting_table")
    ap.set(7, 4, 6, "minecraft:sponge")
    ap.jigsaw(5, 4, 0, "north_up", "canopycavern:obs_pod", "canopycavern:obs_pod",
              "minecraft:empty", "minecraft:air", "aligned")
    pod_portals = {(x, y, 0) for x in (4, 5, 6) for y in (4, 5, 6)}
    ap.validate("abyssal_thermal_observatory/airlock_pod")
    ap.verify_watertight("abyssal_thermal_observatory/airlock_pod", [(5, 5, 5)], pod_portals)
    ap.save("abyssal_thermal_observatory/airlock_pod.nbt")

    # Geothermal Vent Drill Rig (11 x 16 x 11) - flush y=3 floor & sealed z=0..2 docking collar
    dr = V4StructureBuilder(11, 16, 11, fill_block="minecraft:structure_void")
    dr.fill(1, 0, 1, 9, 3, 9, "minecraft:basalt")
    dr.fill(4, 0, 4, 6, 2, 6, "minecraft:magma_block")
    dr.hollow_box(2, 3, 2, 8, 8, 8, "minecraft:polished_deepslate", fill_spec="minecraft:air")
    for p in range(3, 8):
        for y in range(5, 7):
            dr.set(2, y, p, "minecraft:tinted_glass")
            dr.set(8, y, p, "minecraft:tinted_glass")
            dr.set(p, y, 8, "minecraft:tinted_glass")
    # Encased vertical thermal drill laser & copper tower
    dr.fill(4, 8, 4, 6, 13, 6, "minecraft:copper_block")
    dr.fill(5, 2, 5, 5, 14, 5, "minecraft:sea_lantern")
    for y in range(4, 8):
        dr.set(4, y, 5, "minecraft:tinted_glass")
        dr.set(6, y, 5, "minecraft:tinted_glass")
        dr.set(5, y, 4, "minecraft:tinted_glass")
        dr.set(5, y, 6, "minecraft:tinted_glass")
    dr.set(5, 15, 5, "minecraft:lightning_rod")
    # Flush docking collar z=0..2 connecting tunnel to drill deck
    for z in range(0, 3):
        dr.fill(3, 2, z, 7, 3, z, "minecraft:polished_deepslate")
        dr.fill(3, 4, z, 3, 7, z, "minecraft:cut_copper")
        dr.fill(7, 4, z, 7, 7, z, "minecraft:cut_copper")
        dr.fill(4, 7, z, 6, 7, z, "minecraft:cut_copper")
        dr.fill(4, 4, z, 6, 6, z, "minecraft:air")
    dr.chest(7, 4, 7, "north", "canopycavern:chests/thermal_observatory")
    dr.add_drowned(1, 4, 5)
    dr.add_guardian(9, 6, 5, elder=False)
    dr.jigsaw(5, 4, 0, "north_up", "canopycavern:obs_pod", "canopycavern:obs_pod",
              "minecraft:empty", "minecraft:air", "aligned")
    dr.validate("abyssal_thermal_observatory/thermal_vent_drill")
    dr.verify_watertight("abyssal_thermal_observatory/thermal_vent_drill", [(4, 5, 4)], pod_portals)
    dr.save("abyssal_thermal_observatory/thermal_vent_drill.nbt")


REEF_FOUNDATION_DEPTH = 48


def add_reef_anchors(builder: V4StructureBuilder, piers: tuple[tuple[int, int], ...]):
    """Preserve sea-level features by extending only the columns below each piece."""
    builder.shift_vertical(REEF_FOUNDATION_DEPTH)
    for x, z in piers:
        for y in range(REEF_FOUNDATION_DEPTH):
            stone = "minecraft:tuff" if (x + y + z) % 3 == 0 else "minecraft:andesite"
            builder.set(x, y, z, stone)
            # Broaden the upper join under the original structure without filling the whole seabed.
            if y >= REEF_FOUNDATION_DEPTH - 8:
                for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    builder.set(x + dx, y, z + dz, stone)


def build_reef_lighthouse_keep():
    # The dock sits at local y=20 before adding supports and offsetting start_height.
    import math
    lh = V4StructureBuilder(27, 50, 27, fill_block="minecraft:air")
    # Below y=21: preserve intact ocean water via structure_void (omitted on save!)
    for x in range(27):
        for y in range(21):
            for z in range(27):
                lh.set(x, y, z, "minecraft:structure_void")

    # Organic Craggy Reef Sea-Stack Island Foundation & Stone Seawall Bastion (y=0..20)
    cx, cz = 13, 12
    for y in range(21):
        base_rad = max(6.8, 12.2 - y * 0.24)
        for x in range(27):
            for z in range(27):
                dx, dz = x - cx, z - cz
                dist = math.hypot(dx, dz)
                angle = math.atan2(dz, dx)
                crag = 1.3 * math.sin(3.0 * angle + y * 0.18) + 0.8 * math.cos(5.0 * angle - y * 0.25)
                eff_rad = base_rad + (crag if y < 18 else crag * 0.45)
                if dist <= eff_rad:
                    if y <= 4:
                        lh.set(x, y, z, "minecraft:gravel" if (x + z) % 3 == 0 else "minecraft:andesite")
                    elif y <= 14:
                        mod = (x * 5 + y * 3 + z * 7) % 6
                        blk = "minecraft:tuff" if mod < 2 else ("minecraft:cobblestone" if mod < 4 else "minecraft:andesite")
                        lh.set(x, y, z, blk)
                    elif y <= 19:
                        lh.set(x, y, z, "minecraft:mossy_stone_bricks" if (x + y + z) % 4 == 0 else "minecraft:stone_bricks")
                    else:
                        lh.set(x, y, z, "minecraft:mossy_stone_bricks" if (x + z) % 3 == 0 else "minecraft:stone_bricks")

    # Natural jagged sea-stack boulder outcrops on West & East surf edges (y=18..22)
    for bx, bz, bh in ((5, 11, 22), (5, 12, 21), (21, 14, 22), (21, 13, 21)):
        for by in range(15, bh + 1):
            lh.set(bx, by, bz, "minecraft:andesite" if by == bh else "minecraft:tuff")

    # Carve Dry Submerged Smugglers' Reef Vault on North Reef Floor (x=9..17, y=2..7, z=2..7)
    lh.hollow_box(9, 2, 2, 17, 7, 7, "minecraft:polished_deepslate", fill_spec="minecraft:air")
    lh.fill(11, 1, 0, 15, 2, 1, "minecraft:cobblestone")
    # Keep open seawater cove channel outside the North vault doorway so rock island never blocks entry!
    lh.fill(12, 3, 0, 14, 9, 1, "minecraft:structure_void")
    lh.set(11, 4, 1, "minecraft:sea_lantern")
    lh.set(15, 4, 1, "minecraft:sea_lantern")
    lh.door(13, 3, 2, "minecraft:warped_door", "north")
    lh.set(13, 5, 2, "minecraft:cyan_stained_glass")
    lh.set(13, 6, 4, "minecraft:sea_lantern")
    lh.chest(11, 3, 3, "south", "canopycavern:chests/armada_treasure")
    lh.chest(15, 3, 3, "south", "canopycavern:chests/armada_treasure")
    lh.set(13, 3, 3, "minecraft:gold_block")
    lh.add_drowned(4, 3, 5)
    lh.add_drowned(22, 3, 5)
    lh.verify_watertight("reef_lighthouse_keep/smuggler_vault", [(13, 4, 5)])

    # Waterline Island Courtyard Quay Deck (y=20) & Timber Harbor Pier Extending South (z=20..26)
    lh.fill(6, 20, 6, 20, 20, 20, "minecraft:stone_bricks")
    lh.fill(7, 20, 7, 19, 20, 19, "minecraft:cobblestone")
    for px in range(11, 16):
        for pz in range(20, 27):
            lh.set(px, 20, pz, "minecraft:spruce_planks")
            if px in (11, 15) and pz in (21, 25):
                # Extend pilings all the way down to y=0 seabed (no floating posts!)
                for py in range(0, 23):
                    lh.set(px, py, pz, "minecraft:oak_log")
                lh.lantern(px, 23, pz)
    lh.set(10, 21, 21, "minecraft:barrel")
    lh.set(16, 21, 21, "minecraft:barrel")

    # Keeper's Detailed Coastal Timber-Stone Lodge on West Half (x=7..14, y=20..27, z=8..17)
    lh.hollow_box(7, 20, 8, 14, 27, 17, "minecraft:calcite", fill_spec="minecraft:air")
    lh.fill(7, 20, 8, 14, 20, 17, "minecraft:spruce_planks")
    for x in range(7, 15):
        lh.set(x, 21, 8, "minecraft:stone_bricks")
        lh.set(x, 21, 17, "minecraft:stone_bricks")
        lh.set(x, 24, 8, "minecraft:dark_oak_log")
        lh.set(x, 24, 17, "minecraft:dark_oak_log")
    for z in range(8, 18):
        lh.set(7, 21, z, "minecraft:stone_bricks")
        lh.set(14, 21, z, "minecraft:stone_bricks")
        lh.set(7, 24, z, "minecraft:dark_oak_log")
        lh.set(14, 24, z, "minecraft:dark_oak_log")
    for px in (7, 14):
        for pz in (8, 17):
            for py in range(21, 28):
                lh.set(px, py, pz, "minecraft:dark_oak_log")
    # South harbor veranda entrance (door faces South cleanly onto quay) + framed multi-pane windows
    lh.door(10, 21, 17, "minecraft:spruce_door", "south")
    for wx in (8, 12, 13):
        lh.pane_x(wx, 22, 23, 17, "minecraft:light_blue_stained_glass_pane")
        lh.pane_x(wx, 22, 23, 8, "minecraft:light_blue_stained_glass_pane")
    lh.set(8, 25, 17, "minecraft:light_blue_stained_glass_pane")
    lh.set(12, 25, 17, "minecraft:light_blue_stained_glass_pane")
    # Side stone hearth chimney (x=6, z=11) + warm campfire smoke
    for cy in range(20, 31):
        lh.set(6, cy, 11, "minecraft:cobblestone" if cy > 25 else "minecraft:stone_bricks")
    lh.set(6, 31, 11, "minecraft:campfire")
    lh.pitched_gable_roof(7, 14, 28, 8, 17, "minecraft:spruce_stairs", "minecraft:dark_oak_planks", "minecraft:spruce_slab", "minecraft:calcite")
    # Cozy Lodge Interior & Veranda Lanterns
    lh.set(8, 21, 11, ("minecraft:smoker", {"facing": "east", "lit": "true"}))
    lh.chest(9, 21, 10, "south", "canopycavern:chests/armada_treasure")
    lh.set(12, 21, 10, "minecraft:cartography_table")
    lh.set(13, 21, 9, "minecraft:bookshelf")
    lh.set(13, 22, 9, "minecraft:potted_cornflower")
    lh.bed(8, 21, 13, "minecraft:red_bed", "south")
    lh.lantern(11, 26, 13, hanging=True)
    for px in (7, 14):
        lh.set(px, 21, 18, "minecraft:spruce_fence")
        lh.set(px, 21, 19, "minecraft:spruce_fence")
        lh.lantern(px, 22, 19, hanging=False)

    # Soaring Crisp Red-and-White Beacon Lighthouse Tower (x=16..20, y=20..49, z=10..14)
    for y in range(20, 41):
        if y <= 24:
            band = "minecraft:stone_bricks" if y % 2 == 0 else "minecraft:cobbled_deepslate"
        else:
            band = "minecraft:white_concrete" if ((y - 25) // 4) % 2 == 0 else "minecraft:red_concrete"
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                if abs(dx) == 2 and abs(dz) == 2:
                    continue
                x, z = 18 + dx, 12 + dz
                on_wall = (abs(dx) == 2 or abs(dz) == 2 or (abs(dx) == 1 and abs(dz) == 1 and abs(dx) + abs(dz) == 2))
                if on_wall:
                    lh.set(x, y, z, band)
                else:
                    lh.set(x, y, z, "minecraft:air")
        lh.set(18, y, 12, "minecraft:stripped_dark_oak_log")
        if y < 40:
            lh.set(17, y, 12, ("minecraft:ladder", {"facing": "west", "waterlogged": "false"}))
        if y % 6 == 0 and 25 <= y <= 38:
            lh.set(18, y, 14, "minecraft:glass_pane")
            lh.set(20, y, 12, "minecraft:glass_pane")
    # Walkable Arched Lighthouse Entrance facing West onto Courtyard (16, 21..22, 12)
    lh.door(16, 21, 12, "minecraft:spruce_door", "west")
    # Wide Walkable Observation Gallery Balcony (y=40) + Connected Iron Bars Railing (y=41)
    lh.fill(14, 40, 8, 22, 40, 16, "minecraft:polished_deepslate_slab")
    lh.set(17, 40, 12, "minecraft:air")  # Clear hatch to climb out!
    for x in range(14, 23):
        lh.set(x, 41, 8, "minecraft:iron_bars")
        lh.set(x, 41, 16, "minecraft:iron_bars")
    for z in range(8, 17):
        lh.set(14, 41, z, "minecraft:iron_bars")
        lh.set(22, 41, z, "minecraft:iron_bars")
    lh.hollow_box(16, 41, 10, 20, 45, 14, "minecraft:glass", fill_spec="minecraft:sea_lantern")
    # Conical Oxidized Copper Beacon Spire (y=46..49)
    lh.fill(16, 46, 10, 20, 46, 14, "minecraft:oxidized_cut_copper")
    lh.fill(17, 47, 11, 19, 47, 13, "minecraft:oxidized_copper")
    lh.set(18, 48, 12, "minecraft:oxidized_copper")
    lh.set(18, 49, 12, "minecraft:lightning_rod")

    # Open-Air Harbor Keep Sentinels + Maritime Villagers (y=21 courtyard & pier)
    lh.add_sentinel(13, 21, 22)
    lh.add_sentinel(16, 21, 17)
    lh.add_sentinel(8, 21, 19)
    lh.add_villager(13, 21, 19, "minecraft:plains", "minecraft:cartographer")
    lh.add_villager(14, 21, 24, "minecraft:plains", "minecraft:fisherman")

    # Jigsaw Wing -> Sunken Armada Galleon Wreck + Harbor Pier
    lh.jigsaw(13, 21, 26, "south_up", "canopycavern:harbor_bay", "canopycavern:harbor_bay",
              "canopycavern:reef_lighthouse_keep/wings", "minecraft:spruce_planks", "aligned")
    lh.validate("reef_lighthouse_keep", require_outdoor_sentinel=True)
    add_reef_anchors(lh, ((13, 12), (9, 12), (17, 12), (13, 8), (13, 16)))
    lh.save("reef_lighthouse_keep/island_keep_anchored.nbt")

    # Sunken Armada Flagship Wreck (17 x 24 x 25): joins dock at [8, 21, 0], tapered curved galleon at y=1..14!
    wr = V4StructureBuilder(17, 24, 25, fill_block="minecraft:structure_void")
    cx_w = 8
    # Mooring End-of-Pier Buoy Platform (z=0..3, y=20) + full-depth oak pilings down to seabed
    wr.fill(6, 20, 0, 10, 20, 3, "minecraft:spruce_planks")
    for px in (6, 10):
        for py in range(0, 22):
            wr.set(px, py, 3, "minecraft:oak_log")
        wr.lantern(px, 22, 3)
    wr.set(cx_w, 21, 2, "minecraft:sea_lantern")

    # Curved, Tapered Galleon Hull resting on Seabed (z=4..22)
    hull_profile = {
        4: 1, 5: 2, 6: 2, 7: 3, 8: 3,
        9: 4, 10: 4, 11: 4, 12: 4, 13: 4, 14: 4, 15: 4, 16: 4,
        17: 4, 18: 4, 19: 3, 20: 3, 21: 3, 22: 2,
    }
    for z, hw in hull_profile.items():
        # Keel spine & rounded bilge
        for dx in range(-hw, hw + 1):
            x = cx_w + dx
            if abs(dx) <= max(1, hw - 2):
                wr.set(x, 1, z, "minecraft:dark_oak_planks")
            if abs(dx) <= max(1, hw - 1):
                wr.set(x, 2, z, "minecraft:dark_oak_planks")
            if z in (4, 22) or abs(dx) == hw:
                top_hull = 8 if z <= 6 else (7 if z <= 16 else 10)
                for y in range(2 if abs(dx) < hw else 3, top_hull + 1):
                    plank = "minecraft:spruce_planks" if y >= 6 else "minecraft:dark_oak_planks"
                    if y in (4, 5) and (x + z) % 5 == 0:
                        plank = "minecraft:mossy_cobblestone"
                    wr.set(x, y, z, plank)
        # Forecastle deck (z=5..7, y=7) & Flooded mid-deck planks (z=8..16, y=3)
        if 5 <= z <= 7:
            for dx in range(-hw + 1, hw):
                wr.set(cx_w + dx, 7, z, "minecraft:spruce_planks")
        elif 8 <= z <= 16:
            for dx in range(-hw + 1, hw):
                wr.set(cx_w + dx, 2, z, "minecraft:dark_oak_planks")

    # Sculpted Angled Bowsprit Spar + Fence Forestay at Prow (z=1..4)
    for idx, bz in enumerate((4, 3, 2, 1)):
        wr.set(cx_w, 8 + idx // 2, bz, "minecraft:stripped_dark_oak_log")
        if bz in (3, 2):
            wr.set(cx_w, 9 + idx // 2, bz, "minecraft:spruce_fence")

    # Sealed Dry Captain's Treasure Stern Cabin (x=6..10, z=17..21, y=3..7; quarterdeck roof y=7)
    wr.hollow_box(5, 2, 17, 11, 7, 22, "minecraft:dark_oak_planks", fill_spec="minecraft:air")
    wr.fill(6, 7, 18, 10, 7, 21, "minecraft:spruce_planks")
    # Illuminated stained glass stern windows + sealed warped_door at z=17
    for wx in (6, 8, 10):
        wr.set(wx, 5, 22, "minecraft:light_blue_stained_glass")
    wr.door(cx_w, 3, 17, "minecraft:warped_door", "north")
    wr.chest(6, 3, 20, "north", "canopycavern:chests/armada_treasure")
    wr.chest(10, 3, 20, "north", "canopycavern:chests/armada_treasure")
    wr.chest(cx_w, 3, 21, "north", "canopycavern:chests/armada_treasure")
    wr.set(7, 3, 20, "minecraft:gold_block")
    wr.set(9, 3, 20, "minecraft:emerald_block")
    wr.set(7, 3, 19, "minecraft:cartography_table")
    wr.set(cx_w, 6, 19, "minecraft:sea_lantern")
    # Stern Quarterdeck Poop Rail (y=8..9)
    for z in range(17, 22):
        hw = hull_profile[z]
        wr.set(cx_w - hw, 8, z, "minecraft:spruce_fence")
        wr.set(cx_w + hw, 8, z, "minecraft:spruce_fence")

    # Broken Asymmetric Foremast (z=8, y=3..14) + Tattered Billowing Canvas Sail
    for y in range(3, 14):
        wr.set(cx_w, y, 8, "minecraft:stripped_dark_oak_log")
    for wx in range(cx_w - 3, cx_w + 4):
        wr.set(wx, 12, 8, "minecraft:spruce_fence")
        for wy in (9, 10, 11):
            if (wx == cx_w - 3 and wy == 9) or (wx == cx_w + 3 and wy == 11):
                continue  # Organic storm-torn edge
            sz = 7 if abs(wx - cx_w) <= 1 else 8
            wr.set(wx, wy, sz, "minecraft:light_gray_wool" if (wx + wy) % 4 == 0 else "minecraft:white_wool")

    # Tall Broken Mainmast (z=14, y=3..18) + Crow's Nest + Wide Billowing Tattered Sail
    for y in range(3, 18):
        wr.set(cx_w, y, 14, "minecraft:stripped_dark_oak_log")
    for x in range(cx_w - 1, cx_w + 2):
        for z in range(13, 16):
            if (x, z) != (cx_w, 14):
                wr.slab(x, 15, z, "minecraft:spruce_slab", "bottom")
                wr.set(x, 16, z, "minecraft:spruce_fence")
    for wx in range(cx_w - 4, cx_w + 5):
        wr.set(wx, 13, 14, "minecraft:spruce_fence")
        for wy in (9, 10, 11, 12):
            if abs(wx - cx_w) == 4 and wy in (9, 10):
                continue
            if (wx, wy) in ((cx_w + 2, 10), (cx_w - 3, 11)):
                continue  # Realistic cannon-torn sail gaps
            sz = 13 if abs(wx - cx_w) <= 2 else 14
            wr.set(wx, wy, sz, "minecraft:light_gray_wool" if wy == 9 else "minecraft:white_wool")

    wr.add_drowned(4, 4, 10)
    wr.add_drowned(12, 4, 10)
    wr.add_drowned(cx_w, 9, 11)
    wr.jigsaw(cx_w, 21, 0, "north_up", "canopycavern:harbor_bay", "canopycavern:harbor_bay",
              "minecraft:empty", "minecraft:spruce_planks", "aligned")
    wr.validate("reef_lighthouse_keep/sunken_flagship_wreck")
    wr.verify_watertight("reef_lighthouse_keep/sunken_flagship_wreck", [(cx_w, 4, 19)])
    add_reef_anchors(wr, ((6, 3), (10, 3), (8, 7), (8, 14), (8, 20)))
    for z in (7, 14, 20):
        wr.set(8, REEF_FOUNDATION_DEPTH, z, "minecraft:andesite")
    wr.save("reef_lighthouse_keep/sunken_flagship_wreck_anchored.nbt")


def generate_ocean_worldgen_and_loot():
    build_sunken_citadel_vault()
    build_abyssal_thermal_observatory()
    build_reef_lighthouse_keep()

    # Template pools
    pools = {
        "sunken_citadel_vault/start": [("canopycavern:sunken_citadel_vault/central_vault", 1, "rigid")],
        "sunken_citadel_vault/wings": [
            ("canopycavern:sunken_citadel_vault/colonnade_wing", 2, "rigid"),
            ("canopycavern:sunken_citadel_vault/sanctum_spire", 1, "rigid"),
        ],
        "abyssal_thermal_observatory/start": [("canopycavern:abyssal_thermal_observatory/main_dome", 1, "rigid")],
        "abyssal_thermal_observatory/tunnels": [("canopycavern:abyssal_thermal_observatory/copper_tunnel_bridge", 1, "rigid")],
        "abyssal_thermal_observatory/pods": [
            ("canopycavern:abyssal_thermal_observatory/airlock_pod", 1, "rigid"),
            ("canopycavern:abyssal_thermal_observatory/thermal_vent_drill", 1, "rigid"),
        ],
        "reef_lighthouse_keep/start": [("canopycavern:reef_lighthouse_keep/island_keep_anchored", 1, "rigid")],
        "reef_lighthouse_keep/wings": [("canopycavern:reef_lighthouse_keep/sunken_flagship_wreck_anchored", 1, "rigid")],
    }
    for name, entries in pools.items():
        write_ns_json(CANOPY_DATA, f"worldgen/template_pool/{name}.json", {
            "elements": [{
                "element": {
                    "element_type": "minecraft:single_pool_element",
                    "location": loc,
                    "processors": {"processors": []},
                    "projection": proj,
                },
                "weight": w,
            } for loc, w, proj in entries],
            "fallback": "minecraft:empty",
        })

    # Structures + Structure Sets + Biome Tags
    ocean_defs = [
        ("sunken_citadel_vault", "sunken_citadel_vaults", 24, 12, 941801, -2, "OCEAN_FLOOR_WG", "#minecraft:is_deep_ocean"),
        ("abyssal_thermal_observatory", "abyssal_thermal_observatories", 22, 11, 941802, -2, "OCEAN_FLOOR_WG", "#minecraft:is_deep_ocean"),
        ("reef_lighthouse_keep", "reef_lighthouse_keeps", 22, 11, 941803, -20 - REEF_FOUNDATION_DEPTH, "WORLD_SURFACE_WG", "#minecraft:is_ocean"),
    ]
    for s_id, set_id, spacing, sep, salt, start_y, heightmap, biome_tag in ocean_defs:
        write_ns_json(CANOPY_DATA, f"tags/worldgen/biome/has_structure/{s_id}.json", {"values": [biome_tag]})
        write_ns_json(CANOPY_DATA, f"worldgen/structure/{s_id}.json", {
            "type": "minecraft:jigsaw",
            "biomes": f"#canopycavern:has_structure/{s_id}",
            "max_distance_from_center": 80,
            "project_start_to_heightmap": heightmap,
            "liquid_settings": "ignore_waterlogging",
            "size": 3 if s_id == "abyssal_thermal_observatory" else 2,
            "spawn_overrides": {},
            "start_height": {"absolute": start_y},
            "start_pool": f"canopycavern:{s_id}/start",
            "step": "surface_structures",
            "use_expansion_hack": False,
        })
        write_ns_json(CANOPY_DATA, f"worldgen/structure_set/{set_id}.json", {
            "placement": {
                "type": "minecraft:random_spread",
                "salt": salt,
                "separation": sep,
                "spacing": spacing,
            },
            "structures": [{"structure": f"canopycavern:{s_id}", "weight": 1}],
        })

    # Structure tag for Abyssal Tide Compass
    write_ns_json(CANOPY_DATA, "tags/worldgen/structure/tide_compass_targets.json", {
        "values": [
            "canopycavern:sunken_citadel_vault",
            "canopycavern:abyssal_thermal_observatory",
            "canopycavern:reef_lighthouse_keep",
        ]
    })

    # Structure tag update for Grotto Relic Compass (includes new Underground Monument)
    write_ns_json(CANOPY_DATA, "tags/worldgen/structure/relic_compass_targets.json", {
        "replace": False,
        "values": [
            "canopycavern:cavern_shrine",
            "canopycavern:echoing_mineshaft_hub",
            "canopycavern:canopy_treetop_bastion",
            "canopycavern:abyssal_sanctum_monument",
        ]
    })

    # Loot tables (multi-pool Vanilla-Plus treasure pools)
    def pool_item(name, w, mn, mx):
        return {
            "type": "minecraft:item",
            "name": name,
            "weight": w,
            "functions": [{"function": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": mn, "max": mx}}],
        }

    loot_defs = {
        "chests/sunken_citadel": (
            [
                ("canopycavern:sea_glass_charm", 3, 1, 1),
                ("canopycavern:abyssal_tide_compass", 3, 1, 1),
                ("minecraft:heart_of_the_sea", 2, 1, 1),
                ("minecraft:trident", 1, 1, 1),
                ("minecraft:diamond", 4, 2, 5),
                ("minecraft:golden_apple", 3, 1, 2),
            ],
            [
                ("minecraft:nautilus_shell", 5, 1, 3),
                ("minecraft:prismarine_crystals", 8, 4, 12),
                ("minecraft:gold_ingot", 6, 4, 10),
                ("minecraft:emerald", 6, 3, 9),
                ("minecraft:cooked_salmon", 5, 3, 7),
            ],
        ),
        "chests/thermal_observatory": (
            [
                ("canopycavern:grotto_crystal_pickaxe", 3, 1, 1),
                ("canopycavern:glow_lantern", 3, 1, 1),
                ("minecraft:netherite_scrap", 2, 1, 2),
                ("minecraft:spyglass", 3, 1, 1),
            ],
            [
                ("minecraft:sponge", 4, 2, 5),
                ("minecraft:copper_ingot", 8, 6, 16),
                ("minecraft:amethyst_shard", 7, 4, 10),
                ("minecraft:prismarine_crystals", 7, 3, 9),
                ("minecraft:lapis_lazuli", 6, 4, 10),
                ("minecraft:cooked_salmon", 6, 3, 7),
            ],
        ),
        "chests/armada_treasure": (
            [
                ("canopycavern:abyssal_tide_compass", 3, 1, 1),
                ("canopycavern:sea_glass_charm", 3, 1, 1),
                ("minecraft:diamond", 3, 1, 3),
                ("minecraft:compass", 4, 1, 1),
            ],
            [
                ("minecraft:gold_ingot", 8, 5, 14),
                ("minecraft:emerald", 8, 4, 12),
                ("minecraft:iron_ingot", 7, 4, 10),
                ("minecraft:nautilus_shell", 5, 1, 3),
                ("minecraft:experience_bottle", 5, 3, 8),
                ("minecraft:cooked_cod", 7, 4, 9),
            ],
        ),
        "chests/abyssal_monument": (
            [
                ("canopycavern:grotto_relic_compass", 3, 1, 1),
                ("canopycavern:alpine_climbing_pick", 3, 1, 1),
                ("canopycavern:glow_lantern", 4, 1, 1),
                ("minecraft:enchanted_golden_apple", 1, 1, 1),
                ("minecraft:diamond", 5, 3, 7),
                ("minecraft:netherite_scrap", 2, 1, 2),
            ],
            [
                ("minecraft:amethyst_shard", 8, 6, 14),
                ("minecraft:emerald", 8, 4, 10),
                ("minecraft:gold_ingot", 8, 5, 12),
                ("minecraft:lapis_lazuli", 6, 6, 14),
                ("minecraft:experience_bottle", 6, 4, 9),
                ("minecraft:golden_carrot", 6, 4, 8),
            ],
        ),
    }
    for rel, (rare_entries, supply_entries) in loot_defs.items():
        write_ns_json(CANOPY_DATA, f"loot_table/{rel}.json", {
            "type": "minecraft:chest",
            "pools": [
                {
                    "rolls": {"type": "minecraft:uniform", "min": 1, "max": 2},
                    "entries": [pool_item(n, w, mn, mx) for n, w, mn, mx in rare_entries],
                },
                {
                    "rolls": {"type": "minecraft:uniform", "min": 3, "max": 5},
                    "entries": [pool_item(n, w, mn, mx) for n, w, mn, mx in supply_entries],
                },
            ],
            "random_sequence": f"canopycavern:{rel}",
        })


# ===========================================================================
# 2. LUXURY VANILLA VILLAGE REVAMP (Plains, Desert, Savanna, Snowy, Taiga)
# ===========================================================================
THEMES = {
    "plains": {
        "vtype": "minecraft:plains",
        "plinth": "minecraft:stone_bricks",
        "plinth_alt": "minecraft:mossy_stone_bricks",
        "floor": "minecraft:oak_planks",
        "path": "minecraft:cobblestone",
        "pillar": "minecraft:stripped_oak_log",
        "wall": "minecraft:white_terracotta",
        "trim": "minecraft:dark_oak_planks",
        "stair": "minecraft:dark_oak_stairs",
        "slab": "minecraft:dark_oak_slab",
        "door": "minecraft:oak_door",
        "pane": "minecraft:glass_pane",
        "stained": "minecraft:light_blue_stained_glass_pane",
        "fence": "minecraft:oak_fence",
        "awning_a": "minecraft:red_wool",
        "awning_b": "minecraft:white_wool",
        "bed": "minecraft:red_bed",
        "flower": "minecraft:potted_flowering_azalea_bush",
        "chimney": "minecraft:bricks",
    },
    "desert": {
        "vtype": "minecraft:desert",
        "plinth": "minecraft:cut_sandstone",
        "plinth_alt": "minecraft:chiseled_sandstone",
        "floor": "minecraft:smooth_sandstone",
        "path": "minecraft:smooth_sandstone",
        "pillar": "minecraft:cut_sandstone",
        "wall": "minecraft:sandstone",
        "trim": "minecraft:oxidized_copper",
        "stair": "minecraft:sandstone_stairs",
        "slab": "minecraft:smooth_sandstone_slab",
        "door": "minecraft:acacia_door",
        "pane": "minecraft:orange_stained_glass_pane",
        "stained": "minecraft:cyan_stained_glass_pane",
        "fence": "minecraft:acacia_fence",
        "awning_a": "minecraft:cyan_wool",
        "awning_b": "minecraft:yellow_wool",
        "bed": "minecraft:cyan_bed",
        "flower": "minecraft:potted_cactus",
        "chimney": "minecraft:terracotta",
    },
    "savanna": {
        "vtype": "minecraft:savanna",
        "plinth": "minecraft:bricks",
        "plinth_alt": "minecraft:polished_granite",
        "floor": "minecraft:acacia_planks",
        "path": "minecraft:packed_mud",
        "pillar": "minecraft:stripped_acacia_log",
        "wall": "minecraft:terracotta",
        "trim": "minecraft:orange_terracotta",
        "stair": "minecraft:acacia_stairs",
        "slab": "minecraft:acacia_slab",
        "door": "minecraft:acacia_door",
        "pane": "minecraft:yellow_stained_glass_pane",
        "stained": "minecraft:orange_stained_glass_pane",
        "fence": "minecraft:acacia_fence",
        "awning_a": "minecraft:orange_wool",
        "awning_b": "minecraft:yellow_wool",
        "bed": "minecraft:orange_bed",
        "flower": "minecraft:potted_acacia_sapling",
        "chimney": "minecraft:bricks",
    },
    "snowy": {
        "vtype": "minecraft:snowy",
        "plinth": "minecraft:stone_bricks",
        "plinth_alt": "minecraft:polished_andesite",
        "floor": "minecraft:spruce_planks",
        "path": "minecraft:cobblestone",
        "pillar": "minecraft:stripped_spruce_log",
        "wall": "minecraft:snow_block",
        "trim": "minecraft:spruce_planks",
        "stair": "minecraft:spruce_stairs",
        "slab": "minecraft:spruce_slab",
        "door": "minecraft:spruce_door",
        "pane": "minecraft:light_blue_stained_glass_pane",
        "stained": "minecraft:blue_stained_glass_pane",
        "fence": "minecraft:spruce_fence",
        "awning_a": "minecraft:blue_wool",
        "awning_b": "minecraft:white_wool",
        "bed": "minecraft:light_blue_bed",
        "flower": "minecraft:potted_spruce_sapling",
        "chimney": "minecraft:cobblestone",
    },
    "taiga": {
        "vtype": "minecraft:taiga",
        "plinth": "minecraft:cobbled_deepslate",
        "plinth_alt": "minecraft:mossy_cobblestone",
        "floor": "minecraft:spruce_planks",
        "path": "minecraft:gravel",
        "pillar": "minecraft:stripped_dark_oak_log",
        "wall": "minecraft:spruce_planks",
        "trim": "minecraft:dark_oak_planks",
        "stair": "minecraft:dark_oak_stairs",
        "slab": "minecraft:spruce_slab",
        "door": "minecraft:spruce_door",
        "pane": "minecraft:glass_pane",
        "stained": "minecraft:green_stained_glass_pane",
        "fence": "minecraft:spruce_fence",
        "awning_a": "minecraft:green_wool",
        "awning_b": "minecraft:brown_wool",
        "bed": "minecraft:green_bed",
        "flower": "minecraft:potted_fern",
        "chimney": "minecraft:deepslate_bricks",
    },
}


def draw_grand_town_center(theme: str, p: dict) -> V4StructureBuilder:
    """
    17x17x17 Grand Civic Town Center Piazza & Clock-Bell Pavilion.
    Zero trapped sentinels: 4 Sentinels + 2 Iron Golems + 4 Villagers patrol OPEN flagstone plaza!
    Cardinal street connectors sit at y=1 matching vanilla streets seamlessly.
    """
    sb = V4StructureBuilder(17, 17, 17, fill_block="minecraft:air")
    # y=0: Ornate Geometric Piazza Paving
    for x in range(17):
        for z in range(17):
            is_border = x in (0, 16) or z in (0, 16)
            is_road = (x in (7, 8, 9) or z in (7, 8, 9))
            if is_road:
                sb.set(x, 0, z, p["path"])
            elif is_border or (x + z) % 2 == 0:
                sb.set(x, 0, z, p["plinth"])
            else:
                sb.set(x, 0, z, p["plinth_alt"])

    # Central Open Arched Bell-Tower Pavilion (x=6..10, y=1..16, z=6..10) - completely pass-through arches!
    for cx, cz in [(6, 6), (10, 6), (6, 10), (10, 10)]:
        for y in range(1, 10):
            sb.set(cx, y, cz, p["pillar"] if y > 2 else p["plinth"])
        lz = cz - 1 if cz == 6 else cz + 1
        sb.set(cx, 4, lz, p["fence"])
        sb.lantern(cx, 3, lz, hanging=True)
    sb.arch_opening(7, 9, 1, 4, 6, p["stair"])
    sb.arch_opening(7, 9, 1, 4, 10, p["stair"])
    sb.arch_opening_z(6, 1, 4, 7, 9, p["stair"])
    sb.arch_opening_z(10, 1, 4, 7, 9, p["stair"])

    # Solid Architrave Deck (y=5) supporting both Upper Belfry & Ceiling Bell at (8, 4, 8)
    sb.fill(6, 5, 6, 10, 5, 10, p["trim"])
    sb.set(8, 1, 8, p["plinth_alt"])
    sb.set(8, 4, 8, ("minecraft:bell", {"attachment": "ceiling", "facing": "north", "powered": "false"}))
    # Upper Timber/Copper Belfry Story (y=6..10) + Looming Pyramid Spire (y=11..16)
    sb.hollow_box(6, 6, 6, 10, 10, 10, p["wall"], fill_spec="minecraft:air")
    for cx, cz in [(6, 6), (10, 6), (6, 10), (10, 10)]:
        for y in range(6, 11):
            sb.set(cx, y, cz, p["pillar"])
    for y in (7, 8):
        sb.set(8, y, 6, p["stained"])
        sb.set(8, y, 10, p["stained"])
        sb.set(6, y, 8, p["stained"])
        sb.set(10, y, 8, p["stained"])
    sb.hipped_pyramid_roof(5, 11, 10, 5, 11, p["trim"], p["stair"], p["slab"])
    sb.chest(7, 1, 7, "east", "canopycavern:chests/village_supply")

    # 2 Covered Open Market Stalls flanking Plaza Corners (NW x=2..4, z=2..4 and NE x=12..14, z=2..4)
    for mx, side in [(2, 1), (12, -1)]:
        sb.set(mx, 1, 2, p["fence"]); sb.set(mx + 2, 1, 2, p["fence"])
        sb.set(mx, 2, 2, p["fence"]); sb.set(mx + 2, 2, 2, p["fence"])
        sb.set(mx, 1, 4, p["fence"]); sb.set(mx + 2, 1, 4, p["fence"])
        sb.set(mx, 2, 4, p["fence"]); sb.set(mx + 2, 2, 4, p["fence"])
        for x in range(mx, mx + 3):
            for z in range(2, 5):
                sb.set(x, 3, z, p["awning_a"] if (x + z) % 2 == 0 else p["awning_b"])
        sb.set(mx + 1, 1, 3, "minecraft:barrel")
        sb.lantern(mx + 1, 4, 3)

    # Ornate Corner Lantern Gardens (SW & SE)
    for gx, gz in [(2, 13), (14, 13)]:
        sb.set(gx, 1, gz, p["plinth_alt"])
        sb.set(gx, 2, gz, p["flower"])
        sb.set(gx + 1 if gx == 2 else gx - 1, 1, gz, p["fence"])
        sb.lantern(gx + 1 if gx == 2 else gx - 1, 2, gz)

    # 4 Street Connectors (y=1 on outermost rims matching vanilla street level)
    sb.jigsaw(0, 1, 8, "west_up", "minecraft:street", "minecraft:street", f"minecraft:village/{theme}/streets", "minecraft:structure_void", "aligned")
    sb.jigsaw(16, 1, 8, "east_up", "minecraft:street", "minecraft:street", f"minecraft:village/{theme}/streets", "minecraft:structure_void", "aligned")
    sb.jigsaw(8, 1, 0, "north_up", "minecraft:street", "minecraft:street", f"minecraft:village/{theme}/streets", "minecraft:structure_void", "aligned")
    sb.jigsaw(8, 1, 16, "south_up", "minecraft:street", "minecraft:street", f"minecraft:village/{theme}/streets", "minecraft:structure_void", "aligned")

    # 9 Outdoor Sentinels (+5 reinforcement on base plaza) + 2 Iron Golems + 5 Villagers (Zero blocked doors!)
    sb.add_sentinel(4, 1, 8)
    sb.add_sentinel(12, 1, 8)
    sb.add_sentinel(8, 1, 4)
    sb.add_sentinel(8, 1, 12)
    sb.add_sentinel(1, 1, 8)
    sb.add_sentinel(15, 1, 8)
    sb.add_sentinel(8, 1, 1)
    sb.add_sentinel(8, 1, 15)
    sb.add_sentinel(4, 1, 13)
    sb.add_golem(3, 1, 11)
    sb.add_golem(13, 1, 11)
    sb.add_villager(3, 1, 5, p["vtype"], "minecraft:farmer")
    sb.add_villager(13, 1, 5, p["vtype"], "minecraft:librarian")
    sb.add_villager(5, 1, 13, p["vtype"], "minecraft:armorer")
    sb.add_villager(11, 1, 13, p["vtype"], "minecraft:cleric")
    sb.add_villager(7, 1, 2, p["vtype"], "minecraft:cartographer")

    sb.validate(f"{theme}/grand_town_center", require_outdoor_sentinel=True)
    return sb


def draw_revamp_house(theme: str, p: dict, role: str) -> V4StructureBuilder:
    """
    13x15x13 Luxury Two-Story / Courtyard Civic Building for vanilla houses pools.
    Uses y=0 foundation + [6, 1, 0] north_up `building_entrance` matching vanilla streets.
    Every role stations multiple Sentinels OUTSIDE on open verandas / courtyards + multiple Villagers.
    """
    sb = V4StructureBuilder(13, 16, 13, fill_block="minecraft:air")
    # y=0: Stepped Courtyard Terrace & Warm Interior Floor
    sb.fill(0, 0, 0, 12, 0, 12, p["path"])
    sb.fill(2, 0, 3, 10, 0, 11, p["plinth"])
    if role not in ("bastion_gatehouse", "market_pavilion"):
        sb.fill(3, 0, 5, 9, 0, 10, p["floor"])

    # Open Front Veranda / Courtyard Colonade (z=1..3, open walk-through with awning/lanterns!)
    for cx in (2, 10):
        for y in range(1, 5):
            sb.set(cx, y, 2, p["pillar"])
        sb.set(cx, 4, 1, p["fence"])
        sb.lantern(cx, 3, 1, hanging=True)
    for x in range(2, 11):
        sb.set(x, 4, 2, p["trim"])
    sb.set(3, 1, 1, p["plinth_alt"]); sb.set(3, 2, 1, p["flower"])
    sb.set(9, 1, 1, p["plinth_alt"]); sb.set(9, 2, 1, p["flower"])

    if role == "bastion_gatehouse":
        # Open-Arch Bastion Watch-Court: spacious walk-in twin barracks wings (x=0..4 & 8..12, z=4..11)
        # + central 3x5 vaulted breezeway + accessible 2nd-story gallery & rooftop lookout!
        sb.hollow_box(0, 0, 4, 4, 11, 11, p["plinth"], fill_spec="minecraft:air")
        sb.hollow_box(8, 0, 4, 12, 11, 11, p["plinth"], fill_spec="minecraft:air")
        sb.fill(0, 0, 4, 4, 0, 11, p["plinth"])
        sb.fill(8, 0, 4, 12, 0, 11, p["plinth"])
        sb.fill(1, 0, 5, 3, 0, 10, p["floor"])
        sb.fill(9, 0, 5, 11, 0, 10, p["floor"])
        for x in (0, 4, 8, 12):
            for z in (4, 11):
                for y in range(1, 12):
                    sb.set(x, y, z, p["plinth_alt"])
        # Continuous 2nd-Story Armory / Watch Bridge (y=6) + Open Roof Battlement Deck (y=11)
        sb.fill(0, 6, 4, 12, 6, 11, p["plinth"])
        sb.fill(1, 6, 5, 3, 6, 10, p["floor"])
        sb.fill(9, 6, 5, 11, 6, 10, p["floor"])
        # Open Central Breezeway Arch (x=5..7, y=1..5) + Upper Bridge Gallery Arch (y=7..10)
        sb.arch_opening(5, 7, 1, 5, 4, p["stair"])
        sb.arch_opening(5, 7, 1, 5, 11, p["stair"])
        sb.arch_opening(5, 7, 7, 10, 4, p["stair"])
        sb.arch_opening(5, 7, 7, 10, 11, p["stair"])
        for z in range(5, 11):
            sb.fill(5, 1, z, 7, 5, z, "minecraft:air")
            sb.fill(5, 7, z, 7, 10, z, "minecraft:air")
        # Carve wide walk-in arches into BOTH Twin Bastion Barracks on BOTH Floors (never sealed!)
        sb.arch_opening_z(4, 1, 3, 6, 8, p["stair"])
        sb.arch_opening_z(8, 1, 3, 6, 8, p["stair"])
        sb.arch_opening_z(4, 7, 9, 6, 8, p["stair"])
        sb.arch_opening_z(8, 7, 9, 6, 8, p["stair"])
        for fx in (2, 10):
            sb.set(fx, 1, 4, "minecraft:air"); sb.set(fx, 2, 4, "minecraft:air")
            sb.set(fx, 8, 4, p["pane"]); sb.set(fx, 8, 11, p["pane"])
            sb.set(fx, 2, 11, p["pane"]); sb.set(fx, 3, 11, p["pane"])
        for oz in (6, 9):
            for oy in (2, 3, 8, 9):
                sb.set(0, oy, oz, "minecraft:iron_bars")
                sb.set(12, oy, oz, "minecraft:iron_bars")
        # Ladder shafts up from ground -> 2nd floor -> rooftop battlement (keep hatches open!)
        for ly in range(1, 12):
            sb.set(1, ly, 5, ("minecraft:ladder", {"facing": "east", "waterlogged": "false"}))
            sb.set(11, ly, 5, ("minecraft:ladder", {"facing": "west", "waterlogged": "false"}))
        # Furnished Ground Barracks, Upper Skybridge Armory, Bell, & Lanterns
        sb.set(6, 5, 7, ("minecraft:bell", {"attachment": "ceiling", "facing": "north", "powered": "false"}))
        sb.lantern(2, 5, 7, hanging=True); sb.lantern(10, 5, 7, hanging=True)
        sb.lantern(2, 10, 7, hanging=True); sb.lantern(10, 10, 7, hanging=True)
        for bx in range(5, 8):
            sb.set(bx, 11, 7, p["trim"])
        sb.lantern(6, 10, 7, hanging=True)
        sb.chest(11, 1, 9, "west", "canopycavern:chests/village_supply")
        sb.set(1, 1, 9, "minecraft:grindstone")
        sb.set(1, 1, 10, "minecraft:fletching_table")
        sb.bed(2, 7, 9, p["bed"], "south")
        sb.chest(10, 7, 9, "north", "canopycavern:chests/village_supply")
        sb.set(6, 7, 7, "minecraft:smithing_table")
        # Roof lookout decks: the ladder shafts end beside open landings.
        for left, right in ((0, 4), (8, 12)):
            for x in range(left, right + 1):
                for z in range(4, 12):
                    if x in (left, right) or z in (4, 11):
                        sb.set(x, 12, z, p["fence"])
        # Ground-only Sentinels outdoors & under wide open bastion archway!
        sb.add_sentinel(4, 1, 2)
        sb.add_sentinel(8, 1, 2)
        sb.add_sentinel(5, 1, 7)
        sb.add_sentinel(7, 1, 7)
        sb.add_golem(6, 1, 2)
        sb.add_villager(3, 1, 1, p["vtype"], "minecraft:fletcher")
        sb.add_villager(9, 1, 1, p["vtype"], "minecraft:armorer")

    elif role == "market_pavilion":
        # Open-Air Vaulted Grand Market Arcade on Ground + Staircase + Cozy Timber Upper Inn Loft!
        for cx in (2, 6, 10):
            for cz in (4, 10):
                for y in range(1, 6):
                    sb.set(cx, y, cz, p["pillar"])
        for y in range(1, 5):
            for x in range(3, 10):
                if x not in (6,):
                    sb.set(x, y, 4, "minecraft:air")
                    sb.set(x, y, 10, "minecraft:air")
        # Colorful Market Stalls Inside Open Arcade (smoker & barrel face East cleanly into open aisle!)
        for x in range(3, 10):
            sb.set(x, 4, 3, p["awning_a"] if x % 2 == 0 else p["awning_b"])
        sb.set(3, 1, 6, ("minecraft:barrel", {"facing": "east", "open": "false"}))
        sb.set(3, 1, 8, ("minecraft:smoker", {"facing": "east", "lit": "true"}))
        sb.set(9, 1, 6, "minecraft:composter")
        sb.chest(9, 1, 8, "west", "canopycavern:chests/village_supply")
        # Second-Story Cantilevered Timber Inn Hall (y=5..12) + Access Ladder Shaft at (4, 1..5, 9)
        sb.hollow_box(2, 5, 4, 10, 8, 10, p["wall"], fill_spec="minecraft:air")
        sb.fill(2, 5, 4, 10, 5, 10, p["floor"])
        for ly in range(1, 6):
            sb.set(7, ly, 10, p["pillar"])
            sb.set(7, ly, 9, ("minecraft:ladder", {"facing": "north", "waterlogged": "false"}))
        for x in (4, 8):
            sb.set(x, 7, 4, p["stained"]); sb.set(x, 7, 10, p["stained"])
        sb.bed(3, 6, 6, p["bed"], "north")
        sb.bed(9, 6, 6, p["bed"], "north")
        # Protect the ladder opening on both sides while leaving a step-out to the north.
        for rail_x in (6, 8):
            sb.set(rail_x, 6, 9, p["fence"])
        sb.chest(5, 6, 9, "north", "canopycavern:chests/village_supply")
        sb.lantern(6, 7, 7, hanging=True)
        sb.pitched_gable_roof(2, 10, 9, 4, 10, p["stair"], p["trim"], p["slab"], p["wall"])
        sb.add_sentinel(4, 1, 1)
        sb.add_sentinel(8, 1, 1)
        sb.add_sentinel(6, 1, 7)
        sb.add_villager(4, 1, 6, p["vtype"], "minecraft:farmer")
        sb.add_villager(8, 1, 6, p["vtype"], "minecraft:butcher")
        sb.add_villager(6, 1, 11, p["vtype"], "minecraft:cartographer")

    else:
        # Grand Two-Story Manor / Vaulted Guild Smithy / Sanctuary Cathedral-Library (ground interior y=1!)
        top_y = 9 if role != "sanctuary_library" else 10
        sb.hollow_box(2, 0, 4, 10, top_y, 11, p["wall"], fill_spec="minecraft:air")
        sb.fill(2, 0, 4, 10, 0, 11, p["plinth"])
        sb.fill(3, 0, 5, 9, 0, 10, p["floor"])
        # Ground Foundation Belt & Exterior Corner Buttresses (never flat!)
        for x in range(2, 11):
            sb.set(x, 1, 4, p["plinth"]); sb.set(x, 1, 11, p["plinth"])
        for z in range(4, 12):
            sb.set(2, 1, z, p["plinth"]); sb.set(10, 1, z, p["plinth"])
        for px in (2, 6, 10):
            for pz in (4, 11):
                if px == 6 and pz == 4:
                    continue
                for y in range(1, top_y + 1):
                    sb.set(px, y, pz, p["pillar"])
        # Upper Mezzanine Loft (y=5) & Ground Entrance Door (y=1..2)
        sb.fill(3, 5, 5, 9, 5, 10, p["floor"])
        sb.door(6, 1, 4, p["door"], "north")
        # Tall Recessed Windows & Side Chimney
        for wx in (4, 8):
            for wy in (2, 3, 6, 7):
                sb.set(wx, wy, 4, p["stained"] if role == "sanctuary_library" else p["pane"])
                sb.set(wx, wy, 11, p["stained"] if role == "sanctuary_library" else p["pane"])
        for wz in (6, 9):
            for wy in (2, 3, 6, 7):
                sb.set(2, wy, wz, p["pane"])
                sb.set(10, wy, wz, p["pane"])
        # Sweeping Stepped Gable Roof
        sb.pitched_gable_roof(2, 10, top_y + 1, 4, 11, p["stair"], p["trim"], p["slab"], p["wall"])
        sb.lantern(6, 4, 7, hanging=True)

        # Ground-floor inlaid parquet frame at y=0 (zero entity obstruction) + Exterior window flower sills at y=5
        for px in range(4, 9):
            for pz in range(6, 10):
                if px in (4, 8) or pz in (6, 9):
                    sb.set(px, 0, pz, p["trim"])
        for wx in (4, 8):
            sb.slab(wx, 5, 12, p["slab"], "top")
            sb.set(wx, 6, 12, p["flower"])
        for wz in (6, 9):
            sb.slab(1, 5, wz, p["slab"], "top")
            sb.set(1, 6, wz, p["flower"])

        def build_interior_stairwell():
            # Solid under-stair support stringer + barrel alcove (no floating steps!), facing south to climb z=6->10
            sb.set(8, 1, 7, p["trim"])
            sb.set(8, 1, 8, ("minecraft:barrel", {"facing": "west", "open": "false"}))
            sb.set(8, 2, 8, p["trim"])
            sb.fill(8, 1, 9, 8, 3, 9, p["trim"])
            sb.stairs(8, 1, 6, p["stair"], "south")
            sb.stairs(8, 2, 7, p["stair"], "south")
            sb.stairs(8, 3, 8, p["stair"], "south")
            sb.stairs(8, 4, 9, p["stair"], "south")
            # Clear full 3-block headroom through y=5 ceiling while keeping (8,5,10) upper landing floor!
            for sz in (7, 8, 9):
                sb.set(8, 5, sz, "minecraft:air")
                sb.set(7, 6, sz, p["fence"])
            for fx in (7, 8, 9):
                sb.set(fx, 6, 6, p["fence"])

        if role == "grand_manor":
            # Tall Brick Chimney + Warm Ground Parlor + Walkable Staircase & Richly Furnished Upper Loft
            for cy in range(1, 15):
                sb.set(11, cy, 8, p["chimney"])
            sb.set(11, 15, 8, "minecraft:campfire")
            sb.set(3, 1, 6, ("minecraft:barrel", {"facing": "east", "open": "false"}))
            sb.set(3, 2, 6, p["flower"])
            sb.set(4, 1, 10, "minecraft:crafting_table")
            sb.set(5, 1, 10, ("minecraft:smoker", {"facing": "north", "lit": "true"}))
            sb.set(6, 1, 10, ("minecraft:barrel", {"facing": "north", "open": "false"}))
            sb.set(9, 1, 10, "minecraft:bookshelf")
            sb.set(9, 2, 10, "minecraft:bookshelf")
            build_interior_stairwell()
            # 2nd floor cozy sleeping quarters & study table (clear of windows and (7..9, 6, 10) stair landing!)
            sb.bed(4, 6, 8, p["bed"], "south")
            sb.bed(6, 6, 8, p["bed"], "south")
            sb.set(3, 6, 10, ("minecraft:barrel", {"facing": "north", "open": "false"}))
            sb.set(3, 7, 10, p["flower"])
            sb.chest(5, 6, 10, "north", "canopycavern:chests/village_supply")
            sb.set(5, 6, 5, "minecraft:bookshelf")
            sb.set(6, 6, 5, "minecraft:crafting_table")
            sb.lantern(6, 7, 5, hanging=False)
            sb.set(7, 6, 5, ("minecraft:barrel", {"facing": "south", "open": "false"}))
            sb.lantern(6, 8, 7, hanging=True)
            sb.add_sentinel(4, 1, 1)
            sb.add_sentinel(8, 1, 1)
            sb.add_villager(5, 1, 2, p["vtype"], "minecraft:farmer")
            sb.add_villager(5, 1, 7, p["vtype"], "minecraft:cartographer")
            sb.add_villager(8, 1, 2, p["vtype"], "minecraft:cleric")

        elif role == "guild_smithy":
            # Open Outdoor Forge Yard (anvil/grindstone) + Ground Interior Blast Furnaces + Walkable Loft Stairs
            for cy in range(1, 14):
                sb.set(11, cy, 7, p["chimney"])
            sb.set(11, 14, 7, "minecraft:campfire")
            sb.set(4, 1, 2, "minecraft:anvil")
            sb.set(8, 1, 2, "minecraft:grindstone")
            sb.set(4, 1, 10, ("minecraft:blast_furnace", {"facing": "north", "lit": "true"}))
            sb.set(5, 1, 10, ("minecraft:blast_furnace", {"facing": "north", "lit": "true"}))
            sb.set(7, 1, 10, "minecraft:smithing_table")
            sb.chest(3, 1, 10, "north", "canopycavern:chests/village_supply")
            sb.set(9, 1, 6, ("minecraft:barrel", {"facing": "south", "open": "false"}))
            build_interior_stairwell()
            sb.bed(4, 6, 8, p["bed"], "south")
            sb.set(3, 6, 10, ("minecraft:barrel", {"facing": "north", "open": "false"}))
            sb.lantern(3, 7, 10, hanging=False)
            sb.chest(5, 6, 10, "north", "canopycavern:chests/village_supply")
            sb.set(4, 6, 5, "minecraft:smithing_table")
            sb.set(6, 6, 5, "minecraft:bookshelf")
            sb.lantern(6, 8, 7, hanging=True)
            sb.add_sentinel(3, 1, 1)
            sb.add_sentinel(9, 1, 1)
            sb.add_sentinel(1, 1, 6)
            sb.add_villager(5, 1, 2, p["vtype"], "minecraft:weaponsmith")
            sb.add_villager(6, 1, 7, p["vtype"], "minecraft:armorer")

        elif role == "sanctuary_library":
            # Soaring Bell-Lantern Cupola Spire on Roof Ridge (y=13..15) + Walkable Two-Story Library!
            sb.fill(5, 13, 7, 7, 14, 8, p["trim"])
            sb.set(6, 15, 7, "minecraft:sea_lantern")
            for bx in (5, 7, 9):
                sb.set(bx, 1, 10, "minecraft:bookshelf")
                sb.set(bx, 2, 10, "minecraft:bookshelf")
            sb.set(6, 1, 10, "minecraft:enchanting_table")
            sb.set(4, 1, 7, ("minecraft:lectern", {"facing": "east", "has_book": "false"}))
            sb.chest(3, 1, 9, "east", "canopycavern:chests/village_supply")
            build_interior_stairwell()
            for bx in (5, 6):
                sb.set(bx, 6, 10, "minecraft:bookshelf")
                sb.set(bx, 7, 10, "minecraft:bookshelf")
            sb.chest(3, 6, 10, "north", "canopycavern:chests/village_supply")
            sb.bed(4, 6, 6, p["bed"], "north")
            sb.set(5, 6, 5, "minecraft:crafting_table")
            sb.lantern(5, 7, 5, hanging=False)
            sb.lantern(6, 9, 7, hanging=True)
            sb.add_sentinel(4, 1, 1)
            sb.add_sentinel(8, 1, 1)
            sb.add_villager(6, 1, 2, p["vtype"], "minecraft:librarian")
            sb.add_villager(6, 1, 7, p["vtype"], "minecraft:cleric")
            sb.add_villager(5, 1, 8, p["vtype"], "minecraft:librarian")

    # Entrance connector at [6, 1, 0] facing north_up -> aligns cleanly with vanilla street `building_entrance` at y=1!
    sb.jigsaw(6, 1, 0, "north_up", "minecraft:building_entrance", "minecraft:building_entrance",
              "minecraft:empty", "minecraft:structure_void", "aligned")
    sb.validate(f"{theme}/{role}", require_outdoor_sentinel=True)
    return sb


def generate_vanilla_village_revamp():
    with zipfile.ZipFile(VANILLA_JAR) as z:
        for theme, pal in THEMES.items():
            # 1. Build 6 opulent architectural NBT files per theme (30 total)
            tc = draw_grand_town_center(theme, pal)
            tc.save(f"vanilla_revamp/{theme}/grand_town_center.nbt")

            roles = [
                ("grand_manor", 8),
                ("guild_smithy", 6),
                ("sanctuary_library", 6),
                ("market_pavilion", 7),
                ("bastion_gatehouse", 7),
            ]
            for role, _ in roles:
                hb = draw_revamp_house(theme, pal, role)
                hb.save(f"vanilla_revamp/{theme}/{role}.nbt")

            # 2. Override vanilla town_centers.json preserving rare zombie villages (weight must be in [1..150])!
            orig_tc = json.loads(z.read(f"data/minecraft/worldgen/template_pool/village/{theme}/town_centers.json"))
            zombie_tc = [e for e in orig_tc["elements"] if "zombie" in e["element"].get("location", "")]
            raw_sum = sum(e["weight"] for e in orig_tc["elements"] if "zombie" not in e["element"].get("location", ""))
            normal_tc_weight = min(145, max(50, raw_sum))
            new_tc_elems = [{
                "element": {
                    "element_type": "minecraft:single_pool_element",
                    "location": f"canopycavern:vanilla_revamp/{theme}/grand_town_center",
                    "processors": {"processors": []},
                    "projection": "rigid",
                },
                "weight": normal_tc_weight,
            }] + zombie_tc
            write_ns_json(MINECRAFT_DATA, f"worldgen/template_pool/village/{theme}/town_centers.json", {
                "elements": new_tc_elems,
                "fallback": orig_tc.get("fallback", "minecraft:empty"),
            })

            # 3. Override vanilla houses.json with grand 2-story civic halls + vanilla empty tail!
            orig_h = json.loads(z.read(f"data/minecraft/worldgen/template_pool/village/{theme}/houses.json"))
            empty_h = [e for e in orig_h["elements"] if e["element"].get("element_type") == "minecraft:empty_pool_element"]
            new_h_elems = [{
                "element": {
                    "element_type": "minecraft:single_pool_element",
                    "location": f"canopycavern:vanilla_revamp/{theme}/{role}",
                    "processors": {"processors": []},
                    "projection": "rigid",
                },
                "weight": weight,
            } for role, weight in roles] + empty_h
            write_ns_json(MINECRAFT_DATA, f"worldgen/template_pool/village/{theme}/houses.json", {
                "elements": new_h_elems,
                "fallback": orig_h.get("fallback", f"minecraft:village/{theme}/terminators"),
            })


def build_abyssal_sanctum_monument():
    """
    Monumental 3-tier Subterranean Cathedral Monument (`canopycavern:abyssal_sanctum_monument`):
    - grand_rotunda.nbt (31x27x31): Vaulted subterranean deepslate-brick & prismarine rotunda
      with colonnade buttresses, sunken reflective water aqueducts, grand twin stairways to
      an elevated amethyst & gold altar dais, suspended crystalline chandelier, mezzanine galleries,
      Elder/regular Guardians, Breeze construct guards, and treasure chests.
    - side_atrium_hall.nbt (15x17x19): Vaulted colonnade nave with thermal lava fountain grates.
    - relic_treasury_vault.nbt (17x15x17): Gilded subterranean treasury chamber with 4 relic chests.
    """
    rot = V4StructureBuilder(31, 27, 31, fill_block="minecraft:air")
    # Solid carved stone encasement shell + open vaulted interior (29x25x29 interior carved air!)
    rot.hollow_box(0, 0, 0, 30, 26, 30, "minecraft:deepslate_bricks", fill_spec="minecraft:air")
    rot.fill(0, 0, 0, 30, 1, 30, "minecraft:polished_tuff")
    rot.fill(2, 1, 2, 28, 1, 28, "minecraft:tuff_bricks")
    # Grand vaulted ceiling coffered rings & towering glowing crystalline oculus cupola (y=24..26)
    for y in range(21, 26):
        inset = y - 20
        rot.hollow_box(inset, y, inset, 30 - inset, 26, 30 - inset, "minecraft:deepslate_bricks", fill_spec="minecraft:air")
    for x in range(11, 20):
        for z in range(11, 20):
            dist = max(abs(x - 15), abs(z - 15))
            if dist == 4:
                rot.set(x, 26, z, "minecraft:gilded_blackstone")
            elif dist == 3:
                rot.set(x, 26, z, "minecraft:sea_lantern")
            elif dist <= 2:
                rot.set(x, 26, z, "minecraft:tinted_glass")
    rot.set(15, 26, 15, "minecraft:gold_block")

    # Sunken cross-axis aqueduct basins (y=1..1 water over y=0 prismarine/sea_lantern inlaid floor)
    for x in range(3, 28):
        for z in range(3, 28):
            in_ring = (6 <= abs(x - 15) <= 8 and abs(z - 15) <= 9) or (6 <= abs(z - 15) <= 8 and abs(x - 15) <= 9)
            if in_ring:
                rot.set(x, 0, z, "minecraft:dark_prismarine")
                rot.set(x, 1, z, "minecraft:water")
                if (x + z) % 6 == 0:
                    rot.set(x, 0, z, "minecraft:sea_lantern")
    # Four ceremonial cardinal bridges (x=13..17 and z=13..17, y=1..1 polished floor)
    rot.fill(13, 1, 1, 17, 1, 29, "minecraft:polished_tuff")
    rot.fill(1, 1, 13, 29, 1, 17, "minecraft:polished_tuff")
    for i in range(4, 27, 4):
        rot.set(15, 1, i, "minecraft:sea_lantern")
        rot.set(i, 1, 15, "minecraft:sea_lantern")

    # Central Stepped Sanctuary Altar Dais (x=11..19, z=11..19, y=2..4 + crowning shrinespire)
    rot.fill(10, 2, 10, 20, 2, 20, "minecraft:deepslate_bricks")
    rot.fill(11, 3, 11, 19, 3, 19, "minecraft:polished_tuff")
    rot.fill(12, 4, 12, 18, 4, 18, "minecraft:gilded_blackstone")
    rot.fill(13, 5, 13, 17, 5, 17, "minecraft:prismarine_bricks")
    # Ceremonial staircases climbing East/West & North/South up to y=5 Sanctum Platform
    for s, dy in [(9, 2), (10, 3), (11, 4), (12, 5)]:
        for w in range(14, 17):
            rot.stairs(s, dy, w, "minecraft:deepslate_tile_stairs", "east")
            rot.stairs(30 - s, dy, w, "minecraft:deepslate_tile_stairs", "west")
            rot.stairs(w, dy, s, "minecraft:deepslate_tile_stairs", "south")
            rot.stairs(w, dy, 30 - s, "minecraft:deepslate_tile_stairs", "north")
    # Glowing Amethyst & Gold Altar Core at (15, 6..10, 15) + 4 Corner Shrine Obelisks
    rot.set(15, 6, 15, "minecraft:gold_block")
    rot.set(15, 7, 15, "minecraft:amethyst_block")
    rot.set(15, 8, 15, "minecraft:sea_lantern")
    rot.set(15, 9, 15, "minecraft:copper_bulb")
    for ox, oz in [(13, 13), (17, 13), (13, 17), (17, 17)]:
        rot.fill(ox, 6, oz, ox, 9, oz, "minecraft:prismarine_bricks")
        rot.set(ox, 10, oz, "minecraft:sea_lantern")
    rot.chest(13, 6, 15, "east", "canopycavern:chests/abyssal_monument")
    rot.chest(17, 6, 15, "west", "canopycavern:chests/abyssal_monument")

    # Suspended Colossal Cathedral Chandelier Hanging Above Altar (y=17..25)
    for cy in range(18, 26):
        rot.set(15, cy, 15, "minecraft:iron_chain")
    rot.fill(13, 17, 15, 17, 17, 15, "minecraft:gold_block")
    rot.fill(15, 17, 13, 15, 17, 17, "minecraft:gold_block")
    rot.set(15, 16, 15, "minecraft:sea_lantern")
    for dx, dz in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, -1), (-1, 1), (1, 1)]:
        rot.set(15 + dx, 16, 15 + dz, "minecraft:amethyst_block")
        rot.lantern(15 + dx, 15, 15 + dz, hanging=True)

    # 12 Monumental Fluted Colonnade Pillars (y=2..21) + Upper Cloister Walkways (y=11)
    rot.hollow_box(1, 11, 1, 29, 11, 29, "minecraft:deepslate_bricks", fill_spec="minecraft:air")
    for px in (4, 11, 19, 26):
        for pz in (4, 11, 19, 26):
            if (px in (11, 19) and pz in (11, 19)):
                continue
            for py in range(2, 22):
                blk = "minecraft:gilded_blackstone" if py in (2, 11, 21) else (
                    "minecraft:amethyst_block" if py in (7, 16) else "minecraft:polished_tuff"
                )
                rot.set(px, py, pz, blk)
            lz = pz + (1 if pz < 15 else -1)
            rot.set(px, 7, lz, "minecraft:deepslate_brick_wall")
            rot.lantern(px, 6, lz, hanging=True)
    # Corner Spiral-Step Stairs connecting Main Floor y=2 -> Mezzanine Balcony y=11 (x=2..4, z=2..9)
    for step_idx in range(10):
        rot.stairs(2, 2 + step_idx, 3 + step_idx, "minecraft:deepslate_tile_stairs", "south")
        rot.set(2, 11, 3 + step_idx, "minecraft:air")
        rot.set(2, 12, 3 + step_idx, "minecraft:air")
    # Carved Open Mezzanine Gallery Walkways at y=11 (3-wide perimeter balcony overlooking center!)
    for gx in range(2, 29):
        for gz in range(2, 29):
            if 5 <= gx <= 25 and 5 <= gz <= 25:
                rot.set(gx, 11, gz, "minecraft:air")
            elif gx in (2, 3, 27, 28) or gz in (2, 3, 27, 28):
                rot.set(gx, 11, gz, "minecraft:polished_tuff")
    for bx in range(4, 27):
        for bz in (4, 26):
            rot.set(bx, 12, bz, "minecraft:deepslate_brick_wall")
            rot.set(bz, 12, bx, "minecraft:deepslate_brick_wall")

    # 4 Cardinal Vaulted Entrance Portals & Jigsaw Wing Connectors
    for jx, jz, ori, open_axis in [
        (15, 0, "north_up", "x"),
        (15, 30, "south_up", "x"),
        (0, 15, "west_up", "z"),
        (30, 15, "east_up", "z"),
    ]:
        if open_axis == "x":
            rot.arch_opening(13, 17, 2, 7, jz, "minecraft:deepslate_tile_stairs")
        else:
            rot.arch_opening_z(jx, 2, 7, 13, 17, "minecraft:deepslate_tile_stairs")
        rot.jigsaw(jx, 2, jz, ori, "canopycavern:monument_wing", "canopycavern:monument_wing",
                   "canopycavern:abyssal_sanctum_monument/atrium_wings", "minecraft:air", "aligned")

    # Monument Defenders: Elder Guardian + 2 Guardians in Aqueducts + 3 Breeze Constructs on Upper Galleries & Altar
    rot.add_guardian(8, 1, 8, elder=True)
    rot.add_guardian(22, 1, 22, elder=False)
    rot.add_guardian(8, 1, 22, elder=False)
    rot.add_entity(15.5, 6.0, 13.5, "minecraft:breeze")
    rot.add_entity(2.5, 12.0, 15.5, "minecraft:breeze")
    rot.add_entity(28.5, 12.0, 15.5, "minecraft:breeze")
    rot.validate("abyssal_sanctum_monument/grand_rotunda")
    rot.save("abyssal_sanctum_monument/grand_rotunda.nbt")

    # Wing 1: Vaulted Atrium Processional Nave (15x17x19)
    nave = V4StructureBuilder(15, 17, 19, fill_block="minecraft:air")
    nave.hollow_box(0, 0, 0, 14, 16, 18, "minecraft:deepslate_bricks", fill_spec="minecraft:air")
    nave.fill(0, 0, 0, 14, 1, 18, "minecraft:tuff_bricks")
    nave.fill(5, 1, 0, 9, 1, 18, "minecraft:polished_tuff")
    for z in range(1, 18):
        if z % 4 == 2:
            for lx in (3, 11):
                for ly in range(2, 12):
                    nave.set(lx, ly, z, "minecraft:gilded_blackstone" if ly in (2, 11) else "minecraft:polished_tuff")
            nave.set(7, 15, z, "minecraft:iron_chain")
            nave.set(7, 14, z, "minecraft:iron_chain")
            nave.lantern(7, 13, z, hanging=True)
        # Side Lava/Magma Thermal Alcoves behind Iron Bars
        for sx in (1, 13):
            nave.set(sx, 1, z, "minecraft:magma_block")
            nave.set(sx + (1 if sx == 1 else -1), 2, z, "minecraft:iron_bars")
            nave.set(sx + (1 if sx == 1 else -1), 3, z, "minecraft:iron_bars")
    for rx in range(2, 13):
        nave.set(rx, 15, 9, "minecraft:sea_lantern")
    nave.arch_opening(5, 9, 2, 7, 0, "minecraft:deepslate_tile_stairs")
    nave.arch_opening(5, 9, 2, 7, 18, "minecraft:deepslate_tile_stairs")
    nave.jigsaw(7, 2, 0, "north_up", "canopycavern:monument_wing", "canopycavern:monument_wing",
                "minecraft:empty", "minecraft:air", "aligned")
    nave.jigsaw(7, 2, 18, "south_up", "canopycavern:monument_vault", "canopycavern:monument_vault",
                "canopycavern:abyssal_sanctum_monument/vaults", "minecraft:air", "aligned")
    nave.add_entity(7.5, 2.0, 9.5, "minecraft:breeze")
    nave.validate("abyssal_sanctum_monument/side_atrium_hall")
    nave.save("abyssal_sanctum_monument/side_atrium_hall.nbt")

    # Wing 2: Gilded Treasury Vault Chamber (17x15x17)
    vault = V4StructureBuilder(17, 15, 17, fill_block="minecraft:air")
    vault.hollow_box(0, 0, 0, 16, 14, 16, "minecraft:deepslate_bricks", fill_spec="minecraft:air")
    vault.fill(0, 0, 0, 16, 1, 16, "minecraft:polished_tuff")
    # Central Gilded Vault Dais (x=5..11, z=5..11, y=2..3)
    vault.fill(5, 2, 5, 11, 2, 11, "minecraft:gilded_blackstone")
    vault.fill(6, 3, 6, 10, 3, 10, "minecraft:gold_block")
    vault.fill(7, 4, 7, 9, 4, 9, "minecraft:emerald_block")
    vault.set(8, 5, 8, "minecraft:diamond_block")
    vault.set(8, 6, 8, "minecraft:amethyst_block")
    vault.set(8, 7, 8, "minecraft:sea_lantern")
    for cx, cz in [(3, 3), (13, 3), (3, 13), (13, 13)]:
        vault.fill(cx, 2, cz, cx, 13, cz, "minecraft:prismarine_bricks")
        vault.set(cx, 8, cz, "minecraft:sea_lantern")
    # 4 Unobstructed Relic Vault Chests + Ancient Lectern + Bell
    vault.chest(6, 4, 8, "west", "canopycavern:chests/abyssal_monument")
    vault.chest(10, 4, 8, "east", "canopycavern:chests/abyssal_monument")
    vault.chest(8, 4, 6, "north", "canopycavern:chests/abyssal_monument")
    vault.chest(8, 4, 10, "south", "canopycavern:chests/abyssal_monument")
    vault.set(4, 2, 8, ("minecraft:lectern", {"facing": "west", "has_book": "false"}))
    vault.set(8, 13, 8, ("minecraft:bell", {"attachment": "ceiling", "facing": "north", "powered": "false"}))
    vault.arch_opening(6, 10, 2, 7, 0, "minecraft:deepslate_tile_stairs")
    vault.jigsaw(8, 2, 0, "north_up", "canopycavern:monument_vault", "canopycavern:monument_vault",
                 "minecraft:empty", "minecraft:air", "aligned")
    vault.add_entity(4.5, 2.0, 4.5, "minecraft:breeze")
    vault.add_entity(12.5, 2.0, 12.5, "minecraft:breeze")
    vault.validate("abyssal_sanctum_monument/relic_treasury_vault")
    vault.save("abyssal_sanctum_monument/relic_treasury_vault.nbt")

    # Worldgen JSON Registration (Underground Structures, Overworld Caves & Custom Grottoes/Caverns)
    write_ns_json(CANOPY_DATA, "worldgen/template_pool/abyssal_sanctum_monument/start.json", {
        "elements": [{
            "element": {
                "element_type": "minecraft:single_pool_element",
                "location": "canopycavern:abyssal_sanctum_monument/grand_rotunda",
                "processors": {"processors": []},
                "projection": "rigid",
            },
            "weight": 1,
        }],
        "fallback": "minecraft:empty",
    })
    write_ns_json(CANOPY_DATA, "worldgen/template_pool/abyssal_sanctum_monument/atrium_wings.json", {
        "elements": [{
            "element": {
                "element_type": "minecraft:single_pool_element",
                "location": "canopycavern:abyssal_sanctum_monument/side_atrium_hall",
                "processors": {"processors": []},
                "projection": "rigid",
            },
            "weight": 1,
        }],
        "fallback": "minecraft:empty",
    })
    write_ns_json(CANOPY_DATA, "worldgen/template_pool/abyssal_sanctum_monument/vaults.json", {
        "elements": [{
            "element": {
                "element_type": "minecraft:single_pool_element",
                "location": "canopycavern:abyssal_sanctum_monument/relic_treasury_vault",
                "processors": {"processors": []},
                "projection": "rigid",
            },
            "weight": 1,
        }],
        "fallback": "minecraft:empty",
    })
    write_ns_json(CANOPY_DATA, "tags/worldgen/biome/has_structure/abyssal_sanctum_monument.json", {
        "replace": False,
        "values": [
            "canopycavern:amber_caverns",
            "canopycavern:verdant_grotto",
            "canopycavern:crystal_steppe",
            "minecraft:dripstone_caves",
            "minecraft:lush_caves",
            "minecraft:plains",
            "#minecraft:is_mountain",
            "#minecraft:is_forest",
            "#minecraft:is_taiga",
            "#minecraft:is_savanna",
        ],
    })
    write_ns_json(CANOPY_DATA, "worldgen/structure/abyssal_sanctum_monument.json", {
        "type": "minecraft:jigsaw",
        "biomes": "#canopycavern:has_structure/abyssal_sanctum_monument",
        "max_distance_from_center": 96,
        "size": 3,
        "spawn_overrides": {},
        "start_height": {"absolute": -32},
        "liquid_settings": "ignore_waterlogging",
        "start_pool": "canopycavern:abyssal_sanctum_monument/start",
        "step": "underground_structures",
        "use_expansion_hack": False,
    })
    write_ns_json(CANOPY_DATA, "worldgen/structure_set/abyssal_sanctum_monument.json", {
        "placement": {
            "type": "minecraft:random_spread",
            "salt": 4049917,
            "separation": 16,
            "spacing": 40,
        },
        "structures": [{"structure": "canopycavern:abyssal_sanctum_monument", "weight": 1}],
    })


if __name__ == "__main__":
    generate_ocean_worldgen_and_loot()
    build_abyssal_sanctum_monument()
    generate_vanilla_village_revamp()
    print("Generated all v0.4.0 Ocean Mega-Structures, Grand Underground Monument, Loot Tables, and Luxury Vanilla Village Revamps.")
