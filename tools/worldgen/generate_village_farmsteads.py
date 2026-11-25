"""Grand Farmsteads for the five revamped vanilla village themes.

The v0.4 revamp replaced every vanilla house pool entry with civic halls, which also removed
vanilla's farm plots, so villages had no crops and farmers had no composters. Each theme now
gets a 23x25 farmstead: four irrigated crop fields, a barn with composters and hay, a
scarecrow, a livestock pen and two farmers. It joins the vanilla street network through the
same north-facing building_entrance jigsaw as the other revamp halls.

Usage: python3 tools/worldgen/generate_village_farmsteads.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import generate_v04_ocean_and_villages as v4  # noqa: E402

SX, SY, SZ = 23, 9, 25
FIELD_W, FIELD_D = 10, 7
POOL_WEIGHT = 7

# Crops per field (NW, NE, SW, SE) and theme accents. Snowy fields sit under a glass roof.
CROPS = {
    "plains":  ("wheat", "carrots", "potatoes", "beetroots"),
    "desert":  ("wheat", "potatoes", "beetroots", "sugar_cane"),
    "savanna": ("wheat", "melon", "pumpkin", "carrots"),
    "snowy":   ("wheat", "potatoes", "beetroots", "carrots"),
    "taiga":   ("wheat", "pumpkin", "potatoes", "sweet_berry_bush"),
}
MAX_AGE = {"wheat": 7, "carrots": 7, "potatoes": 7, "beetroots": 3}
FIELDS = ((1, 6), (12, 6), (1, 14), (12, 14))  # field origins (x, z); each 10 wide x 7 deep


def _crop_cell(sb, x, z, crop, rng_val):
    """Ground at y=0, plant at y=1."""
    if crop in MAX_AGE:
        sb.set(x, 0, z, ("minecraft:farmland", {"moisture": "7"}))
        age = MAX_AGE[crop] - (rng_val % 3 if MAX_AGE[crop] > 3 else rng_val % 2)
        sb.set(x, 1, z, (f"minecraft:{crop}", {"age": str(age)}))
    elif crop in ("melon", "pumpkin"):
        if rng_val % 2 == 0:
            sb.set(x, 0, z, ("minecraft:farmland", {"moisture": "7"}))
            sb.set(x, 1, z, (f"minecraft:{crop}_stem", {"age": "7"}))
        else:
            sb.set(x, 0, z, "minecraft:dirt")
            sb.set(x, 1, z, f"minecraft:{crop}" if rng_val % 4 == 1 else "minecraft:air")
    elif crop == "sugar_cane":
        sb.set(x, 0, z, "minecraft:sand")
        for dy in range(1, 1 + 1 + rng_val % 3):
            sb.set(x, dy, z, ("minecraft:sugar_cane", {"age": "0"}))
    elif crop == "sweet_berry_bush":
        sb.set(x, 0, z, "minecraft:grass_block")
        sb.set(x, 1, z, ("minecraft:sweet_berry_bush", {"age": str(2 + rng_val % 2)}))


def draw_grand_farmstead(theme: str, p: dict) -> v4.V4StructureBuilder:
    sb = v4.V4StructureBuilder(SX, SY, SZ)
    soil = "minecraft:sand" if theme == "desert" else "minecraft:grass_block"
    path = p["path"]
    # Foundation and lawn
    sb.fill(0, 0, 0, SX - 1, 0, SZ - 1, soil)
    # Entrance lane from the street (north edge) down the middle
    sb.fill(10, 0, 0, 12, 0, SZ - 1, path)
    sb.fill(0, 0, 4, SX - 1, 0, 4, path)

    crops = CROPS[theme]
    for (fx, fz), crop in zip(FIELDS, crops):
        # Log frame around the field at y=0, water channel through the middle row (z+2)
        for x in range(fx, fx + FIELD_W):
            for z in range(fz, fz + FIELD_D):
                edge = x in (fx, fx + FIELD_W - 1) or z in (fz, fz + FIELD_D - 1)
                if edge:
                    sb.set(x, 0, z, (p["pillar"], {"axis": "y"}) if p["pillar"].endswith("_log") else p["pillar"])
                elif z == fz + FIELD_D // 2 and crop != "sweet_berry_bush":
                    sb.set(x, 0, z, "minecraft:water")
                    if x % 3 == 0:
                        sb.set(x, 1, z, ("minecraft:lily_pad", {}) if theme != "snowy" else "minecraft:air")
                else:
                    _crop_cell(sb, x, z, crop, (x * 7 + z * 13) % 11)
        # Low fence along the outer side of each field; gaps face the lane
        for x in range(fx, fx + FIELD_W):
            if not (9 <= x <= 13):
                sb.set(x, 1, fz + FIELD_D - 1 if fz == FIELDS[2][1] else fz, p["fence"])

    # Barn along the north side (x 1..8 and 14..21, z 0..3), split by the lane
    for bx0, bx1 in ((1, 8), (14, 21)):
        sb.fill(bx0, 0, 0, bx1, 0, 3, p["floor"])
        for x in (bx0, bx1):
            for z in (0, 3):
                sb.fill(x, 1, z, x, 4, z, (p["pillar"], {"axis": "y"}) if p["pillar"].endswith("_log") else p["pillar"])
        sb.fill(bx0, 5, 0, bx1, 5, 3, p["slab"] if "slab" in p["slab"] else p["trim"])
        sb.fill(bx0 + 1, 1, 0, bx1 - 1, 1, 0, p["fence"])
        # Interior: hay stacks, composters (farmer workstations), barrel, lanterns
        sb.fill(bx0 + 1, 1, 2, bx0 + 2, 2, 2, ("minecraft:hay_block", {"axis": "y"}))
        sb.set(bx1 - 1, 1, 2, ("minecraft:composter", {"level": "0"}))
        sb.set(bx1 - 2, 1, 2, ("minecraft:barrel", {"facing": "up", "open": "false"}),
               {"id": "minecraft:barrel", "LootTable": "minecraft:chests/village/village_plains_house"})
        sb.lantern(bx0 + 3, 4, 1, hanging=True)
        sb.set(bx0 + 3, 5, 1, p["trim"])
        sb.lantern(bx1 - 3, 4, 1, hanging=True)
        sb.set(bx1 - 3, 5, 1, p["trim"])

    # Scarecrow standing in the north-west field, facing the lane
    sb.set(5, 0, 7, soil)
    sb.set(5, 1, 7, p["fence"])
    sb.set(5, 2, 7, ("minecraft:hay_block", {"axis": "y"}))
    sb.set(5, 3, 7, ("minecraft:carved_pumpkin", {"facing": "east"}))

    # Livestock pen at the south end of the lane with a water trough
    sb.fill(8, 1, 22, 14, 1, 22, p["fence"])
    sb.fill(8, 1, 23, 8, 1, 24, p["fence"])
    sb.fill(14, 1, 23, 14, 1, 24, p["fence"])
    sb.fill(9, 1, 24, 13, 1, 24, p["fence"])
    sb.set(11, 0, 23, "minecraft:water")
    sb.add_entity(9.5, 1.0, 23.5, "minecraft:cow")
    sb.add_entity(13.5, 1.0, 23.5, "minecraft:sheep" if theme != "desert" else "minecraft:chicken")

    if theme == "snowy":
        # Greenhouse roof over the fields keeps snow off the crops (plain glass, no tint)
        for (fx, fz) in FIELDS:
            sb.fill(fx, 4, fz, fx + FIELD_W - 1, 4, fz + FIELD_D - 1, "minecraft:glass")
            for x in (fx, fx + FIELD_W - 1):
                for z in (fz, fz + FIELD_D - 1):
                    sb.fill(x, 1, z, x, 3, z, p["fence"])

    # Two farmers working the lane
    sb.add_villager(11, 1, 7, p["vtype"], "minecraft:farmer")
    sb.add_villager(11, 1, 17, p["vtype"], "minecraft:farmer")

    sb.jigsaw(11, 1, 0, "north_up", "minecraft:building_entrance", "minecraft:building_entrance",
              "minecraft:empty", "minecraft:structure_void", "aligned")
    sb.validate(f"{theme}/grand_farmstead", require_outdoor_sentinel=False, min_sentinels=0)
    return sb


def add_to_house_pool(theme: str):
    path = v4.MINECRAFT_DATA / f"worldgen/template_pool/village/{theme}/houses.json"
    pool = json.loads(path.read_text())
    loc = f"canopycavern:vanilla_revamp/{theme}/grand_farmstead"
    if not any(e["element"].get("location") == loc for e in pool["elements"]):
        empties = [e for e in pool["elements"] if e["element"].get("element_type") == "minecraft:empty_pool_element"]
        others = [e for e in pool["elements"] if e not in empties]
        others.append({"element": {"element_type": "minecraft:single_pool_element", "location": loc,
                                   "processors": {"processors": []}, "projection": "rigid"}, "weight": POOL_WEIGHT})
        pool["elements"] = others + empties
        path.write_text(json.dumps(pool, indent=2) + "\n")


def main():
    for theme, pal in v4.THEMES.items():
        sb = draw_grand_farmstead(theme, pal)
        sb.save(f"vanilla_revamp/{theme}/grand_farmstead.nbt")
        add_to_house_pool(theme)
        print(f"{theme}: grand_farmstead.nbt")


if __name__ == "__main__":
    main()
