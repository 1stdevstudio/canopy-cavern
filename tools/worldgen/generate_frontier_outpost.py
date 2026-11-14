"""Generate modular terrain-conforming frontier pillager outpost templates and worldgen data."""

from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from generate_v04_ocean_and_villages import V4StructureBuilder, v3

OUTPOST_ID = "frontier_pillager_outpost"
LOOT = f"canopycavern:chests/{OUTPOST_ID}"
AIR = "minecraft:air"
VOID = "minecraft:structure_void"
UNLIT_CAMPFIRE = ("minecraft:campfire", {
    "facing": "north", "lit": "false", "signal_fire": "false", "waterlogged": "false",
})


def stamp_uuids(builder: V4StructureBuilder, seed_key: str):
    for index, entity in enumerate(builder.entities):
        value = uuid5(NAMESPACE_URL, f"canopycavern:{seed_key}/{index}").bytes
        entity["nbt"]["UUID"] = v3.nbt_int_array(
            [int.from_bytes(value[i:i + 4], "big", signed=True) for i in range(0, 16, 4)]
        )


def add_pillager(builder: V4StructureBuilder, x: int, y: int, z: int):
    builder.clear_headroom(x, y, z, 2)
    builder.add_entity(x + 0.5, float(y), z + 0.5, "minecraft:pillager", {"PersistenceRequired": 1})


def build_watchtower_keep() -> V4StructureBuilder:
    """Compact 15x25x15 watchtower hub with 14-block ladder, gabled timber roof, and 4 wing sockets."""
    sb = V4StructureBuilder(15, 25, 15, fill_block=VOID)
    sb.fill(1, 0, 1, 13, 0, 13, "minecraft:cobblestone")
    sb.fill(1, 1, 1, 13, 6, 13, AIR)

    # 3-wide road necks reaching the four cardinal jigsaw sockets without a wide skirt
    for x0, x1, z0, z1 in ((6, 8, 0, 1), (6, 8, 13, 14), (0, 1, 6, 8), (13, 14, 6, 8)):
        sb.fill(x0, 0, z0, x1, 0, z1, "minecraft:cobblestone")
        sb.fill(x0, 1, z0, x1, 3, z1, AIR)

    # Floor 1 (y=7) and cantilevered Floor 2 (y=14) cleared before structural framing
    sb.fill(2, 7, 2, 12, 7, 12, "minecraft:dark_oak_planks")
    sb.fill(2, 8, 2, 12, 13, 12, AIR)
    sb.fill(1, 14, 1, 13, 14, 13, "minecraft:dark_oak_planks")
    sb.fill(1, 15, 1, 13, 21, 13, AIR)

    for deck_y, d0, d1 in ((7, 2, 12), (14, 1, 13)):
        fence_y = deck_y + 1
        for i in range(d0, d1 + 1):
            for fx, fz in ((i, d0), (i, d1), (d0, i), (d1, i)):
                if (fx, fz) not in ((2, 2), (12, 2), (2, 12), (12, 12)):
                    sb.set(fx, fence_y, fz, "minecraft:dark_oak_fence")
        sb.set(8, deck_y, 8, AIR)
        if fence_y == 8:
            sb.set(8, 8, 8, AIR)

    # Full-height corner piers rising continuously past Floor 1 & Floor 2 up to the y=17 gable slope
    for px, pz in ((2, 2), (12, 2), (2, 12), (12, 12)):
        sb.fill(px, 1, pz, px, 2, pz, "minecraft:cobblestone")
        sb.fill(px, 3, pz, px, 16, pz, "minecraft:dark_oak_log")

    # Outer eave posts on Floor 2 supporting the cantilevered roof corners at y=16
    for px, pz in ((1, 1), (13, 1), (1, 13), (13, 13)):
        sb.fill(px, 14, pz, px, 15, pz, "minecraft:dark_oak_log")

    # Mid-span struts on ground walls, leaving cardinal 3-wide archways open
    for px, pz in ((5, 2), (9, 2), (5, 12), (9, 12), (2, 5), (2, 9), (12, 5), (12, 9)):
        sb.fill(px, 1, pz, px, 7, pz, "minecraft:dark_oak_log")

    # Full 14-block climbable ladder beside solid log spine
    sb.fill(9, 1, 8, 9, 14, 8, "minecraft:dark_oak_log")
    for y in range(1, 15):
        sb.set(8, y, 8, ("minecraft:ladder", {"facing": "west", "waterlogged": "false"}))

    # Gabled dark-oak roof starting at y=16 (peak y=22, slab cap y=23)
    sb.pitched_gable_roof(
        1, 13, 16, 1, 13,
        "minecraft:dark_oak_stairs", "minecraft:dark_oak_planks",
        "minecraft:dark_oak_slab", "minecraft:dark_oak_planks",
    )

    sb.chest(5, 15, 5, "south", LOOT)
    for lx, ly, lz in ((3, 6, 3), (11, 6, 11), (3, 13, 3), (11, 13, 11)):
        sb.lantern(lx, ly, lz, hanging=True)
    sb.lantern(1, 1, 1)
    sb.lantern(13, 1, 13)

    add_pillager(sb, 5, 1, 5)
    add_pillager(sb, 5, 8, 5)
    add_pillager(sb, 10, 15, 10)

    sb.jigsaw(7, 1, 0, "north_up", "canopycavern:outpost_north", "canopycavern:outpost_north",
              f"canopycavern:{OUTPOST_ID}/wing_cage", AIR, "aligned")
    sb.jigsaw(14, 1, 7, "east_up", "canopycavern:outpost_east", "canopycavern:outpost_east",
              f"canopycavern:{OUTPOST_ID}/wing_tent_east", AIR, "aligned")
    sb.jigsaw(7, 1, 14, "south_up", "canopycavern:outpost_south", "canopycavern:outpost_south",
              f"canopycavern:{OUTPOST_ID}/wing_gate", AIR, "aligned")
    sb.jigsaw(0, 1, 7, "west_up", "canopycavern:outpost_west", "canopycavern:outpost_west",
              f"canopycavern:{OUTPOST_ID}/wing_tent_west", AIR, "aligned")

    stamp_uuids(sb, f"{OUTPOST_ID}/watchtower_keep")
    sb.validate(f"{OUTPOST_ID}/watchtower_keep")
    return sb


