"""Redesign the vanilla Pillager Outpost tower and all 18 abandoned camp families."""

import argparse
import gzip
import json
import os
import struct
from collections import Counter
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5
from zipfile import ZipFile

from generate_v04_ocean_and_villages import V4StructureBuilder, v3

DATA = v3.DATA.parent
MINECRAFT_JAR = Path(os.environ.get("MINECRAFT_JAR", str(
    Path.home() / ".gradle/caches/fabric-loom/26.3/minecraft-common.jar")))
OUTPOST_ASSET = "vanilla_revamp/pillager_outpost/stepped_watchtower"
AIR = "minecraft:air"
WOOD = "minecraft:dark_oak_planks"
BEAM = "minecraft:stripped_dark_oak_log"
PATH = "minecraft:coarse_dirt"
COMMON_CHEST = "minecraft:chests/abandoned_camp_common_chest"
SECRET_CHEST = "minecraft:chests/abandoned_camp_secret_chest"
BARREL = "minecraft:barrels/abandoned_camp_barrel"


@dataclass(frozen=True)
class Camp:
    wood: str
    canvas: str
    trim: str


BIOMES = {
    "bamboo_jungle": Camp("bamboo", "lime", "yellow"),
    "birch_forest": Camp("birch", "white", "light_gray"),
    "cherry_grove": Camp("cherry", "pink", "white"),
    "dappled_forest": Camp("oak", "orange", "red"),
    "flower_forest": Camp("oak", "magenta", "pink"),
    "forest": Camp("oak", "green", "brown"),
    "meadow": Camp("spruce", "light_blue", "white"),
    "old_growth_birch_forest": Camp("birch", "white", "brown"),
    "old_growth_pine_taiga": Camp("spruce", "brown", "yellow"),
    "old_growth_spruce_taiga": Camp("spruce", "green", "brown"),
    "pale_garden": Camp("pale_oak", "gray", "white"),
    "savanna": Camp("acacia", "orange", "yellow"),
    "snowy_taiga": Camp("spruce", "cyan", "white"),
    "sparse_jungle": Camp("jungle", "lime", "orange"),
    "swamp": Camp("mangrove", "green", "purple"),
    "taiga": Camp("spruce", "brown", "green"),
    "windswept_forest": Camp("oak", "light_gray", "blue"),
    "wooded_badlands": Camp("acacia", "red", "orange"),
}


def read_template(raw):
    """Read vanilla template properties, loot metadata, jigsaw sockets and entities."""
    stream = BytesIO(gzip.decompress(raw))
    formats = {1: ">b", 2: ">h", 3: ">i", 4: ">q", 5: ">f", 6: ">d"}

    def num(fmt):
        return struct.unpack(fmt, stream.read(struct.calcsize(fmt)))[0]

    def string():
        return stream.read(num(">H")).decode("utf-8")

    def payload(tag):
        if tag in formats:
            return num(formats[tag])
        if tag == 7:
            return stream.read(num(">i"))
        if tag == 8:
            return string()
        if tag == 9:
            element, length = num(">B"), num(">i")
            return [payload(element) for _ in range(length)]
        if tag == 10:
            data = {}
            while (child := num(">B")) != 0:
                name = string()
                data[name] = payload(child)
            return data
        if tag in (11, 12):
            return [num(">i" if tag == 11 else ">q") for _ in range(num(">i"))]
        raise ValueError(f"Unexpected NBT tag {tag}")

    if num(">B") != 10 or string():
        raise ValueError("Expected unnamed root NBT")
    return payload(10)


def vanilla_template(vanilla, location):
    return read_template(vanilla.read(f"data/minecraft/structure/{location.split(':', 1)[-1]}.nbt"))


def pool(vanilla, path):
    return json.loads(vanilla.read(f"data/minecraft/worldgen/template_pool/{path}.json"))


def save_pool(output, path, contents):
    target = output / f"minecraft/worldgen/template_pool/{path}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(contents, indent=2) + "\n")


def replacement(asset, weight):
    return {"element": {"element_type": "minecraft:single_pool_element",
                        "location": f"canopycavern:{asset}",
                        "processors": {"processors": []},
                        "projection": "rigid"},
            "weight": weight}


def banner_data():
    with ZipFile(MINECRAFT_JAR) as jar:
        original = vanilla_template(jar, "minecraft:pillager_outpost/watchtower")
    banner = next(block["nbt"] for block in original["blocks"]
                  if block.get("nbt", {}).get("id") == "minecraft:banner")
    return {**banner, "patterns": v3.nbt_list(v3.TAG_COMPOUND, banner["patterns"])}


