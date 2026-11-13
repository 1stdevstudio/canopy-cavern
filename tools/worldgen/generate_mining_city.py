"""Build the sealed 100×100 civic level of the inhabited expedition mine."""

from dataclasses import dataclass
from uuid import NAMESPACE_URL, uuid5

from generate_v04_ocean_and_villages import V4StructureBuilder, v3

ASSET = "mining_city/city_districts.nbt"
SIZE, HEIGHT = 100, 30
AIR = "minecraft:air"
VOID = "minecraft:structure_void"
TRIM = "minecraft:polished_deepslate"
TILE = "minecraft:deepslate_tiles"
STONE = "minecraft:deepslate_bricks"
COPPER = "minecraft:oxidized_cut_copper"
TIMBER = "minecraft:stripped_spruce_log"
PLANK = "minecraft:spruce_planks"
SUPPLY = "canopycavern:chests/village_supply"
TREASURY = "canopycavern:chests/underground_village_treasury"
ROCK = ("minecraft:deepslate", "minecraft:tuff", "minecraft:cobbled_deepslate")


@dataclass(frozen=True)
class District:
    kind: str
    x: int
    z: int
    radius: int
    roof: int
    accent: str
    jobs: tuple[tuple[str, str], tuple[str, str]]


DISTRICTS = (
    District("market", 24, 23, 19, 17, COPPER,
             (("fisherman", "minecraft:barrel"), ("butcher", "minecraft:smoker"))),
    District("forge", 75, 24, 20, 19, "minecraft:cut_copper",
             (("toolsmith", "minecraft:smithing_table"), ("armorer", "minecraft:blast_furnace"))),
    District("garden", 23, 74, 20, 15, "minecraft:moss_block",
             (("farmer", "minecraft:composter"), ("cleric", "minecraft:brewing_stand"))),
    District("archive", 74, 75, 18, 20, "minecraft:amethyst_block",
             (("librarian", "minecraft:lectern"), ("cartographer", "minecraft:cartography_table"))),
)


def roofline():
    """Map the union of uneven chambers and deliberately graded, level passages."""
    chambers = [(50, 49, 22, 28)] + [(d.x, d.z, d.radius, d.roof) for d in DISTRICTS]
    ceilings = {}
    for x in range(1, SIZE - 1):
        for z in range(1, SIZE - 1):
            height = 0
            for cx, cz, radius, ceiling in chambers:
                radius_sq = ((x - cx) / radius) ** 2 + ((z - cz) / (radius + 1)) ** 2
                if radius_sq >= 1:
                    continue
                noise = ((x * 19 + z * 11 + x * z * 3) % 13 - 6) / 4
                height = max(height, int(ceiling * (1 - radius_sq) ** .5 + noise))
            if height >= 4:
                ceilings[x, z] = min(height, HEIGHT - 2)

    def passage(x0, z0, x1, z1):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                ceilings[x, z] = max(5, ceilings.get((x, z), 0))

    passage(48, 1, 52, 54)
    passage(20, 47, 78, 51)
    for district in DISTRICTS:
        passage(district.x - 2, min(49, district.z), district.x + 2, max(49, district.z))
        # The two dwellings back onto their own frontage at z+6.
        passage(district.x - 12, district.z + 3, district.x + 12, district.z + 6)
    return ceilings


def carve_city(city):
    ceilings = roofline()
    for (x, z), ceiling in ceilings.items():
        paved = abs(x - 50) <= 2 or abs(z - 49) <= 2
        city.set(x, 0, z, TRIM if paved else ROCK[(x + 2 * z) % len(ROCK)])
        for y in range(1, ceiling + 1):
            city.set(x, y, z, AIR)
    # A six-connected rock skin surrounds carved air. The outer rock is kept
    # sparse and doesn't flatten or replace unrelated terrain outside the city.
    for (x, z), ceiling in ceilings.items():
        city.set(x, ceiling + 1, z, ROCK[(x * 3 + z) % len(ROCK)])
        for dx, dz in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, nz = x + dx, z + dz
            for y in range(ceilings.get((nx, nz), 0) + 1, ceiling + 1):
                city.set(nx, y, nz, ROCK[(x * 7 + z * 11 + y) % len(ROCK)])
    for x in range(48, 53):
        city.set(x, 0, 0, TRIM)
        city.set(x, 5, 0, STONE)
    city.fill(49, 1, 0, 51, 4, 0, AIR)


def light_boulevard(city):
    for z in range(4, 40, 6):
        for x in (48, 52):
            city.set(x, 1, z, STONE)
            city.set(x, 2, z, COPPER)
            city.lantern(x, 3, z)
        city.set(50, 0, z, "minecraft:chiseled_deepslate")


def workshop_block(station):
    props = {
        "minecraft:lectern": {"facing": "north", "has_book": "false", "powered": "false"},
        "minecraft:smoker": {"facing": "north", "lit": "false"},
        "minecraft:blast_furnace": {"facing": "north", "lit": "false"},
        "minecraft:stonecutter": {"facing": "north"},
        "minecraft:barrel": {"facing": "north", "open": "false"},
    }
    return (station, props[station]) if station in props else station