def build_trail(wing: str, start_key: str, target_pool: str) -> V4StructureBuilder:
    """Short 5x5x6 terrain-matching gravel trail linking the watchtower to an outpost module."""
    sb = V4StructureBuilder(5, 5, 6, fill_block=VOID)
    sb.fill(1, 0, 0, 3, 0, 5, "minecraft:coarse_dirt")
    sb.fill(2, 0, 0, 2, 0, 5, "minecraft:cobblestone")
    sb.fill(1, 1, 0, 3, 3, 5, AIR)
    sb.set(0, 0, 3, "minecraft:cobblestone")
    sb.set(0, 1, 3, "minecraft:dark_oak_fence")
    sb.lantern(0, 2, 3)

    sb.jigsaw(2, 1, 0, "north_up", start_key, start_key, "minecraft:empty", AIR, "aligned")
    sb.jigsaw(2, 1, 5, "south_up", "canopycavern:outpost_link", "canopycavern:outpost_link",
              f"canopycavern:{OUTPOST_ID}/{target_pool}", AIR, "aligned")
    return sb


def build_golem_cage() -> V4StructureBuilder:
    """Compact 7x8x7 iron-bar cage holding a captive iron golem on dry ground."""
    sb = V4StructureBuilder(7, 8, 7, fill_block=VOID)
    sb.fill(1, 0, 1, 5, 0, 5, "minecraft:cobblestone")
    sb.fill(2, 0, 0, 4, 0, 0, "minecraft:cobblestone")
    sb.fill(2, 1, 0, 4, 3, 0, AIR)
    sb.fill(1, 1, 1, 5, 4, 5, AIR)
    sb.fill(1, 5, 1, 5, 5, 5, "minecraft:dark_oak_planks")
    sb.fill(2, 6, 2, 4, 6, 4, "minecraft:dark_oak_slab")

    for x, z in ((1, 1), (5, 1), (1, 5), (5, 5)):
        sb.fill(x, 1, z, x, 5, z, "minecraft:dark_oak_log")

    for y in range(1, 4):
        for i in range(2, 5):
            sb.set(i, y, 5, "minecraft:iron_bars")
            sb.set(1, y, i, "minecraft:iron_bars")
            sb.set(5, y, i, "minecraft:iron_bars")
            sb.set(i, y, 1, "minecraft:iron_bars")

    sb.add_golem(3, 1, 3)
    sb.lantern(1, 6, 1)
    sb.lantern(5, 6, 1)
    sb.jigsaw(3, 1, 0, "north_up", "canopycavern:outpost_link", "canopycavern:outpost_link",
              "minecraft:empty", AIR, "aligned")
    stamp_uuids(sb, f"{OUTPOST_ID}/golem_cage")
    sb.validate(f"{OUTPOST_ID}/golem_cage")
    return sb


