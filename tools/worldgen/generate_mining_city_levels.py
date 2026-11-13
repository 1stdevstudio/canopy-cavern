"""Generate three mining city stations with a shared west-side access contract."""

from generate_v04_ocean_and_villages import V4StructureBuilder, v3

ASSET_ROOT = "mining_city"
ENTRY_Z = 12
ASSET_NAMES = {"industry": "industry_district", "excavation": "excavation_district"}
LEVELS = {
    "surface": (89, 19, 33),
    "industry": (27, 12, 25),
    "excavation": (31, 14, 25),
}
AIR = "minecraft:air"
VOID = "minecraft:structure_void"
STONE = "minecraft:deepslate_bricks"
LOG = "minecraft:stripped_spruce_log"
WOOD = "minecraft:spruce_planks"
ROAD = "minecraft:polished_tuff"
SUPPLY = "canopycavern:chests/village_supply"
MINING_LOOT = "canopycavern:chests/echoing_mineshaft"
RAIL = ("minecraft:rail", {"shape": "east_west", "waterlogged": "false"})


def station(name):
    return V4StructureBuilder(*LEVELS[name], fill_block=VOID)


def open_entry(site):
    site.fill(0, 0, ENTRY_Z - 1, 3, 0, ENTRY_Z + 1, ROAD)
    site.fill(0, 1, ENTRY_Z - 1, 3, 3, ENTRY_Z + 1, AIR)
    site.fill(0, 4, ENTRY_Z - 1, 3, 4, ENTRY_Z + 1, STONE)
    site.lantern(1, 3, ENTRY_Z, hanging=True)


