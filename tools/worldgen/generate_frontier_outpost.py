"""Generate the Frontier Pillager Outpost stockade; retain its legacy center template."""

from uuid import NAMESPACE_URL, uuid5

from generate_v04_ocean_and_villages import V4StructureBuilder, v3

ASSET = "frontier_pillager_outpost/stockade.nbt"
LOOT = "canopycavern:chests/frontier_pillager_outpost"
AIR = "minecraft:air"
STONE = "minecraft:cobblestone"
WOOD = "minecraft:dark_oak_planks"
BEAM = "minecraft:stripped_dark_oak_log"
FENCE = "minecraft:dark_oak_fence"
STAIR = "minecraft:dark_oak_stairs"
BARS = "minecraft:iron_bars"


def build_tower(stockade):
    for x in (17, 29):
        for z in (17, 29):
            stockade.fill(x, 1, z, x, 17, z, BEAM)
            stockade.fill(x, 1, z, x, 3, z, "minecraft:mossy_cobblestone")
    for floor, border in ((7, 17), (14, 19)):
        end = 46 - border
        stockade.fill(border, floor, border, end, floor, end, WOOD)
        for i in range(border, end + 1):
            for x, z in ((border, i), (end, i), (i, border), (i, end)):
                if stockade.grid[x, floor + 1, z][0] == AIR:
                    stockade.set(x, floor + 1, z, FENCE)
        # Three fences guard the hatch while the west approach stays open.
        for x, z in ((24, 23), (25, 24), (24, 25)):
            stockade.set(x, floor + 1, z, FENCE)
    for y in range(1, 15):
        stockade.set(25, y, 24, BEAM)
        stockade.set(24, y, 24, ("minecraft:ladder", {"facing": "west", "waterlogged": "false"}))

    # Solid roof trims and forward-facing gables give the watchtower a distinct profile.
    stockade.pitched_gable_roof(18, 28, 17, 18, 28, STAIR, WOOD, "minecraft:dark_oak_slab", WOOD)
    for x in range(19, 28):
        stockade.set(x, 16, 19, BEAM)
        stockade.set(x, 16, 27, BEAM)
    for x, z in ((19, 21), (27, 21), (19, 25), (27, 25)):
        stockade.set(x, 16, z, BEAM)
        stockade.lantern(x, 15, z, hanging=True)
    stockade.chest(22, 15, 20, "south", LOOT)


def build_tent(stockade, x, z, wool, facing):
    stockade.fill(x, 0, z, x + 8, 0, z + 6, WOOD)
    for step in range(4):
        west, east = x + step, x + 8 - step
        y = 2 + step
        for pz in range(z, z + 7):
            stockade.set(west, y, pz, wool)
            stockade.set(east, y, pz, wool)
            if step == 3:
                stockade.set(x + 4, y, pz, wool)
    for px in (x + 1, x + 7):
        stockade.fill(px, 1, z + 1, px, 2, z + 1, BEAM)
        stockade.fill(px, 1, z + 5, px, 2, z + 5, BEAM)
    stockade.chest(x + 2, 1, z + 3, facing, LOOT)


def build_cage(stockade, x, z):
    stockade.fill(x - 2, 0, z - 2, x + 2, 0, z + 2, STONE)
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if max(abs(dx), abs(dz)) == 2:
                block = BEAM if abs(dx) == abs(dz) else BARS
                stockade.fill(x + dx, 1, z + dz, x + dx, 3, z + dz, block)
            stockade.set(x + dx, 4, z + dz, WOOD)
    stockade.add_golem(x, 1, z)


def build_stockade():
    stockade = V4StructureBuilder(47, 24, 47, fill_block="minecraft:structure_void")
    # Cross-path and coarse courtyard. Omit untouched terrain at outer corners.
    for x in range(4, 43):
        for z in range(4, 43):
            if (x - 23)**2 + (z - 23)**2 <= 22**2 or abs(x - 23) <= 3 or abs(z - 23) <= 3:
                ground = "minecraft:gravel" if (x + z) % 5 else "minecraft:coarse_dirt"
                stockade.set(x, 0, z, ground)
                stockade.fill(x, 1, z, x, 3, z, AIR)
    for i in range(8, 39):
        for x, z in ((i, 7), (i, 39), (7, i), (39, i)):
            if abs(i - 23) <= 3:
                continue
            height = 3 + int((i + x + z) % 4 == 0)
            stockade.fill(x, 1, z, x, height, z, BEAM)
            stockade.set(x, 0, z, STONE)
    for x, z in ((8, 8), (38, 8), (8, 38), (38, 38)):
        stockade.fill(x, 1, z, x, 5, z, BEAM)
        stockade.set(x, 0, z, STONE)
        stockade.lantern(x, 6, z)
    for x, z in ((19, 7), (27, 7), (19, 39), (27, 39)):
        stockade.lantern(x, 5, z)
        stockade.set(x, 4, z, BEAM)

    # Explicitly carve habitable air and walkable deck approaches.
    stockade.fill(17, 4, 17, 29, 19, 29, AIR)
    build_tower(stockade)
    build_tent(stockade, 9, 10, "minecraft:gray_wool", "east")
    build_tent(stockade, 30, 31, "minecraft:brown_wool", "east")
    build_cage(stockade, 12, 32)
    for x, z in ((12, 15), (34, 31)):
        stockade.set(x, 1, z, ("minecraft:campfire", {
            "facing": "north", "lit": "false", "signal_fire": "false", "waterlogged": "false",
        }))

    for x, y, z in ((15, 1, 17), (33, 1, 27), (25, 15, 23)):
        stockade.add_entity(x + .5, float(y), z + .5, "minecraft:pillager")
    for index, entity in enumerate(stockade.entities):
        identifier = uuid5(NAMESPACE_URL, f"canopycavern:{ASSET}/{index}").bytes
        entity["nbt"]["UUID"] = v3.nbt_int_array(
            [int.from_bytes(identifier[i:i + 4], "big", signed=True) for i in range(0, 16, 4)]
        )

    stockade.validate("Frontier Pillager Outpost stockade")
    return stockade


if __name__ == "__main__":
    build_stockade().save(ASSET)