def build_tent(variant: str, cloth: str, trim: str, chest_side: str) -> V4StructureBuilder:
    """Compact 11x8x9 pillager supply tent with chest, unlit campfire, and garrison."""
    sb = V4StructureBuilder(11, 8, 9, fill_block=VOID)
    sb.fill(2, 0, 1, 8, 0, 7, "minecraft:cobblestone")
    sb.fill(3, 0, 2, 7, 0, 6, "minecraft:coarse_dirt")
    sb.fill(4, 0, 0, 6, 0, 0, "minecraft:cobblestone")
    sb.fill(4, 1, 0, 6, 3, 0, AIR)
    sb.fill(2, 1, 1, 8, 5, 7, AIR)

    for px, pz in ((2, 1), (8, 1), (2, 7), (8, 7)):
        sb.fill(px, 1, pz, px, 4, pz, "minecraft:dark_oak_fence")
    sb.fill(5, 1, 7, 5, 5, 7, "minecraft:dark_oak_log")

    for z in range(1, 8):
        wool = trim if z in (1, 4, 7) else cloth
        sb.fill(2, 1, z, 2, 2, z, wool)
        sb.fill(8, 1, z, 8, 2, z, wool)
        sb.set(3, 3, z, wool)
        sb.set(7, 3, z, wool)
        sb.set(4, 4, z, wool)
        sb.set(6, 4, z, wool)
        sb.set(5, 5, z, wool)
    for x in range(3, 8):
        sb.fill(x, 1, 7, x, 3, 7, trim)
    sb.fill(4, 1, 1, 6, 3, 1, AIR)
    sb.set(5, 4, 1, trim)

    # Small side stone pad holding an unlit campfire (never hazardous blocks under entities)
    sb.fill(0, 0, 3, 1, 0, 4, "minecraft:cobblestone")
    sb.fill(0, 1, 3, 1, 2, 4, AIR)
    sb.set(0, 1, 3, UNLIT_CAMPFIRE)

    if chest_side == "east":
        sb.chest(3, 1, 6, "east", LOOT)
        sb.set(7, 1, 6, "minecraft:fletching_table")
        add_pillager(sb, 5, 1, 4)
    else:
        sb.chest(7, 1, 6, "west", LOOT)
        sb.set(3, 1, 6, "minecraft:smithing_table")
        add_pillager(sb, 5, 1, 4)
    sb.lantern(5, 4, 4, hanging=True)

    sb.jigsaw(5, 1, 0, "north_up", "canopycavern:outpost_link", "canopycavern:outpost_link",
              "minecraft:empty", AIR, "aligned")
    stamp_uuids(sb, f"{OUTPOST_ID}/tent_{variant}")
    sb.validate(f"{OUTPOST_ID}/tent_{variant}")
    return sb


