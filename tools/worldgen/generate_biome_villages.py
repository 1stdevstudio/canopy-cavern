"""Generate the six biome village templates without replacing the original center assets."""

from dataclasses import dataclass
from uuid import NAMESPACE_URL, uuid5

from generate_v04_ocean_and_villages import V4StructureBuilder, v3


@dataclass(frozen=True)
class Theme:
    villager: str
    floor: str
    wall: str
    frame: str
    roof: str
    stairs: str
    door: str
    path: str
    accent: str
    profile: str


THEMES = {
    "jungle_canopy_hamlet": Theme("jungle", "bamboo_mosaic", "jungle_planks", "stripped_jungle_log",
                                  "bamboo_planks", "bamboo_stairs", "jungle_door", "coarse_dirt",
                                  "moss_block", "tall_gable"),
    "mangrove_marsh_village": Theme("swamp", "mud_bricks", "mangrove_planks", "stripped_mangrove_log",
                                    "mangrove_planks", "mangrove_stairs", "mangrove_door", "packed_mud",
                                    "mangrove_roots", "hip"),
    "badlands_pueblo": Theme("desert", "red_sandstone", "orange_terracotta", "chiseled_red_sandstone",
                              "smooth_red_sandstone", "red_sandstone_stairs", "acacia_door",
                              "red_sandstone", "yellow_terracotta", "terrace"),
    "cherry_grove_hamlet": Theme("plains", "cherry_planks", "cherry_planks", "stripped_cherry_log",
                                 "dark_oak_planks", "dark_oak_stairs", "cherry_door", "coarse_dirt",
                                 "pink_wool", "double_eave"),
    "mushroom_island_outpost": Theme("plains", "moss_block", "oak_planks", "mushroom_stem",
                                    "red_mushroom_block", "oak_stairs", "oak_door", "mycelium",
                                    "brown_mushroom_block", "cap"),
    "frozen_ridge_village": Theme("snow", "spruce_planks", "spruce_log", "stripped_spruce_log",
                                  "spruce_planks", "spruce_stairs", "spruce_door", "snow_block",
                                  "packed_ice", "snow_gable"),
}
AIR = "minecraft:air"
LOOT = "canopycavern:chests/village_supply"


def mc(name):
    return f"minecraft:{name}"


def build_gable(builder, x, z, theme, steep=False, extra_eave=False):
    for step in range(5):
        west, east = x - 1 + step, x + 8 - step
        y = 5 + step * (2 if steep else 1)
        for pz in range(z - 1, z + 9):
            builder.stairs(west, y, pz, mc(theme.stairs), "east")
            builder.stairs(east, y, pz, mc(theme.stairs), "west")
            if steep and step > 0:
                builder.set(west, y - 1, pz, mc(theme.roof))
                builder.set(east, y - 1, pz, mc(theme.roof))
        for front in (z, z + 7):
            if west + 1 < east:
                builder.fill(west + 1, y, front, east - 1, y + int(steep), front, mc(theme.wall))
    if extra_eave:
        for pz in range(z - 1, z + 9):
            builder.stairs(x - 1, 4, pz, mc(theme.stairs), "east", half="top")
            builder.stairs(x + 8, 4, pz, mc(theme.stairs), "west", half="top")


def build_roof(builder, x, z, theme, house_index):
    profile = theme.profile
    if profile == "tall_gable":
        build_gable(builder, x, z, theme, steep=house_index == 0)
    elif profile == "double_eave":
        build_gable(builder, x, z, theme, extra_eave=True)
        builder.fill(x + 3, 10, z, x + 4, 10, z + 7, mc(theme.frame))
    elif profile == "snow_gable":
        build_gable(builder, x, z, theme, steep=True)
        builder.fill(x + 3, 14, z, x + 4, 14, z + 7, "minecraft:snow_block")
    elif profile == "hip":
        builder.hipped_pyramid_roof(x - 1, x + 8, 5, z - 1, z + 8, mc(theme.roof),
                                    mc(theme.stairs), "minecraft:mangrove_slab")
    elif profile == "terrace":
        builder.fill(x, 6, z, x + 7, 6, z + 7, mc(theme.wall))
        for offset in range(0, 8, 2):
            for px, pz in ((x + offset, z), (x + offset, z + 7), (x, z + offset), (x + 7, z + offset)):
                builder.set(px, 7, pz, mc(theme.accent))
        builder.fill(x + 2, 7, z + 2, x + 5, 8, z + 5, mc(theme.roof))
        builder.fill(x + 3, 9, z + 3, x + 4, 9, z + 4, mc(theme.accent))
    else:
        for y, radius in ((5, 4.8), (6, 5.4), (7, 5.0), (8, 3.9), (9, 2.6), (10, 1.2)):
            for dx in range(-2, 10):
                for dz in range(-2, 10):
                    if (dx - 3.5)**2 + (dz - 3.5)**2 <= radius**2:
                        color = theme.accent if (dx + 2 * dz + house_index) % 9 == 0 else theme.roof
                        builder.set(x + dx, y, z + dz, mc(color))


