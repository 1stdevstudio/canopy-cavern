"""Generate the Grotto Outpost's market, passageways, and mining rooms."""

import argparse
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import generate_v03_structures as nbt

ID = "grotto_outpost_town"
AIR = "minecraft:air"
WALL = "minecraft:deepslate_bricks"
RIB = "minecraft:polished_deepslate"
PAVING = "minecraft:cobbled_deepslate"
COPPER = "minecraft:oxidized_cut_copper"
SUPPLY = "canopycavern:chests/village_supply"
STREET = "minecraft:street"
ENTRANCE = "minecraft:building_entrance"
EMPTY = "minecraft:empty"
ROLES = {
    "miners_quarters": ("minecraft:crafting_table", None),
    "deep_forge": ("minecraft:smithing_table", "minecraft:toolsmith"),
    "survey_library": (
        ("minecraft:lectern", {"facing": "west", "has_book": "false", "powered": "false"}),
        "minecraft:librarian",
    ),
    "watch_room": ("minecraft:fletching_table", None),
}


def socket(piece, x, z, facing, name, pool=EMPTY):
    piece.jigsaw(x, 1, z, facing + "_up", name, name, pool, AIR)


def opening(piece, x, z, dx, dz):
    for span in (-1, 0, 1):
        px, pz = x + dx * span, z + dz * span
        piece.set(px, 0, pz, RIB)
        for y in range(1, 4):
            piece.set(px, y, pz, AIR)


def hanging_lamp(piece, x, y, z):
    piece.set(x, y + 1, z, COPPER)
    piece.lantern(x, y, z, hanging=True)


def villager(piece, x, z, profession="minecraft:none"):
    piece.add_entity(x + 0.5, 1.0, z + 0.5, "minecraft:villager", {
        "VillagerData": {"level": 1, "profession": profession, "type": "minecraft:taiga"},
    })


def build_market():
    market = nbt.StructureBuilder(19, 11, 19, fill_block="minecraft:structure_void")
    for x in range(19):
        for z in range(19):
            dx, dz = abs(x - 9), abs(z - 9)
            if dx + dz > 15:
                continue
            radius = max(dx, dz)
            crown = 9 - max(0, radius - 4)
            rim = radius == 9 or dx + dz == 15
            market.set(x, 0, z, RIB if dx <= 1 or dz <= 1 else PAVING)
            for y in range(1, crown + 1):
                market.set(x, y, z, WALL if rim or y == crown else AIR)
            market.set(x, crown + 1, z, "minecraft:deepslate")

    # Keep the plaza crossing open and put storage and displays into the corners.
    for x, z in ((4, 4), (14, 4), (4, 14), (14, 14)):
        market.set(x, 0, z, COPPER)
        market.set(x, 1, z, "minecraft:amethyst_block")
        market.set(x, 2, z, "minecraft:calcite")
        market.set(x, 3, z, "minecraft:amethyst_block")
        hanging_lamp(market, x, 6, z)

    market.set(12, 1, 6, ("minecraft:bell", {"attachment": "floor", "facing": "north", "powered": "false"}))
    market.set(6, 1, 6, "minecraft:cartography_table")
    market.chest(12, 1, 12, "west", SUPPLY)
    market.bed(5, 1, 12, "minecraft:green_bed", "south")
    villager(market, 6, 8, "minecraft:cartographer")
    market.add_entity(12.5, 1.0, 8.5, "canopycavern:village_sentinel")
    market.add_entity(9.5, 1.0, 9.5, "minecraft:iron_golem")

    for x, z, dx, dz, facing in (
        (9, 0, 1, 0, "north"), (9, 18, 1, 0, "south"),
        (0, 9, 0, 1, "west"), (18, 9, 0, 1, "east"),
    ):
        opening(market, x, z, dx, dz)
        socket(market, x, z, facing, STREET, f"canopycavern:{ID}/streets")
    return market


