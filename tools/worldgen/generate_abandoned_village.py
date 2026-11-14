"""Generate modular terrain-conforming abandoned mega village templates and worldgen data."""

from uuid import NAMESPACE_URL, uuid5

from generate_v04_ocean_and_villages import V4StructureBuilder, v3

VILLAGE_ID = "abandoned_mega_village"
LOOT = f"canopycavern:chests/{VILLAGE_ID}"
AIR = "minecraft:air"
VOID = "minecraft:structure_void"
MASONRY = (
    "minecraft:stone_bricks",
    "minecraft:mossy_stone_bricks",
    "minecraft:cracked_stone_bricks",
    "minecraft:mossy_cobblestone",
)
DIRECTIONS = ("north", "east", "south", "west")


def masonry_at(x: int, y: int, z: int, variant: int = 0) -> str:
    return MASONRY[(x * 7 + y * 13 + z * 11 + variant * 5) % len(MASONRY)]


def stamp_uuids(builder: V4StructureBuilder, seed_key: str):
    for index, entity in enumerate(builder.entities):
        value = uuid5(NAMESPACE_URL, f"canopycavern:{seed_key}/{index}").bytes
        entity["nbt"]["UUID"] = v3.nbt_int_array(
            [int.from_bytes(value[i:i + 4], "big", signed=True) for i in range(0, 16, 4)]
        )


def add_zombie_villager(builder: V4StructureBuilder, x: int, y: int, z: int):
    builder.clear_headroom(x, y, z, 2)
    builder.add_entity(x + 0.5, float(y), z + 0.5, "minecraft:zombie_villager", {
        "PersistenceRequired": 1,
        "ConversionTime": -1,
    })


def build_belfry_plaza() -> V4StructureBuilder:
    """Compact 13x20x13 ruined stone plaza + 18-high decaying belfry with bell & 4 wing sockets."""
    sb = V4StructureBuilder(13, 20, 13, fill_block=VOID)
    for x in range(2, 11):
        for z in range(2, 11):
            sb.set(x, 0, z, masonry_at(x, 0, z))
    sb.fill(2, 1, 2, 10, 4, 10, AIR)

    for x0, x1, z0, z1 in ((5, 7, 0, 1), (5, 7, 11, 12), (0, 1, 5, 7), (11, 12, 5, 7)):
        sb.fill(x0, 0, z0, x1, 0, z1, "minecraft:mossy_cobblestone")
        sb.fill(x0, 1, z0, x1, 3, z1, AIR)

    # Crumbling corner lantern posts
    for lx, lz in ((2, 2), (10, 2), (2, 10), (10, 10)):
        sb.set(lx, 1, lz, "minecraft:mossy_cobblestone")
        sb.lantern(lx, 2, lz)

    # 5x5 ruined belfry centered at (4..8, 4..8) climbing to y=18
    for px, pz in ((4, 4), (8, 4), (4, 8), (8, 8)):
        sb.fill(px, 1, pz, px, 17, pz, masonry_at(px, 3, pz))
    for y in range(4, 13):
        for i in range(4, 9):
            for wx, wz in ((i, 4), (i, 8), (4, i), (8, i)):
                if (wx, wz) in ((4, 4), (8, 4), (4, 8), (8, 8)):
                    continue
                if y in (6, 10) and i == 6:
                    sb.set(wx, y, wz, "minecraft:iron_bars")
                elif (wx + y * 3 + wz) % 7 != 0:
                    sb.set(wx, y, wz, masonry_at(wx, y, wz))
    sb.fill(5, 1, 5, 7, 15, 7, AIR)
    for x in range(4, 9):
        for z in range(4, 9):
            sb.set(x, 16, z, masonry_at(x, 16, z))
            if (x, z) not in ((4, 4), (8, 4)):
                sb.set(x, 17, z, masonry_at(x, 17, z))
    sb.fill(5, 18, 5, 7, 18, 7, "minecraft:mossy_stone_bricks")

    sb.set(6, 15, 6, ("minecraft:bell", {"attachment": "ceiling", "facing": "north", "powered": "false"}))
    sb.lantern(5, 15, 5, hanging=True)
    sb.set(6, 1, 6, "minecraft:mossy_cobblestone")
    sb.set(4, 2, 5, "minecraft:cobweb")
    sb.set(7, 15, 5, "minecraft:cobweb")

    sb.jigsaw(6, 1, 0, "north_up", "canopycavern:ruin_north", "canopycavern:ruin_north",
              f"canopycavern:{VILLAGE_ID}/wing_north", AIR, "aligned")
    sb.jigsaw(12, 1, 6, "east_up", "canopycavern:ruin_east", "canopycavern:ruin_east",
              f"canopycavern:{VILLAGE_ID}/wing_east", AIR, "aligned")
    sb.jigsaw(6, 1, 12, "south_up", "canopycavern:ruin_south", "canopycavern:ruin_south",
              f"canopycavern:{VILLAGE_ID}/wing_south", AIR, "aligned")
    sb.jigsaw(0, 1, 6, "west_up", "canopycavern:ruin_west", "canopycavern:ruin_west",
              f"canopycavern:{VILLAGE_ID}/wing_west", AIR, "aligned")

    stamp_uuids(sb, f"{VILLAGE_ID}/belfry_plaza")
    sb.validate(f"{VILLAGE_ID}/belfry_plaza")
    return sb