def surface():
    site = station("surface")
    # Continuous square-cut foundation. The worldgen piece supports it where terrain dips.
    site.fill(0, 0, 0, 28, 0, 24, "minecraft:cobbled_deepslate")
    site.fill(0, 0, 8, 28, 0, 17, ROAD)
    site.fill(0, 1, 0, 28, 4, 24, AIR)

    # Open-sided warehouse and workshop. Offset footprints distinguish the two rooflines.
    for z, raised in ((3, False), (16, True)):
        x = 17 if raised else 15
        width = 9
        site.fill(x, 0, z, x + width - 1, 0, z + 5, WOOD)
        site.fill(x, 1, z + 5, x + width - 1, 3, z + 5, WOOD)
        for px in (x, x + width - 1):
            for pz in (z, z + 5):
                site.fill(px, 1, pz, px, 4, pz, LOG)
        for dx in range(-1, width + 1):
            rise = min(dx + 1, width - dx)
            y = 4 + rise
            for pz in range(z - 1, z + 7):
                if dx == width // 2:
                    site.slab(x + dx, y, pz, "minecraft:dark_oak_slab")
                else:
                    site.stairs(x + dx, y, pz, "minecraft:dark_oak_stairs",
                                "east" if dx < width // 2 else "west")
            if rise:
                site.fill(x + dx, 4, z + 5, x + dx, y - 1, z + 5, WOOD)
        site.fill(x, 4, z, x + width - 1, 4, z, LOG)
        site.lantern(x + 2, 3, z, hanging=True)
        site.lantern(x + 6, 3, z, hanging=True)
        site.chest(x + 1, 1, z + 4, "north", SUPPLY)
    site.set(19, 1, 20, "minecraft:smithing_table")
    site.set(20, 1, 20, ("minecraft:blast_furnace", {"facing": "north", "lit": "false"}))
    for x in range(11, 25):
        site.set(x, 1, 10, RAIL)
    site.fill(25, 1, 10, 25, 1, 10, "minecraft:polished_andesite")
    for x in (8, 10):
        site.fill(x, 1, 7, x, 1, 8, "minecraft:barrel")

    # Hoist frame over the west approach. Wheel is a block sculpture, not a lift.
    for x in (2, 8):
        for z in (9, 15):
            site.set(x, 1, z, STONE)
            site.fill(x, 2, z, x, 8, z, LOG)
        site.fill(x, 8, 9, x, 8, 15, LOG)
    for z in (9, 15):
        site.fill(2, 8, z, 8, 8, z, LOG)
    site.fill(2, 8, 12, 8, 8, 12, LOG)
    for dx, dy in ((-2, -1), (-2, 0), (-2, 1), (2, -1), (2, 0), (2, 1),
                   (-1, -2), (0, -2), (1, -2), (-1, 2), (0, 2), (1, 2),
                   (0, -1), (0, 0), (0, 1), (-1, 0), (1, 0)):
        site.set(5 + dx, 9 + dy, 12, "minecraft:dark_oak_planks")
    site.fill(5, 5, 12, 5, 7, 12, "minecraft:iron_chain")
    for x in (2, 8):
        site.set(x, 4, 11, WOOD)
        site.lantern(x, 3, 11, hanging=True)
    open_entry(site)
    # A recessed stone portal and contrasting guide strip make the descent visible from the yard.
    for z in (10, 14):
        site.fill(0, 1, z, 0, 5, z, STONE)
        site.set(1, 4, z, WOOD)
        site.lantern(1, 3, z, hanging=True)
    site.fill(0, 5, 11, 0, 5, 13, "minecraft:polished_deepslate")
    site.set(0, 6, 12, "minecraft:sea_lantern")
    for x in range(1, 15):
        site.set(x, 0, 12, "minecraft:polished_andesite")
    site.fill(29, 0, 7, 88, 0, 16, STONE)
    site.fill(29, 1, 7, 88, 4, 16, AIR)
    site.fill(29, 0, 12, 88, 0, 14, "minecraft:polished_andesite")
    for x in range(25, 85):
        site.set(x, 1, 10, RAIL)
    site.set(85, 1, 10, "minecraft:polished_andesite")
    for a, b, height, back in ((31, 47, 6, 28), (50, 64, 5, 26), (68, 87, 8, 31)):
        site.fill(a, 0, 17, b, 0, back, STONE)
        site.fill(a, 1, 17, b, height - 1, back, AIR)
        site.fill(a, 1, back, b, height - 1, back, STONE)
        for x in range(a, b + 1):
            for z in range(17, back + 1):
                rise = min(z - 17, back - z)
                site.stairs(x, height + rise, z, "minecraft:dark_oak_stairs",
                            "south" if 2*z < 17 + back else "north")
                if x in (a,b) and rise:
                    site.fill(x, height, z, x, height + rise - 1, z, WOOD)
        for x in (a, (a+b)//2, b):
            for z in (17, back):
                site.fill(x, 1, z, x, height, z, LOG)
        for x in range(a + 3, b, 4):
            if a == 31:
                site.set(x, 1, back - 1, ("minecraft:blast_furnace", {"facing": "north", "lit": "false"}))
                site.fill(x, 2, back - 1, x, height + 3, back - 1, STONE)
            else:
                site.set(x, 1, back - 1, "minecraft:barrel")
        site.chest(a + 2, 1, 20, "north", SUPPLY)
    for x in (31, 53, 75, 86):
        for z in (8, 15):
            site.fill(x, 1, z, x, 6, z, LOG)
        site.fill(x, 5, 8, x, 5, 15, LOG)
        site.lantern(x, 4, 13, hanging=True)
    return site


def industry():
    site = station("industry")
    site.hollow_box(0, 0, 0, 26, 6, 24, STONE, AIR)
    site.fill(1, 0, 1, 25, 0, 23, "minecraft:polished_deepslate")
    site.fill(1, 0, 11, 25, 0, 13, ROAD)
    # Taller loading nave rises above the workshops with a sealed, stepped vault.
    for z in range(7, 18):
        for x in range(13, 25):
            crown = 7 + min(2, x - 13, 24 - x)
            for y in range(6, crown):
                border = z in (7, 17) or x in (13, 24)
                site.set(x, y, z, STONE if border else AIR)
            site.set(x, crown, z, STONE)
    for x in (16, 19, 22):
        site.set(x, 8, 12, "minecraft:sea_lantern")
    for x in (4, 10, 16, 22):
        for z in (4, 20):
            site.fill(x, 1, z, x, 5, z, LOG)
        site.fill(x, 5, 4, x, 5, 20, LOG)
        for z in (8, 16):
            site.lantern(x, 4, z, hanging=True)
    for x in range(4, 22):
        site.set(x, 1, 9, RAIL)
    site.set(22, 1, 9, STONE)
    # Loading bay and workshop fronts stay clear of track and tank.
    site.fill(4, 0, 3, 20, 0, 7, "minecraft:polished_andesite")
    for x in (5, 7, 9):
        site.set(x, 1, 3, ("minecraft:blast_furnace", {"facing": "south", "lit": "false"}))
    site.set(11, 1, 3, "minecraft:smithing_table")
    site.set(14, 1, 3, "minecraft:stonecutter")
    site.chest(19, 1, 4, "south", SUPPLY)
    site.chest(22, 1, 18, "north", SUPPLY)

    # Masonry furnace shelter and a separate timber dispatch office face the main route.
    for x in (4, 12):
        for z in (4, 7):
            site.fill(x, 1, z, x, 4, z, "minecraft:polished_deepslate")
    site.fill(4, 4, 4, 12, 4, 7, "minecraft:deepslate_tiles")
    for x in range(4, 13):
        site.stairs(x, 5, 7, "minecraft:deepslate_tile_stairs", "north")
    site.lantern(6, 3, 7, hanging=True)
    site.lantern(10, 3, 7, hanging=True)

    site.fill(14, 0, 17, 20, 0, 21, WOOD)
    site.fill(14, 1, 21, 20, 3, 21, WOOD)
    for x in (14, 20):
        for z in (17, 21):
            site.fill(x, 1, z, x, 3, z, LOG)
    site.set(14, 1, 20, WOOD)
    site.set(16, 1, 20, "minecraft:cartography_table")
    site.set(18, 1, 20, "minecraft:barrel")
    site.fill(14, 4, 17, 20, 4, 21, WOOD)
    for x in range(14, 21):
        site.stairs(x, 4, 21, "minecraft:spruce_stairs", "north")
    site.lantern(17, 3, 17, hanging=True)

    # Fully enclosed viewing tank; copper pipe stays on top of the glass lid.
    site.hollow_box(5, 0, 16, 12, 3, 21, STONE, "minecraft:water")
    site.fill(6, 1, 16, 11, 2, 16, "minecraft:glass")
    site.fill(6, 1, 21, 11, 2, 21, "minecraft:glass")
    site.fill(6, 3, 17, 11, 3, 20, "minecraft:glass")
    site.fill(8, 4, 18, 8, 4, 20, "minecraft:cut_copper")
    site.set(8, 5, 20, "minecraft:cut_copper")
    site.set(8, 5, 21, "minecraft:cut_copper")
    open_entry(site)
    return site


def excavation():
    site = station("excavation")
    # Overlapping chambers give the excavation uneven shoulders and a varied ceiling.
    cells = set()
    for x in range(1, 30):
        for z in range(1, 24):
            field = min(((x-10)/9)**2 + ((z-12)/8)**2,
                        ((x-20)/10)**2 + ((z-14)/10)**2,
                        ((x-23)/6)**2 + ((z-7)/6)**2)
            if field < 1:
                height = 4 + int(6 * (1 - field)**0.5)
                cells.update((x, y, z) for y in range(1, height))
    cells.update((x, y, z) for x in range(4) for z in range(11, 14) for y in range(1, 4))
    # Seal the carved space everywhere except the exact west-side entrance.
    for x, y, z in sorted(cells):
        site.set(x, y, z, AIR)
        for dx, dy, dz in ((-1,0,0),(1,0,0),(0,-1,0),(0,1,0),(0,0,-1),(0,0,1)):
            neighbor = x+dx, y+dy, z+dz
            if neighbor not in cells:
                nx, ny, nz = neighbor
                rock = "minecraft:tuff" if (nx*7+ny*3+nz*11) % 5 == 0 else "minecraft:deepslate"
                if ny == 0:
                    rock = ROAD
                site.set(nx, ny, nz, rock)
    for x in range(5, 19):
        site.set(x, 1, 13, RAIL)
    site.set(19, 1, 13, STONE)
    for x in (7, 13, 18):
        for z in (9, 15):
            site.fill(x, 1, z, x, 4, z, LOG)
        site.fill(x, 4, 9, x, 4, 15, LOG)
        site.lantern(x, 3, 12, hanging=True)

    # Unmined crystal face and a dry survey post at the end of the track.
    for x, z, height in ((21, 6, 4), (24, 9, 5), (26, 12, 4), (25, 19, 3), (21, 21, 4)):
        site.set(x, 1, z, "minecraft:calcite")
        site.fill(x, 2, z, x, height, z, "minecraft:amethyst_block")
        site.set(x, height + 1, z,
                 ("minecraft:amethyst_cluster", {"facing": "up", "waterlogged": "false"}))
    for x, z, height in ((21, 5, 3), (22, 5, 4), (23, 5, 5), (24, 6, 4), (25, 7, 3)):
        site.set(x, 1, z, "minecraft:calcite")
        site.fill(x, 2, z, x, height, z, "minecraft:amethyst_block")
    site.set(20, 1, 8, "minecraft:stonecutter")
    site.set(21, 1, 8, "minecraft:cartography_table")

    # Survey shelter: attached props, clear aisles and a roof with a stepped ridge.
    site.fill(19, 0, 17, 24, 0, 20, WOOD)
    for x in (19, 24):
        for z in (17, 20):
            site.fill(x, 1, z, x, 3, z, LOG)
    for x in range(19, 25):
        for z in range(17, 21):
            if x in (21, 22):
                site.slab(x, 6, z, "minecraft:dark_oak_slab")
            else:
                y = 4 if x in (19, 24) else 5
                site.stairs(x, y, z, "minecraft:dark_oak_stairs", "east" if x < 21 else "west")
    site.fill(19, 4, 17, 24, 4, 17, LOG)
    site.set(21, 1, 19, ("minecraft:lectern", {"facing": "north", "has_book": "false", "powered": "false"}))
    site.chest(22, 1, 19, "north", MINING_LOOT)
    site.lantern(22, 3, 17, hanging=True)
    open_entry(site)
    return site


def build_levels():
    levels = {"surface": surface(), "industry": industry(), "excavation": excavation()}
    for name, site in levels.items():
        site.validate(f"{ASSET_ROOT}/{name}")
    return levels


if __name__ == "__main__":
    for name, site in build_levels().items():
        site.save(f"{ASSET_ROOT}/{ASSET_NAMES.get(name, name)}.nbt")