def build_arcade():
    arcade = nbt.StructureBuilder(11, 8, 15, fill_block="minecraft:structure_void")
    for x in range(11):
        for z in range(15):
            crown = 7 - max(0, abs(x - 5) - 2)
            boundary = x in (0, 10) or z in (0, 14)
            rib = z in (2, 7, 12)
            arcade.set(x, 0, z, RIB if 4 <= x <= 6 else PAVING)
            for y in range(1, crown + 1):
                state = AIR
                if boundary or y >= crown - int(rib):
                    state = RIB if rib else WALL
                arcade.set(x, y, z, state)

    for x, z, dx, dz, facing, name, pool in (
        (5, 0, 1, 0, "north", STREET, f"canopycavern:{ID}/streets"),
        (5, 14, 1, 0, "south", STREET, f"canopycavern:{ID}/streets"),
        (0, 5, 0, 1, "west", ENTRANCE, f"canopycavern:{ID}/buildings"),
        (10, 10, 0, 1, "east", ENTRANCE, f"canopycavern:{ID}/buildings"),
    ):
        opening(arcade, x, z, dx, dz)
        socket(arcade, x, z, facing, name, pool)
    hanging_lamp(arcade, 5, 5, 2)
    hanging_lamp(arcade, 5, 5, 12)
    return arcade


def build_room(role):
    station, profession = ROLES[role]
    room = nbt.StructureBuilder(9, 7, 9, fill_block="minecraft:structure_void")
    for x in range(9):
        for z in range(9):
            crown = 6 - abs(x - 4) // 2
            boundary = x in (0, 8) or z in (0, 8)
            room.set(x, 0, z, PAVING if boundary else "minecraft:spruce_planks")
            for y in range(1, crown + 1):
                room.set(x, y, z, (RIB if y == 1 else WALL) if boundary or y == crown else AIR)

    opening(room, 4, 0, 1, 0)
    socket(room, 4, 0, "north", ENTRANCE)
    room.set(6, 1, 5, station)
    room.bed(2, 1, 5, "minecraft:green_bed", "south")
    room.chest(2, 1, 3, "east", SUPPLY)
    hanging_lamp(room, 4, 4, 4)
    if role == "miners_quarters":
        room.set(6, 1, 7, "minecraft:barrel")
        villager(room, 4, 4)
    elif role == "deep_forge":
        room.set(6, 1, 7, ("minecraft:blast_furnace", {"facing": "west", "lit": "false"}))
        room.set(2, 1, 7, ("minecraft:anvil", {"facing": "east"}))
        villager(room, 4, 4, profession)
    elif role == "survey_library":
        room.fill(3, 1, 7, 5, 2, 7, "minecraft:bookshelf")
        villager(room, 4, 4, profession)
    else:
        room.set(6, 1, 7, "minecraft:barrel")
        room.add_entity(4.5, 1.0, 4.5, "canopycavern:village_sentinel")
    return room


def build_survey_exit():
    exit_piece = nbt.StructureBuilder(7, 6, 7, fill_block="minecraft:structure_void")
    for z in range(7):
        width = 3 - int(z >= 4)
        for x in range(3 - width, 4 + width):
            edge = abs(x - 3) == width
            crown = 5 - int(z >= 4)
            exit_piece.set(x, 0, z, RIB)
            for y in range(1, crown + 1):
                exit_piece.set(x, y, z, WALL if edge or y == crown else AIR)
    socket(exit_piece, 3, 0, "north", STREET)
    hanging_lamp(exit_piece, 3, 3, 3)
    return exit_piece


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", type=Path, default=nbt.STRUCT_DIR)
    nbt.STRUCT_DIR = parser.parse_args().output
    pieces = {
        "lantern_market": build_market(),
        "mining_arcade": build_arcade(),
        "survey_exit": build_survey_exit(),
        **{role: build_room(role) for role in ROLES},
    }
    for name, piece in pieces.items():
        for index, entity in enumerate(piece.entities):
            value = uuid5(NAMESPACE_URL, f"canopycavern:{ID}/{name}/{index}").bytes
            entity["nbt"]["UUID"] = nbt.nbt_int_array(
                [int.from_bytes(value[i:i + 4], "big", signed=True) for i in range(0, 16, 4)]
            )
        piece.save(f"{ID}/{name}.nbt")


if __name__ == "__main__":
    main()