def build_ruined_street(direction: str) -> V4StructureBuilder:
    """Short 5x5x9 terrain-matching overgrown lane connecting plaza to a collapsed hall."""
    sb = V4StructureBuilder(5, 5, 9, fill_block=VOID)
    variant = DIRECTIONS.index(direction)
    for z in range(9):
        for x in range(1, 4):
            block = "minecraft:coarse_dirt" if (x + z + variant) % 3 == 0 else "minecraft:mossy_cobblestone"
            sb.set(x, 0, z, block)
    sb.fill(1, 1, 0, 3, 3, 8, AIR)
    sb.set(0, 0, 4, "minecraft:mossy_cobblestone")
    sb.set(0, 1, 4, "minecraft:cobblestone_wall")
    sb.lantern(0, 2, 4)

    sb.jigsaw(2, 1, 0, "north_up", f"canopycavern:ruin_{direction}", f"canopycavern:ruin_{direction}",
              "minecraft:empty", AIR, "aligned")
    sb.jigsaw(2, 1, 8, "south_up", "canopycavern:ruin_link", "canopycavern:ruin_link",
              f"canopycavern:{VILLAGE_ID}/hall_{direction}", AIR, "aligned")
    return sb


def build_ruined_hall(direction: str, variant: int) -> V4StructureBuilder:
    """Compact 11x11x11 collapsed masonry hall with dark oak door, cobwebs, loot, and zombie villager."""
    sb = V4StructureBuilder(11, 11, 11, fill_block=VOID)
    sb.hollow_box(1, 0, 1, 9, 5, 9, "minecraft:stone_bricks", fill_spec=AIR)
    for x in range(1, 10):
        for z in range(1, 10):
            sb.set(x, 0, z, masonry_at(x, 0, z, variant))
            for y in range(1, 6):
                if x in (1, 9) or z in (1, 9):
                    sb.set(x, y, z, masonry_at(x, y, z, variant))

    # Entrance threshold aligned with (5, 1, 0)
    sb.fill(4, 0, 0, 6, 0, 0, "minecraft:mossy_cobblestone")
    sb.fill(4, 1, 0, 6, 3, 0, AIR)
    sb.door(5, 1, 1, "minecraft:dark_oak_door", "north")

    # Barred windows
    for wx, wz in ((3, 1), (7, 1), (1, 5), (9, 5), (5, 9)):
        sb.set(wx, 2, wz, "minecraft:iron_bars")
        sb.set(wx, 3, wz, "minecraft:iron_bars")

    # Partial breached roof + dark_oak_stairs gables
    for z in range(1, 10):
        for step in range(4):
            y = 5 + step
            lx, rx = 1 + step, 9 - step
            if (z + variant + step) % 5 != 0:
                sb.stairs(lx, y, z, "minecraft:dark_oak_stairs", "east")
            if (z + variant * 2 + step) % 4 != 0:
                sb.stairs(rx, y, z, "minecraft:dark_oak_stairs", "west")
        if (z + variant) % 3 != 0:
            sb.set(5, 9, z, "minecraft:dark_oak_slab")

    # Collapse a few upper edge blocks for authentic ruin silhouette without breaking chest/entity clearance
    sb.set(1, 4, 8, AIR)
    sb.set(9, 4, 2, AIR)
    sb.set(2, 4, 2, "minecraft:cobweb")
    sb.set(8, 4, 8, "minecraft:cobweb")
    sb.set(2, 4, 8, "minecraft:cobweb")

    sb.set(2, 1, 8, "minecraft:mossy_cobblestone")
    sb.chest(8, 1, 8, "west", LOOT)
    sb.lantern(2, 2, 8)
    add_zombie_villager(sb, 5, 1, 5)

    sb.jigsaw(5, 1, 0, "north_up", "canopycavern:ruin_link", "canopycavern:ruin_link",
              "minecraft:empty", AIR, "aligned")
    stamp_uuids(sb, f"{VILLAGE_ID}/ruined_hall_{direction}")
    sb.validate(f"{VILLAGE_ID}/ruined_hall_{direction}")
    return sb


