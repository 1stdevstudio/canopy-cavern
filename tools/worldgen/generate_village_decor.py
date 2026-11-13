"""Redesign village decor while preserving vanilla pool weights and connectors."""

import argparse
import json
import os
from pathlib import Path
from zipfile import ZipFile

import generate_v03_structures as nbt

THEMES = ("plains", "desert", "savanna", "snowy", "taiga")
MINECRAFT_JAR = Path(os.environ.get(
    "MINECRAFT_JAR", str(Path.home() / ".gradle/caches/fabric-loom/26.3/minecraft-common.jar")
))
ROOT = "vanilla_revamp"
SPRUCE = "minecraft:spruce_planks"
SPRUCE_LOG = ("minecraft:stripped_spruce_log", {"axis": "y"})
SPRUCE_FENCE = "minecraft:spruce_fence"
COBBLE = "minecraft:cobblestone"
MOSSY = "minecraft:mossy_cobblestone"
STONE_BRICKS = "minecraft:stone_bricks"
CAMPFIRE = ("minecraft:campfire", {
    "facing": "north", "lit": "true", "signal_fire": "false", "waterlogged": "false",
})


def piece(size, anchor, foundation):
    builder = nbt.StructureBuilder(*size, fill_block=None)
    builder.jigsaw(*anchor, "down_south", "minecraft:bottom", "minecraft:bottom",
                   "minecraft:empty", foundation, "rollable")
    return builder


def plains_lamp():
    builder = piece((3, 6, 3), (1, 0, 1), STONE_BRICKS)
    builder.set(1, 1, 1, ("minecraft:stripped_oak_log", {"axis": "y"}))
    builder.set(1, 2, 1, "minecraft:oak_fence")
    builder.set(1, 3, 1, ("minecraft:stripped_oak_log", {"axis": "y"}))
    builder.set(1, 4, 1, "minecraft:oak_planks")
    builder.slab(1, 5, 1, "minecraft:oak_slab")
    for x, z, facing in ((0, 1, "west"), (2, 1, "east")):
        builder.set(x, 3, z, ("minecraft:wall_torch", {"facing": facing}))
        builder.stairs(x, 4, z, "minecraft:oak_stairs", facing)
    return builder


def desert_lamp():
    builder = piece((1, 5, 1), (0, 0, 0), "minecraft:cut_sandstone")
    builder.set(0, 1, 0, "minecraft:chiseled_sandstone")
    builder.set(0, 2, 0, "minecraft:sandstone_wall")
    builder.set(0, 3, 0, "minecraft:smooth_sandstone")
    builder.set(0, 4, 0, "minecraft:torch")
    return builder


def savanna_lamp():
    builder = piece((1, 5, 1), (0, 0, 0), "minecraft:orange_terracotta")
    builder.set(0, 1, 0, ("minecraft:stripped_acacia_log", {"axis": "y"}))
    builder.set(0, 2, 0, "minecraft:acacia_fence")
    builder.set(0, 3, 0, "minecraft:acacia_planks")
    builder.set(0, 4, 0, "minecraft:torch")
    return builder


def snowy_lamp(size, anchor, lights):
    x, _, z = anchor
    builder = piece(size, anchor, "minecraft:polished_andesite")
    builder.set(x, 1, z, SPRUCE_LOG)
    builder.set(x, 2, z, SPRUCE_FENCE)
    builder.set(x, 3, z, SPRUCE_LOG)
    builder.set(x, 4, z, SPRUCE)
    builder.slab(x, 5, z, "minecraft:spruce_slab")
    for dx, dz, facing in lights:
        builder.set(x + dx, 4, z + dz, SPRUCE)
        builder.lantern(x + dx, 3, z + dz, hanging=True)
    return builder


def taiga_lamp():
    builder = piece((1, 5, 1), (0, 0, 0), MOSSY)
    builder.set(0, 1, 0, "minecraft:mossy_cobblestone_wall")
    builder.set(0, 2, 0, SPRUCE_LOG)
    builder.set(0, 3, 0, "minecraft:polished_andesite")
    builder.set(0, 4, 0, "minecraft:torch")
    return builder


def trough():
    builder = piece((3, 3, 6), (1, 1, 3), "minecraft:structure_void")
    builder.fill(1, 0, 1, 1, 0, 4, SPRUCE)
    builder.set(1, 1, 2, ("minecraft:water_cauldron", {"level": "2"}))
    builder.set(1, 1, 4, ("minecraft:water_cauldron", {"level": "3"}))
    builder.stairs(1, 1, 1, "minecraft:spruce_stairs", "south")
    return builder