def house(city, x, z, accent, profession):
    # Footprint 9×7. Low shoulders rise to a timber gable, inset from the cave roof.
    city.hollow_box(x - 4, 0, z - 3, x + 4, 4, z + 3, STONE, fill_spec=AIR)
    city.fill(x - 3, 0, z - 2, x + 3, 0, z + 2, PLANK)
    for dx in (-4, 4):
        for dz in (-3, 3):
            city.fill(x + dx, 1, z + dz, x + dx, 4, z + dz, TIMBER)
    for rise in range(3):
        city.fill(x - 4 + rise, 5 + rise, z - 3, x + 4 - rise, 5 + rise, z + 3, PLANK)
        for dx, facing in ((-4 + rise, "east"), (4 - rise, "west")):
            for dz in range(-3, 4):
                city.stairs(x + dx, 5 + rise, z + dz, "minecraft:spruce_stairs", facing)
    city.door(x, 1, z - 3, "minecraft:spruce_door", "north")
    for dx in (-2, 2):
        city.set(x + dx, 2, z - 3, "minecraft:cyan_stained_glass")
    city.set(x, 3, z - 3, accent)
    city.bed(x - 2, 1, z - 1, "minecraft:cyan_bed", "north")
    city.set(x + 2, 1, z + 2, ("minecraft:barrel", {"facing": "north", "open": "false"}))
    city.lantern(x, 3, z + 1, hanging=True)
    city.add_villager(x, 1, z, "minecraft:taiga", f"minecraft:{profession}")
    city.entities[-1]["nbt"]["VillagerData"]["level"] = 1


def build_district(city, district):
    x, z = district.x, district.z
    city.fill(x - 12, 0, z - 3, x + 12, 0, z + 6, TILE)
    for dx in (-12, 12):
        city.set(x + dx, 1, z - 2, TRIM)
        city.lantern(x + dx, 2, z - 2)
    for offset, (profession, station) in zip((-4, 4), district.jobs):
        city.set(x + offset, 1, z + 5, workshop_block(station))
        city.fill(x + offset, 4, z + 4, x + offset, 4, z + 6, TIMBER)
        city.lantern(x + offset, 3, z + 5, hanging=True)
        house(city, x + offset * 2, z + 10, district.accent, profession)
        # Direct, level access to the door two blocks beyond the frontage.
        city.set(x + offset * 2, 0, z + 7, TILE)

    if district.kind == "garden":
        for dx in (-10, -9, 9, 10):
            for dz in range(-10, -4):
                city.set(x + dx, 0, z + dz, "minecraft:podzol")
                fungus = "minecraft:red_mushroom" if (dx + dz) % 2 else "minecraft:brown_mushroom"
                city.set(x + dx, 1, z + dz, fungus)
    elif district.kind == "archive":
        for dx in (-10, 10):
            for dz in range(-9, -4):
                city.fill(x + dx, 1, z + dz, x + dx, 2, z + dz, "minecraft:bookshelf")
                city.set(x + dx, 3, z + dz, district.accent)
    elif district.kind == "forge":
        for dx in (-10, 10):
            city.set(x + dx, 1, z - 6, "minecraft:anvil")
            city.set(x + dx, 1, z - 7, "minecraft:cauldron")
            city.fill(x + dx, 1, z - 9, x + dx, 2, z - 9, district.accent)
    else:
        for dx in (-9, 9):
            city.fill(x + dx - 1, 1, z - 7, x + dx + 1, 1, z - 7, PLANK)
            for post in (-1, 1):
                city.fill(x + dx + post, 2, z - 7, x + dx + post, 4, z - 7, TIMBER)
            city.fill(x + dx - 2, 5, z - 8, x + dx + 2, 5, z - 6, district.accent)
            city.lantern(x + dx, 4, z - 7, hanging=True)

    city.chest(x - 10, 1, z + 3, "north", SUPPLY)


