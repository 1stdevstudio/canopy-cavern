"""Generate the ruined Abandoned Mega Village while retaining the legacy center template."""

from uuid import NAMESPACE_URL, uuid5

from generate_v04_ocean_and_villages import V4StructureBuilder, v3

ASSET = "abandoned_mega_village/ruins.nbt"
LOOT = "canopycavern:chests/abandoned_mega_village"
AIR = "minecraft:air"
MOSS = "minecraft:mossy_stone_bricks"
CRACKED = "minecraft:cracked_stone_bricks"
STONE = "minecraft:stone_bricks"
WOOD = "minecraft:dark_oak_planks"


def masonry(x, y, z):
    return (STONE, MOSS, CRACKED, MOSS, STONE)[(x * 11 + y * 3 + z * 7) % 5]


def ruined_hall(ruins, left, front, width, depth, height, collapse):
    right, back = left + width - 1, front + depth - 1
    ruins.fill(left, 0, front, right, 0, back, WOOD)
    for x in range(left, right + 1):
        for z in range(front, back + 1):
            for y in range(1, height + 1):
                outer = x in (left, right) or z in (front, back)
                collapsed = abs(x - collapse[0]) + abs(z - collapse[1]) <= y - 1
                ruins.set(x, y, z, masonry(x, y, z) if outer and not collapsed else AIR)
    # Leave partial gables and rafters. Each damaged roof loses a different portion.
    for slope in range((width + 1) // 2):
        y = height + slope
        west, east = left + slope, right - slope
        for x, direction in ((west, "east"), (east, "west")):
            for z in range(front, back + 1):
                if abs(x - collapse[0]) + abs(z - collapse[1]) > 4:
                    ruins.stairs(x, y, z, "minecraft:dark_oak_stairs", direction)
        for z in (front, back):
            for x in range(west + 1, east):
                if abs(x - collapse[0]) + abs(z - collapse[1]) > 4:
                    ruins.set(x, y, z, masonry(x, y, z))

    door_x = (left + right) // 2
    door_z = back if front < 23 else front
    facing = "south" if front < 23 else "north"
    ruins.door(door_x, 1, door_z, "minecraft:dark_oak_door", facing)
    ruins.set(door_x, 3, door_z, CRACKED)
    ruins.set(left + 1, 2, front + 1, "minecraft:cobweb")
    ruins.set(right - 1, 2, back - 1, "minecraft:cobweb")
    for x in (left, right):
        for z in (front + 2, back - 2):
            ruins.set(x, 2, z, "minecraft:iron_bars")
            ruins.set(x, 3, z, AIR)
    ruins.chest(left + 2, 1, front + 3, "east", LOOT)


def belfry(ruins):
    # Open central landmark: damaged masonry shoulders and fragment of its original roof.
    for x, z, height in ((20, 20, 18), (26, 20, 16), (20, 26, 14), (26, 26, 9)):
        for y in range(1, height + 1):
            ruins.set(x, y, z, masonry(x, y, z))
        for dx, dz in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            ruins.set(x + dx, 1, z + dz, MOSS)
    for x in range(20, 27):
        for y in range(5, 8):
            ruins.set(x, y, 20, masonry(x, y, 20))
    for z in range(20, 27):
        for y in range(6, 8):
            ruins.set(20, y, z, masonry(20, y, z))
    for x in range(20, 25):
        ruins.stairs(x, 16 + (x - 20) // 2, 20, "minecraft:dark_oak_stairs", "east")
    ruins.set(23, 4, 20, ("minecraft:bell", {"attachment": "ceiling", "facing": "north", "powered": "false"}))
    ruins.lantern(21, 4, 20, hanging=True)


def build_ruins():
    ruins = V4StructureBuilder(47, 20, 47, fill_block="minecraft:structure_void")
    # Reclaim some paving as grass and moss while keeping cross streets traversable.
    for x in range(47):
        for z in range(47):
            street = abs(x - 23) <= 3 or abs(z - 23) <= 3
            court = 4 <= x <= 42 and 12 <= z <= 34
            if street or court:
                if street and (x + z) % 4 != 0:
                    surface = "minecraft:gravel"
                elif (x + z) % 3 == 0:
                    surface = "minecraft:moss_block"
                else:
                    surface = "minecraft:coarse_dirt"
                ruins.set(x, 0, z, surface)
                ruins.fill(x, 1, z, x, 2, z, AIR)
    for x, z, width, depth, height, collapse in (
        (5, 5, 11, 10, 6, (14, 5)),
        (31, 6, 10, 9, 5, (39, 14)),
        (5, 32, 10, 10, 5, (5, 41)),
        (32, 32, 9, 11, 6, (38, 33)),
    ):
        ruined_hall(ruins, x, z, width, depth, height, collapse)
    belfry(ruins)

    for x, z, height in ((5, 19, 3), (41, 19, 2), (5, 27, 2), (41, 27, 4)):
        for step in range(4):
            for y in range(1, max(1, height - step) + 1):
                ruins.set(x + step - 2, y, z, masonry(x + step, y, z))
    for x, z in ((17, 18), (29, 17), (16, 30), (29, 30), (8, 23), (36, 24)):
        ruins.set(x, 1, z, "minecraft:mossy_cobblestone")
        ruins.set(x, 2, z, "minecraft:oak_leaves")

    for index, (x, z) in enumerate(((8, 8), (36, 37))):
        identifier = uuid5(NAMESPACE_URL, f"canopycavern:{ASSET}/{index}").bytes
        ruins.add_entity(x + .5, 1., z + .5, "minecraft:zombie_villager", {
            "UUID": v3.nbt_int_array([
                int.from_bytes(identifier[i:i + 4], "big", signed=True) for i in range(0, 16, 4)
            ]),
            "VillagerData": {
                "type": "minecraft:plains", "profession": "minecraft:none", "level": 1,
            },
        })
    ruins.validate("Abandoned Mega Village ruins")
    return ruins


if __name__ == "__main__":
    build_ruins().save(ASSET)
