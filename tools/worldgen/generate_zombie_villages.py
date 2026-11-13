"""Generate modular ruined vanilla village centers and houses for five themes."""

import json
from zipfile import ZipFile

from generate_v04_ocean_and_villages import MINECRAFT_DATA, THEMES, VANILLA_JAR, V4StructureBuilder, write_ns_json

AIR = "minecraft:air"
VOID = "minecraft:structure_void"
ROLES = ("collapsed_cottage", "ruined_workshop", "abandoned_longhouse")


def zombie_pool(theme, kind):
    return f"minecraft:village/{theme}/zombie/{kind}"


def ruin_piece(builder, start_x, start_z, end_x, end_z, height, collapse, palette):
    builder.fill(start_x, 0, start_z, end_x, 0, end_z, palette["floor"])
    for x in range(start_x, end_x + 1):
        for z in range(start_z, end_z + 1):
            edge = x in (start_x, end_x) or z in (start_z, end_z)
            for y in range(1, height + 1):
                fallen = abs(x - collapse[0]) + abs(z - collapse[1]) <= y - 1
                stone = palette["plinth_alt"] if (x + y + z) % 4 == 0 else palette["plinth"]
                wall = stone if y <= 2 else palette["wall"]
                builder.set(x, y, z, wall if edge and not fallen else AIR)
    for step in range((end_x - start_x + 2) // 2):
        left, right = start_x + step, end_x - step
        y = height + step
        for x, facing in ((left, "east"), (right, "west")):
            for z in range(start_z, end_z + 1):
                if abs(x - collapse[0]) + abs(z - collapse[1]) > 3:
                    builder.stairs(x, y, z, palette["stair"], facing)


def build_cottage(theme, palette, index):
    builder = V4StructureBuilder(9, 12, 12, fill_block=VOID)
    back = (9, 10, 11)[index]
    collapse = ((7, 8), (1, 9), (7, 4))[index]
    ruin_piece(builder, 1, 2, 7, back, 4 + (index % 2), collapse, palette)
    builder.fill(3, 0, 0, 5, 0, 1, palette["path"])
    builder.fill(3, 1, 0, 5, 2, 1, AIR)
    builder.fill(4, 1, 2, 4, 2, 2, AIR)
    builder.set(2, 2, 4, "minecraft:cobweb")
    builder.set(6, 1, back - 1, palette["flower"])
    builder.set(6, 1, 4, ("minecraft:barrel", {"facing": "west", "open": "false"}))
    builder.jigsaw(4, 1, 0, "north_up", "minecraft:building_entrance", "minecraft:building_entrance",
                   "minecraft:empty", VOID)
    builder.jigsaw(4, 0, 4, "up_north", "minecraft:bottom", "minecraft:bottom",
                   zombie_pool(theme, "villagers"), palette["floor"], "rollable")
    builder.validate(f"{theme} {ROLES[index]}")
    return builder


def build_plaza(theme, palette):
    builder = V4StructureBuilder(15, 13, 15, fill_block=VOID)
    builder.fill(1, 0, 1, 13, 0, 13, palette["path"])
    builder.fill(1, 1, 1, 13, 2, 13, AIR)
    builder.fill(6, 0, 0, 8, 0, 14, palette["path"])
    builder.fill(0, 0, 6, 14, 0, 8, palette["path"])
    for (x, z), height in zip(((5, 5), (9, 5), (5, 9), (9, 9)), (11, 8, 7, 3)):
        for y in range(1, height + 1):
            stone = palette["plinth_alt"] if y % 3 == 0 else palette["plinth"]
            builder.set(x, y, z, stone)
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            builder.set(x + dx, 1, z + dz, palette["plinth_alt"])
    for x in range(5, 10):
        builder.set(x, 5, 5, palette["pillar"])
        if x <= 7:
            builder.stairs(x, 9 + (x - 5) // 2, 5, palette["stair"], "east")
    builder.set(7, 4, 5, ("minecraft:bell", {"attachment": "ceiling", "facing": "north", "powered": "false"}))
    for x, z in ((2, 2), (12, 2), (2, 12), (12, 12)):
        builder.set(x, 1, z, palette["plinth_alt"])
        builder.set(x, 2, z, "minecraft:cobweb")
    for x, z, direction in ((0, 7, "west"), (14, 7, "east"), (7, 0, "north"), (7, 14, "south")):
        builder.jigsaw(x, 1, z, direction + "_up", "minecraft:street", "minecraft:street",
                       zombie_pool(theme, "streets"), VOID)
    for x, z in ((3, 6), (11, 8)):
        builder.jigsaw(x, 0, z, "up_north", "minecraft:bottom", "minecraft:bottom",
                       zombie_pool(theme, "villagers"), palette["path"], "rollable")
    builder.validate(f"{theme} ruined zombie plaza")
    return builder


def replacement(theme, role, weight, processor):
    return {"element": {"element_type": "minecraft:single_pool_element",
                        "location": f"canopycavern:vanilla_revamp/{theme}/zombie/{role}",
                        "processors": processor,
                        "projection": "rigid"},
            "weight": weight}


def update_pools(theme, vanilla):
    prefix = "worldgen/template_pool/village"
    plaza_path = f"{prefix}/{theme}/town_centers.json"
    houses_path = f"{prefix}/{theme}/zombie/houses.json"
    original = json.loads(vanilla.read(f"data/minecraft/{plaza_path}"))
    current = json.loads((MINECRAFT_DATA / plaza_path).read_text())
    is_zombie = lambda row: "/zombie/" in row["element"].get("location", "")
    rare_weight = sum(row["weight"] for row in original["elements"] if is_zombie(row))
    processor = f"minecraft:zombie_{theme}"
    current["elements"] = [row for row in current["elements"] if not is_zombie(row)]
    current["elements"].append(replacement(theme, "ruined_plaza", rare_weight, processor))
    write_ns_json(MINECRAFT_DATA, plaza_path, current)

    original_houses = json.loads(vanilla.read(f"data/minecraft/{houses_path}"))
    empty = [row for row in original_houses["elements"]
             if row["element"]["element_type"] == "minecraft:empty_pool_element"]
    weight = sum(row["weight"] for row in original_houses["elements"] if row not in empty)
    base, remainder = divmod(weight, len(ROLES))
    houses = [replacement(theme, role, base + int(i < remainder), processor)
              for i, role in enumerate(ROLES)]
    write_ns_json(MINECRAFT_DATA, houses_path, {"elements": houses + empty, "fallback": original_houses["fallback"]})


if __name__ == "__main__":
    with ZipFile(VANILLA_JAR) as vanilla:
        for theme, palette in THEMES.items():
            folder = f"vanilla_revamp/{theme}/zombie"
            build_plaza(theme, palette).save(f"{folder}/ruined_plaza.nbt")
            for index, role in enumerate(ROLES):
                build_cottage(theme, palette, index).save(f"{folder}/{role}.nbt")
            update_pools(theme, vanilla)
