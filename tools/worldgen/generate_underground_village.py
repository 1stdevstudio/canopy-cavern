"""Generate the Underground Hollow Village cavern borough template."""

import argparse
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from generate_v04_ocean_and_villages import V4StructureBuilder, v3

ASSET = "underground_hollow_village/cavern_borough.nbt"
SIZE = 47
CENTER = SIZE // 2
AIR = "minecraft:air"
STONE = "minecraft:deepslate_bricks"
TRIM = "minecraft:polished_deepslate"
FLOOR = "minecraft:deepslate_tiles"
COPPER = "minecraft:oxidized_cut_copper"
SUPPLY = "canopycavern:chests/village_supply"
TREASURY = "canopycavern:chests/underground_village_treasury"


NATURAL_STONE = (
    "minecraft:deepslate", "minecraft:tuff", "minecraft:cobbled_deepslate",
    "minecraft:deepslate", "minecraft:deepslate", "minecraft:deepslate",
)


def cavern_field(x, y, z):
    # The union of unequal chambers shapes irregular roof and alcoves.
    chambers = (
        (22, 21, 20, 18, 20),
        (12, 13, 10, 12, 12),
        (33, 13, 11, 11, 10),
        (13, 33, 10, 12, 10),
        (34, 34, 10, 11, 9),
    )
    ripple = ((x * 19 + z * 11 + x * z * 3) % 23 - 11) / 420
    return min(
        ((x - cx) / rx)**2 + ((z - cz) / rz)**2 + ((y - 1) / ry)**2
        for cx, cz, rx, ry, rz in chambers
    ) + ripple


def build_cavern(hall):
    for x in range(SIZE):
        for z in range(SIZE):
            field = cavern_field(x, 1, z)
            if field <= 1.19:
                paved = abs(x - CENTER) <= 2 or abs(z - CENTER) <= 2
                hall.set(x, 0, z, TRIM if paved else NATURAL_STONE[(x + z * 3) % len(NATURAL_STONE)])
            for y in range(1, hall.sy):
                field = cavern_field(x, y, z)
                if field <= 1:
                    hall.set(x, y, z, AIR)
                elif field <= 1.19:
                    stone = NATURAL_STONE[(x * 7 + z * 3 + y * 11) % len(NATURAL_STONE)]
                    if (x * 3 + y * 7 + z * 11) % 103 == 0:
                        stone = "minecraft:deepslate_copper_ore"
                    hall.set(x, y, z, stone)

    # Floor-level tunnels curve before meeting the chamber, with naturally stepped crowns.
    for offset in range(-CENTER, CENTER + 1):
        bend = (1 if offset < 0 else -1) * max(0, min(abs(offset) - 12, 23 - abs(offset)))
        for side in range(-2, 3):
            cross = CENTER + bend + side
            along = CENTER + offset
            for px, pz in ((cross, along), (along, cross)):
                hall.set(px, 0, pz, TRIM)
                height = 3 if abs(side) == 2 else 4
                for y in range(1, height + 1):
                    hall.set(px, y, pz, AIR)
                if abs(offset) >= 16:
                    hall.set(px, height + 1, pz, NATURAL_STONE[(px + pz) % len(NATURAL_STONE)])


def build_quarters(hall, x, z, job, station):
    # An arched stone alcove rather than a cuboid house. Taper each shoulder into the crown.
    for dx in range(7):
        for dz in range(7):
            corner = dx in (0, 6) and dz in (0, 6)
            if corner:
                continue
            px, pz = x + dx, z + dz
            wall = dx in (0, 6) or dz in (0, 6) or (dx, dz) in ((1, 1), (1, 5), (5, 1), (5, 5))
            peak = 7 - abs(dx - 3) // 2 - int(dz in (0, 6))
            hall.set(px, 0, pz, FLOOR)
            for y in range(1, peak):
                rock = STONE if (px + y + pz) % 3 == 0 else "minecraft:tuff_bricks"
                hall.set(px, y, pz, rock if wall else AIR)
            hall.set(px, peak, pz, TRIM)
    door_z = z + 6 if z < CENTER else z
    facing = "south" if z < CENTER else "north"
    hall.door(x + 3, 1, door_z, "minecraft:dark_oak_door", facing)
    for px in (x + 1, x + 5):
        hall.set(px, 3, door_z, "minecraft:cyan_stained_glass")
    hall.set(x + 3, 4, door_z, COPPER)
    hall.bed(x + 2, 1, z + 2, "minecraft:blue_bed", "south")
    hall.set(x + 4, 1, z + 2, station)
    hall.lantern(x + 3, 6, z + 3, hanging=True)
    hall.add_villager(x + 3, 1, z + 3, "minecraft:taiga", f"minecraft:{job}")


def build_underground_village() -> V4StructureBuilder:
    hall = V4StructureBuilder(SIZE, 23, SIZE, fill_block="minecraft:structure_void")
    build_cavern(hall)

    for x, z, job, station in (
        (9, 10, "librarian", ("minecraft:lectern", {"facing": "west", "has_book": "false", "powered": "false"})),
        (30, 11, "farmer", "minecraft:composter"),
        (10, 30, "cartographer", "minecraft:cartography_table"),
        (30, 31, "toolsmith", "minecraft:smithing_table"),
    ):
        build_quarters(hall, x, z, job, station)

    # Crystal outcrops climb at different angles. Leave the market's central crossing open.
    for x, z, height, lean_x, lean_z in (
        (17, 18, 9, 1, 0), (29, 17, 12, 0, 1), (17, 28, 6, 0, -1), (30, 27, 10, -1, 0),
    ):
        for y in range(1, height + 1):
            drift = (y - 1) // 3
            px, pz = x + drift * lean_x, z + drift * lean_z
            mineral = "minecraft:amethyst_block" if y % 4 in (0, 1) else "minecraft:calcite"
            hall.set(px, y, pz, mineral)
            if y < height:
                hall.set(px + lean_x, y, pz + lean_z, mineral)
        hall.set(px, height + 1, pz, "minecraft:shroomlight")
        for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            hall.set(x + dx, 1, z + dz, "minecraft:tuff")

    hall.set(CENTER, 1, CENTER, ("minecraft:bell", {"attachment": "floor", "facing": "north", "powered": "false"}))
    for x, z, facing, loot in (
        (21, 21, "south", SUPPLY),
        (25, 21, "south", SUPPLY),
        (25, 25, "north", TREASURY),
    ):
        hall.set(x, 0, z, COPPER)
        hall.chest(x, 1, z, facing, loot)
    hall.add_sentinel(23, 1, 26)

    # Preserve exact output regardless of the Python process hash seed.
    for index, entity in enumerate(hall.entities):
        value = uuid5(NAMESPACE_URL, f"canopycavern:{ASSET}/{index}").bytes
        entity["nbt"]["UUID"] = v3.nbt_int_array(
            [int.from_bytes(value[i:i + 4], "big", signed=True) for i in range(0, 16, 4)]
        )
    hall.validate("Underground Hollow Village cavern borough")
    return hall


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", type=Path, default=v3.STRUCT_DIR)
    v3.STRUCT_DIR = parser.parse_args().output
    build_underground_village().save(ASSET)


if __name__ == "__main__":
    main()