def public_facility(city, district):
    """Add a usable public building on the north side of each district."""
    x, z = district.x, district.z
    outer = {
        "market": "minecraft:mossy_stone_bricks",
        "forge": "minecraft:tuff_bricks",
        "garden": "minecraft:calcite",
        "archive": STONE,
    }[district.kind]
    city.fill(x - 5, 0, z - 12, x + 5, 0, z - 4, TRIM)
    city.fill(x - 5, 1, z - 12, x + 5, 1, z - 12, outer)
    for dx in (-5, 5):
        city.fill(x + dx, 1, z - 11, x + dx, 1, z - 4, outer)
        for dz in (-12, -8, -4):
            city.fill(x + dx, 2, z + dz, x + dx, 4, z + dz, TIMBER)
    for dx in (-4, 4):
        city.fill(x + dx, 1, z - 4, x + dx, 4, z - 4, outer)
    city.fill(x - 4, 4, z - 4, x + 4, 4, z - 4, outer)

    if district.kind == "market":
        # Canteen with a high timber roof, tables and a food counter.
        for step in range(4):
            city.fill(x - 5 + step, 5 + step, z - 12, x + 5 - step, 5 + step, z - 4, PLANK)
        city.set(x - 4, 1, z - 10, "minecraft:hay_block")
        for dx in (-3, 3):
            city.set(x + dx, 1, z - 7, PLANK)
            city.stairs(x + dx, 1, z - 6, "minecraft:spruce_stairs", "north")
            city.stairs(x + dx, 1, z - 8, "minecraft:spruce_stairs", "south")
        city.set(x + 3, 1, z - 11, ("minecraft:smoker", {"facing": "south", "lit": "false"}))
        city.set(x + 4, 1, z - 11, workshop_block("minecraft:barrel"))
    elif district.kind == "forge":
        # Stone work shed with a raised copper hood and cold furnaces.
        city.fill(x - 5, 5, z - 12, x + 5, 5, z - 4, "minecraft:polished_tuff")
        city.fill(x - 3, 6, z - 11, x + 3, 6, z - 5, district.accent)
        city.fill(x + 3, 6, z - 10, x + 4, 8, z - 9, outer)
        city.set(x - 4, 1, z - 10, ("minecraft:anvil", {"facing": "north"}))
        city.set(x - 4, 1, z - 8, workshop_block("minecraft:stonecutter"))
        city.set(x + 4, 1, z - 10, workshop_block("minecraft:blast_furnace"))
        city.set(x + 4, 1, z - 8, "minecraft:cauldron")
        city.set(x - 4, 1, z - 6, "minecraft:smithing_table")
    elif district.kind == "garden":
        # Grow house with low beds on podzol. Mushrooms can remain below lamps
        # because podzol allows placement independent of light level.
        city.fill(x - 5, 5, z - 12, x + 5, 5, z - 4, COPPER)
        city.fill(x - 3, 5, z - 11, x + 3, 5, z - 5, "minecraft:green_stained_glass")
        city.fill(x - 2, 6, z - 10, x + 2, 6, z - 6, "minecraft:green_stained_glass")
        for dx in (-4, 4):
            for dz in range(-11, -6):
                city.set(x + dx, 0, z + dz, "minecraft:podzol")
                mushroom = "brown_mushroom" if dz % 2 == 0 else "red_mushroom"
                city.set(x + dx, 1, z + dz, f"minecraft:{mushroom}")
        city.set(x + 4, 1, z - 6, "minecraft:composter")
    else:
        # Reading hall with beveled vault, shelves and a second survey station.
        for step in range(3):
            city.fill(x - 5 + step, 5 + step, z - 12 + step, x + 5 - step, 5 + step, z - 4 - step, TILE)
        for dx in (-4, 4):
            city.fill(x + dx, 1, z - 11, x + dx, 2, z - 8, "minecraft:bookshelf")
        city.set(x + 4, 1, z - 6, workshop_block("minecraft:lectern"))
        city.set(x - 4, 1, z - 6, "minecraft:cartography_table")

    for dz in (-10, -6):
        city.fill(x - 4, 4, z + dz, x + 4, 4, z + dz, TIMBER)
        city.lantern(x, 3, z + dz, hanging=True)


def civic_hall(city):
    # A 24×24 floor, octagonal edge inlay, and elevated timber beams.
    city.fill(38, 0, 38, 61, 0, 61, TILE)
    for x in range(38, 62):
        for z in range(38, 62):
            if abs(2 * x - 99) + abs(2 * z - 99) == 36:
                city.set(x, 0, z, COPPER)
    for x in (40, 59):
        for z in (40, 59):
            city.fill(x, 1, z, x, 8, z, STONE)
            city.set(x, 5, z, "minecraft:amethyst_block")
        city.fill(x, 8, 40, x, 8, 59, TIMBER)
        for z in (44, 50, 55):
            city.lantern(x, 7, z, hanging=True)
    city.fill(40, 8, 50, 59, 8, 50, TIMBER)
    city.lantern(50, 7, 50, hanging=True)
    city.set(52, 1, 53, ("minecraft:bell", {"attachment": "floor", "facing": "north", "powered": "false"}))
    city.chest(55, 1, 55, "north", TREASURY)
    city.add_sentinel(46, 1, 51)


def build():
    city = V4StructureBuilder(SIZE, HEIGHT, SIZE, fill_block=None)
    carve_city(city)
    light_boulevard(city)
    for district in DISTRICTS:
        build_district(city, district)
        public_facility(city, district)
    civic_hall(city)
    for index, entity in enumerate(city.entities):
        value = uuid5(NAMESPACE_URL, f"canopycavern:{ASSET}/{index}").bytes
        entity["nbt"]["UUID"] = v3.nbt_int_array([
            int.from_bytes(value[i:i + 4], "big", signed=True) for i in range(0, 16, 4)
        ])
    city.validate("Mining City")
    return city


if __name__ == "__main__":
    build().save(ASSET)