def corner_bench():
    builder = piece((2, 3, 3), (1, 0, 1), MOSSY)
    builder.set(1, 0, 2, COBBLE)
    builder.set(0, 0, 2, MOSSY)
    builder.stairs(1, 1, 1, "minecraft:spruce_stairs", "south")
    builder.stairs(1, 1, 2, "minecraft:spruce_stairs", "south", shape="inner_left")
    builder.stairs(0, 1, 2, "minecraft:spruce_stairs", "east")
    return builder


def waystone():
    builder = piece((1, 4, 2), (0, 0, 0), MOSSY)
    builder.set(0, 1, 0, "minecraft:chiseled_stone_bricks")
    builder.set(0, 2, 0, "minecraft:mossy_cobblestone_wall")
    builder.slab(0, 3, 0, "minecraft:stone_brick_slab")
    builder.stairs(0, 0, 1, "minecraft:mossy_cobblestone_stairs", "north")
    return builder


def rest_seat():
    builder = piece((1, 3, 2), (0, 0, 0), COBBLE)
    builder.set(0, 0, 1, MOSSY)
    builder.stairs(0, 1, 0, "minecraft:spruce_stairs", "north")
    builder.stairs(0, 1, 1, "minecraft:spruce_stairs", "north")
    return builder


def brazier():
    builder = piece((1, 2, 1), (0, 0, 0), "minecraft:polished_andesite")
    builder.set(0, 1, 0, CAMPFIRE)
    return builder


def sheltered_hearth():
    builder = piece((3, 3, 3), (1, 0, 1), "minecraft:hay_block")
    builder.set(1, 1, 1, CAMPFIRE)
    for x, z in ((1, 0), (0, 1), (2, 1), (1, 2)):
        builder.set(x, 0, z, MOSSY)
        builder.set(x, 1, z, "minecraft:mossy_cobblestone_wall")
    return builder


def build_pieces():
    left = (-1, 0, "west")
    right = (1, 0, "east")
    lamps = {
        "plains/plains_lamp_1": plains_lamp(),
        "desert/desert_lamp_1": desert_lamp(),
        "savanna/savanna_lamp_post_01": savanna_lamp(),
        "snowy/snowy_lamp_post_01": snowy_lamp((3, 6, 1), (1, 0, 0), (left, right)),
        "snowy/snowy_lamp_post_02": snowy_lamp((2, 6, 1), (1, 0, 0), (left,)),
        "snowy/snowy_lamp_post_03": snowy_lamp(
            (3, 6, 3), (1, 0, 1), (left, right, (0, -1, "north"), (0, 1, "south"))
        ),
        "taiga/taiga_lamp_post_1": taiga_lamp(),
        "taiga/taiga_decoration_1": trough(),
        "taiga/taiga_decoration_2": corner_bench(),
        "taiga/taiga_decoration_3": waystone(),
        "taiga/taiga_decoration_4": rest_seat(),
        "taiga/taiga_decoration_5": brazier(),
        "taiga/taiga_decoration_6": sheltered_hearth(),
    }
    return {f"{ROOT}/{theme}/decor/{name}.nbt": builder
            for key, builder in lamps.items() for theme, name in (key.split("/"),)}


def generate(minecraft_jar):
    pieces = build_pieces()
    with ZipFile(minecraft_jar) as vanilla:
        for theme in THEMES:
            for variant in ("", "zombie/"):
                rel = f"minecraft/worldgen/template_pool/village/{theme}/{variant}decor.json"
                pool = json.loads(vanilla.read("data/" + rel))
                for entry in pool["elements"]:
                    element = entry["element"]
                    if "location" in element:
                        name = element["location"].split("/")[-1]
                        path = f"{ROOT}/{theme}/decor/{name}"
                        if path + ".nbt" not in pieces:
                            raise ValueError(f"Missing redesign for {element['location']}")
                        element["location"] = "canopycavern:" + path
                dest = nbt.DATA.parent / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(json.dumps(pool, indent=2) + "\n")
    for name, builder in pieces.items():
        builder.save(name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--minecraft-jar", type=Path, default=MINECRAFT_JAR)
    generate(parser.parse_args().minecraft_jar)