def build_house(builder, x, z, theme, index, job, station):
    builder.fill(x, 0, z, x + 7, 0, z + 7, mc(theme.floor))
    builder.hollow_box(x, 1, z, x + 7, 5, z + 7, mc(theme.wall), fill_spec=AIR)
    builder.fill(x, 5, z, x + 7, 5, z + 7, mc(theme.roof))
    builder.fill(x + 1, 1, z + 1, x + 6, 1, z + 6, AIR)
    for px, pz in ((x, z), (x + 7, z), (x, z + 7), (x + 7, z + 7)):
        builder.fill(px, 1, pz, px, 5, pz, mc(theme.frame))
    for wy in (2, 3):
        for px in (x + 2, x + 5):
            for pz in (z, z + 7):
                builder.set(px, wy, pz, "minecraft:glass_pane")
        for px in (x, x + 7):
            builder.set(px, wy, z + 3, "minecraft:glass_pane")
    door_z = z + 7 if z < 23 else z
    facing = "south" if z < 23 else "north"
    builder.door(x + 3, 1, door_z, mc(theme.door), facing)
    for px in (x + 1, x + 5):
        builder.set(px, 4, door_z, mc(theme.accent))
    builder.bed(x + 2, 1, z + 4, "minecraft:red_bed", "north")
    builder.set(x + 5, 1, z + 4, station)
    builder.lantern(x + 4, 4, z + 4, hanging=True)
    builder.add_villager(x + 4, 1, z + 2, mc(theme.villager), mc(job))
    build_roof(builder, x, z, theme, index)


def build_civic_tower(builder, theme):
    # A walk-through belvedere on the central crossroad with a climbable lookout.
    cx, cz = 23, 23
    for x in (19, 27):
        for z in (19, 27):
            builder.fill(x, 1, z, x, 13, z, mc(theme.frame))
    builder.fill(19, 10, 19, 27, 10, 27, mc(theme.floor))
    for y in range(1, 11):
        builder.set(27, y, 20, mc(theme.frame))
        builder.set(26, y, 20, ("minecraft:ladder", {"facing": "west", "waterlogged": "false"}))
    fence = {"tall_gable": "bamboo_fence", "hip": "mangrove_fence",
             "terrace": "acacia_fence", "double_eave": "cherry_fence",
             "cap": "oak_fence", "snow_gable": "spruce_fence"}[theme.profile]
    for edge in range(19, 28):
        for x, z in ((edge, 19), (edge, 27), (19, edge), (27, edge)):
            if (x, z) not in ((19, 19), (19, 27), (27, 19), (27, 27)):
                builder.set(x, 11, z, mc(fence))
    # Use each village's established roof profile above the central lookout.
    roof = V4StructureBuilder(47, 24, 47, fill_block="")
    build_roof(roof, 19, 19, theme, 0)
    for (x, y, z), (block, properties) in roof.grid.items():
        builder.set(x, y + 9, z, (block, dict(properties)))
    for x, z in ((19, 19), (19, 27), (27, 19), (27, 27)):
        builder.set(x, 14, z, mc(theme.frame))
    builder.set(cx, 1, cz, ("minecraft:bell", {"attachment": "floor", "facing": "north", "powered": "false"}))
    builder.chest(22, 1, 21, "north", LOOT)


def build_side_garden(builder, x, z, theme):
    builder.fill(x, 0, z, x + 8, 0, z + 6, mc(theme.floor))
    for dx in (1, 7):
        for dz in (1, 5):
            builder.fill(x + dx, 1, z + dz, x + dx, 3, z + dz, mc(theme.frame))
            builder.lantern(x + dx, 4, z + dz)
    for dx in range(2, 7):
        for dz in (1, 5):
            builder.set(x + dx, 1, z + dz, mc(theme.accent))
    for dx in (0, 8):
        for dz in (0, 6):
            builder.set(x + dx, 1, z + dz, mc(theme.frame))


def build_village(name, theme):
    builder = V4StructureBuilder(47, 24, 47, fill_block="minecraft:structure_void")
    # The crossroad runs edge to edge and broad courtyards connect every doorstep.
    builder.fill(21, 0, 0, 25, 0, 46, mc(theme.path))
    builder.fill(0, 0, 21, 46, 0, 25, mc(theme.path))
    builder.fill(3, 0, 12, 43, 0, 34, mc(theme.path))
    builder.fill(15, 0, 15, 31, 0, 31, mc(theme.floor))
    for index, (x, z, job, station) in enumerate((
        (5, 5, "farmer", "minecraft:composter"),
        (34, 5, "librarian", ("minecraft:lectern", {"facing": "west", "powered": "false", "has_book": "false"})),
        (5, 34, "weaponsmith", "minecraft:grindstone"),
        (34, 34, "cartographer", "minecraft:cartography_table"),
    )):
        build_house(builder, x, z, theme, index, job, station)
    for x, z in ((4, 14), (34, 14), (4, 26), (34, 26)):
        build_side_garden(builder, x, z, theme)
    build_civic_tower(builder, theme)
    for x, z in ((15, 15), (31, 15), (15, 31), (31, 31)):
        builder.set(x, 1, z, mc(theme.frame))
        builder.lantern(x, 2, z)
    builder.add_sentinel(26, 1, 24)
    builder.add_golem(17, 1, 23)

    # Explicitly clear traffic space above the roads without clearing unused terrain.
    for (x, y, z), (kind, _) in list(builder.grid.items()):
        if y == 0 and kind != "minecraft:structure_void":
            for level in (1, 2):
                if builder.grid[x, level, z][0] == "minecraft:structure_void":
                    builder.set(x, level, z, AIR)

    for index, entity in enumerate(builder.entities):
        value = uuid5(NAMESPACE_URL, f"canopycavern:{name}/hillside_village/{index}").bytes
        entity["nbt"]["UUID"] = v3.nbt_int_array(
            [int.from_bytes(value[i:i + 4], "big", signed=True) for i in range(0, 16, 4)]
        )
    builder.validate(name)
    return builder


if __name__ == "__main__":
    for name, theme in THEMES.items():
        build_village(name, theme).save(f"{name}/hillside_village.nbt")