def write_pool(pool_name: str, piece_name: str, projection: str):
    v3.write_json(f"worldgen/template_pool/{VILLAGE_ID}/{pool_name}.json", {
        "elements": [{
            "element": {
                "element_type": "minecraft:single_pool_element",
                "location": f"canopycavern:{VILLAGE_ID}/{piece_name}",
                "processors": {"processors": []},
                "projection": projection,
            },
            "weight": 1,
        }],
        "fallback": "minecraft:empty",
    })


def generate_all():
    legacy = v3.STRUCT_DIR / VILLAGE_ID / "ruins.nbt"
    if legacy.exists():
        legacy.unlink()

    build_belfry_plaza().save(f"{VILLAGE_ID}/belfry_plaza.nbt")
    write_pool("start", "belfry_plaza", "rigid")

    for index, direction in enumerate(DIRECTIONS):
        build_ruined_street(direction).save(f"{VILLAGE_ID}/ruined_street_{direction}.nbt")
        build_ruined_hall(direction, index).save(f"{VILLAGE_ID}/ruined_hall_{direction}.nbt")
        write_pool(f"wing_{direction}", f"ruined_street_{direction}", "terrain_matching")
        write_pool(f"hall_{direction}", f"ruined_hall_{direction}", "rigid")

    v3.write_json(f"worldgen/structure/{VILLAGE_ID}.json", {
        "type": "canopycavern:surface_jigsaw",
        "biomes": f"#canopycavern:has_structure/{VILLAGE_ID}",
        "max_distance_from_center": 48,
        "project_start_to_heightmap": "WORLD_SURFACE_WG",
        "size": 3,
        "spawn_overrides": {},
        "start_height": {"absolute": 0},
        "start_pool": f"canopycavern:{VILLAGE_ID}/start",
        "step": "surface_structures",
        "terrain_adaptation": "beard_thin",
        "terrain_guard": {
            "allow_water": False,
            "core_probe_radius": 8,
            "foundation_block": "minecraft:mossy_stone_bricks",
            "max_core_relief": 4,
            "max_foundation_depth": 6,
            "max_piece_embed": 3,
            "max_piece_relief": 5,
            "max_water_depth": 0,
            "min_piece_y_above_sea": -64,
            "min_rigid_pieces": 4,
        },
        "use_expansion_hack": False,
    })


if __name__ == "__main__":
    generate_all()
    print("Generated modular terrain-safe abandoned_mega_village!")