def build_tower():
    tower = V4StructureBuilder(15, 24, 15, fill_block=None)
    tower.fill(1, 0, 1, 13, 0, 13, "minecraft:cobblestone")
    tower.fill(1, 1, 1, 13, 20, 13, AIR)
    for x in (2, 12):
        for z in (2, 12):
            tower.fill(x, 1, z, x, 16, z, BEAM)
            tower.fill(x, 1, z, x, 3, z, "minecraft:mossy_cobblestone")
    for y, inset in ((7, 1), (14, 2)):
        edge = 14 - inset
        tower.fill(inset, y, inset, edge, y, edge, WOOD)
        for index in range(inset, edge + 1):
            for x, z in ((inset, index), (edge, index), (index, inset), (index, edge)):
                if tower.grid[x, y + 1, z][0] == AIR:
                    tower.set(x, y + 1, z, "minecraft:dark_oak_fence")
        for x, z in ((8, 6), (8, 8)):
            tower.set(x, y + 1, z, "minecraft:dark_oak_fence")
    for y in range(1, 15):
        tower.set(9, y, 7, BEAM)
        tower.set(8, y, 7, ("minecraft:ladder", {"facing": "west", "waterlogged": "false"}))
    tower.set(9, 15, 7, "minecraft:dark_oak_fence")
    tower.pitched_gable_roof(1, 13, 17, 2, 12, "minecraft:dark_oak_stairs",
                            WOOD, "minecraft:dark_oak_slab", WOOD)
    banner = banner_data()
    for x in (4, 10):
        for z in (2, 12):
            tower.set(x, 13, z, BEAM)
            tower.set(x, 13, 1 if z == 2 else 13, ("minecraft:white_wall_banner", {
                "facing": "north" if z == 2 else "south"}), banner)
    for z in (4, 10):
        for x in (2, 12):
            tower.set(x, 13, z, BEAM)
            tower.set(1 if x == 2 else 13, 13, z, ("minecraft:white_wall_banner", {
                "facing": "west" if x == 2 else "east"}), banner)
    tower.chest(8, 15, 10, "north", "minecraft:chests/pillager_outpost")
    tower.jigsaw(7, 1, 13, "south_up", "minecraft:entrance", "minecraft:entrance",
                 "minecraft:empty", AIR)
    tower.validate("Vanilla Pillager Outpost stepped watchtower")
    return tower


def container(builder, x, y, z, table):
    if table == BARREL:
        builder.set(x, y, z, ("minecraft:barrel", {"facing": "up", "open": "false"}),
                    {"id": "minecraft:barrel", "LootTable": table})
    else:
        builder.chest(x, y, z, "north", table)


def build_tent(biome, theme, index, tree_sockets=(), loot_tables=(BARREL,)):
    builder = V4StructureBuilder(9, 10, 11, fill_block=None)
    plank = f"minecraft:{theme.wood}_planks"
    stair = f"minecraft:{theme.wood}_stairs"
    builder.fill(1, 0, 1, 8, 0, 9, PATH)
    builder.fill(2, 0, 2, 7, 0, 8, plank)
    builder.fill(1, 1, 1, 8, 6, 9, AIR)
    for z in range(2, 9):
        for step in range(3):
            y = 2 + step + index % 2
            cloth = f"minecraft:{theme.trim if z in (2, 8) or step == 2 else theme.canvas}_wool"
            for x in (2 + step, 7 - step):
                builder.set(x, y, z, cloth)
            if step == 0:
                builder.stairs(1, y, z, stair, "east")
                builder.stairs(8, y, z, stair, "west")
    for z in (3, 7):
        for x in (2, 7):
            builder.fill(x, 1, z, x, 1 + index % 2, z, plank)
    for table, (x, z) in zip(loot_tables, ((3, 3), (6, 4), (3, 6), (6, 7))):
        container(builder, x, 1, z, table)
    builder.set(4, 1, 8, "minecraft:crafting_table")
    builder.jigsaw(0, 0, 4, "west_up", "minecraft:connector", "minecraft:end_connector",
                   f"minecraft:abandoned_camp/camp/{biome}", PATH, "rollable")
    sockets = ((1, 1), (1, 3), (1, 6), (1, 9), (8, 1), (8, 3), (8, 6), (8, 9))
    if len(tree_sockets) > len(sockets) or len(loot_tables) > 4:
        raise ValueError(f"Unsupported tent mechanics in {biome}/{index}")
    for (x, z), (state, source) in zip(sockets, tree_sockets):
        builder.set(x, 0, z, (state["id"], state["properties"]), source)
    builder.validate(f"{biome} camp pavilion {index}")
    return builder