def build_gate_palisade() -> V4StructureBuilder:
    """Compact 9x8x5 dark-oak palisade gate arch and pillager lookout."""
    sb = V4StructureBuilder(9, 8, 5, fill_block=VOID)
    sb.fill(1, 0, 1, 7, 0, 3, "minecraft:cobblestone")
    sb.fill(3, 0, 0, 5, 0, 4, "minecraft:cobblestone")
    sb.fill(1, 1, 1, 7, 6, 3, AIR)

    for px in (1, 2, 6, 7):
        height = 5 if px in (2, 6) else 4
        sb.fill(px, 1, 2, px, height, 2, "minecraft:dark_oak_log")
        sb.set(px, height + 1, 2, "minecraft:dark_oak_fence")
    sb.fill(2, 5, 2, 6, 5, 2, "minecraft:dark_oak_planks")
    sb.fill(2, 6, 2, 6, 6, 2, "minecraft:dark_oak_slab")
    sb.lantern(3, 4, 2, hanging=True)
    sb.lantern(5, 4, 2, hanging=True)
    add_pillager(sb, 4, 1, 2)

    sb.jigsaw(4, 1, 0, "north_up", "canopycavern:outpost_link", "canopycavern:outpost_link",
              "minecraft:empty", AIR, "aligned")
    stamp_uuids(sb, f"{OUTPOST_ID}/gate_palisade")
    sb.validate(f"{OUTPOST_ID}/gate_palisade")
    return sb


def write_pool(pool_name: str, piece_name: str, projection: str):
    v3.write_json(f"worldgen/template_pool/{OUTPOST_ID}/{pool_name}.json", {
        "elements": [{
            "element": {
                "element_type": "minecraft:single_pool_element",
                "location": f"canopycavern:{OUTPOST_ID}/{piece_name}",
                "processors": {"processors": []},
                "projection": projection,
            },
            "weight": 1,
        }],
        "fallback": "minecraft:empty",
    })


def generate_all():
    legacy = v3.STRUCT_DIR / OUTPOST_ID / "stockade.nbt"
    if legacy.exists():
        legacy.unlink()

    build_watchtower_keep().save(f"{OUTPOST_ID}/watchtower_keep.nbt")
    build_golem_cage().save(f"{OUTPOST_ID}/golem_cage.nbt")
    build_tent("west", "minecraft:white_wool", "minecraft:light_gray_wool", "west").save(f"{OUTPOST_ID}/tent_west.nbt")
    build_tent("east", "minecraft:brown_wool", "minecraft:red_wool", "east").save(f"{OUTPOST_ID}/tent_east.nbt")
    build_gate_palisade().save(f"{OUTPOST_ID}/gate_palisade.nbt")

    wings = (
        ("cage", "canopycavern:outpost_north", "golem_cage"),
        ("tent_east", "canopycavern:outpost_east", "tent_east"),
        ("gate", "canopycavern:outpost_south", "gate_palisade"),
        ("tent_west", "canopycavern:outpost_west", "tent_west"),
    )
    for wing, start_key, module in wings:
        build_trail(wing, start_key, module).save(f"{OUTPOST_ID}/trail_{wing}.nbt")
        write_pool(f"wing_{wing}", f"trail_{wing}", "terrain_matching")
        write_pool(module, module, "rigid")

    write_pool("start", "watchtower_keep", "rigid")

    v3.write_json(f"worldgen/structure/{OUTPOST_ID}.json", {
        "type": "canopycavern:surface_jigsaw",
        "biomes": f"#canopycavern:has_structure/{OUTPOST_ID}",
        "max_distance_from_center": 48,
        "project_start_to_heightmap": "WORLD_SURFACE_WG",
        "size": 3,
        "spawn_overrides": {},
        "start_height": {"absolute": 0},
        "start_pool": f"canopycavern:{OUTPOST_ID}/start",
        "step": "surface_structures",
        "terrain_adaptation": "beard_thin",
        "terrain_guard": {
            "allow_water": False,
            "core_probe_radius": 8,
            "foundation_block": "minecraft:cobblestone",
            "max_core_relief": 4,
            "max_foundation_depth": 6,
            "max_piece_embed": 3,
            "max_piece_relief": 5,
            "max_water_depth": 0,
            "min_piece_y_above_sea": -64,
            "min_rigid_pieces": 3,
        },
        "use_expansion_hack": False,
    })


if __name__ == "__main__":
    generate_all()
    print("Generated modular terrain-safe frontier_pillager_outpost!")