def build_campsite(theme, role):
    builder = V4StructureBuilder(9, 8, 9, fill_block=None)
    plank = f"minecraft:{theme.wood}_planks"
    stair = f"minecraft:{theme.wood}_stairs"
    builder.fill(0, 0, 2, 8, 0, 6, PATH)
    builder.fill(0, 1, 2, 8, 4, 6, AIR)
    for x, z in ((1, 2), (1, 6), (6, 2), (6, 6)):
        builder.set(x, 0, z, "minecraft:cobblestone")
        builder.fill(x, 1, z, x, 2, z, plank)
    for x, z, direction in ((1, 3, "east"), (1, 5, "east"), (5, 2, "north"), (5, 6, "south")):
        builder.stairs(x, 1, z, stair, direction)
    builder.set(3, 1, 4, ("minecraft:campfire", {
        "facing": "north", "lit": "false", "signal_fire": "false", "waterlogged": "false"}))
    if role == "secret":
        container(builder, 6, 0, 3, SECRET_CHEST)
        builder.set(6, 1, 3, f"minecraft:{theme.trim}_carpet")
    elif role in ("barrel", "chest"):
        container(builder, 6, 1, 3, BARREL if role == "barrel" else COMMON_CHEST)
    else:
        builder.fill(1, 3, 2, 6, 3, 6, f"minecraft:{theme.canvas}_wool")
        builder.fill(2, 4, 3, 5, 4, 5, f"minecraft:{theme.trim}_wool")
        container(builder, 6, 1, 3, BARREL)
    builder.jigsaw(8, 0, 4, "east_up", "minecraft:end_connector", "minecraft:connector",
                   "minecraft:empty", PATH, "rollable")
    identifier = uuid5(NAMESPACE_URL, f"canopycavern:camp/{theme}/{role}").bytes
    builder.add_entity(5.5, 0.9375, 5.5, "minecraft:cushion", {
        "color": theme.canvas, "block_pos": v3.nbt_int_list([5, 0, 5]),
        "UUID": v3.nbt_int_array([int.from_bytes(identifier[i:i + 4], "big", signed=True)
                                 for i in range(0, 16, 4)]),
    })
    return builder


def build_camp(archive, output, biome, theme):
    root = f"vanilla_revamp/abandoned_camp/{biome}"
    tent_pool = f"abandoned_camp/tent/{biome}"
    original = pool(archive, tent_pool)
    entries = []
    for index, row in enumerate(original["elements"]):
        source = vanilla_template(archive, row["element"]["location"])
        tree_sockets = [(source["palette"][block["state"]], block["nbt"])
                        for block in source["blocks"]
                        if "/trees/" in block.get("nbt", {}).get("pool", "")]
        loot_tables = [block["nbt"]["LootTable"] for block in source["blocks"]
                       if block.get("nbt", {}).get("LootTable")]
        asset = f"{root}/tent_{index + 1}"
        build_tent(biome, theme, index, tree_sockets, loot_tables).save(asset + ".nbt")
        entries.append(replacement(asset, row["weight"]))
    save_pool(output, tent_pool, {**original, "elements": entries})

    camp_pool = f"abandoned_camp/camp/{biome}"
    original = pool(archive, camp_pool)
    weights = Counter()
    for row in original["elements"]:
        path = row["element"]["location"]
        role = next((role for role, marker in (("chest", "default_chest"), ("barrel", "default_barrel"),
                                             ("secret", "default_special")) if marker in path), "rest")
        weights[role] += row["weight"]
    entries = []
    for role, weight in sorted(weights.items()):
        asset = f"{root}/campsite_{role}"
        build_campsite(theme, role).save(asset + ".nbt")
        entries.append(replacement(asset, weight))
    save_pool(output, camp_pool, {**original, "elements": entries})


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("output", type=Path, nargs="?", default=DATA)
    output = cli.parse_args().output
    v3.STRUCT_DIR = output / "canopycavern/structure"
    build_tower().save(OUTPOST_ASSET + ".nbt")
    save_pool(output, "pillager_outpost/towers", {"elements": [replacement(OUTPOST_ASSET, 1)],
                                               "fallback": "minecraft:empty"})
    with ZipFile(MINECRAFT_JAR) as archive:
        for biome, theme in BIOMES.items():
            build_camp(archive, output, biome, theme)


if __name__ == "__main__":
    main()
