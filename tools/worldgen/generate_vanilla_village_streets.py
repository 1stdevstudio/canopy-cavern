"""Build paved village roads from the Minecraft 26.3 terrain-matching layouts."""

import argparse
import gzip
import json
import os
import struct
from collections import Counter
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import generate_v03_structures as nbt

DEFAULT_JAR = Path.home() / ".gradle/caches/fabric-loom/26.3/minecraft-common.jar"
DATA = nbt.DATA.parent
POOL_DIR = Path("village")
AIR = "minecraft:air"
GROUND = {"minecraft:dirt_path", "minecraft:smooth_sandstone"}
BIOMES = {
    # Paving, curb, waypoint marker.
    "plains": ("minecraft:stone_bricks", "minecraft:mossy_cobblestone", "minecraft:stone_brick_wall"),
    "desert": ("minecraft:cut_sandstone", "minecraft:smooth_sandstone", "minecraft:sandstone_wall"),
    "savanna": ("minecraft:terracotta", "minecraft:packed_mud", "minecraft:mud_brick_wall"),
    "snowy": ("minecraft:polished_andesite", "minecraft:andesite", "minecraft:andesite_wall"),
    "taiga": ("minecraft:cobbled_deepslate", "minecraft:mossy_stone_bricks", "minecraft:cobbled_deepslate_wall"),
}


def read_template(data):
    """Read the tag subset used by unpopulated vanilla street templates."""
    stream = BytesIO(gzip.decompress(data))

    def number(kind):
        return struct.unpack(">" + kind, stream.read(struct.calcsize(kind)))[0]

    def string():
        return stream.read(number("H")).decode("utf-8")

    def payload(kind):
        if 1 <= kind <= 6:
            return number(("b", "h", "i", "q", "f", "d")[kind - 1])
        if kind == 8:
            return string()
        if kind == 9:
            element = number("B")
            return [payload(element) for _ in range(number("i"))]
        if kind == 10:
            result = {}
            while (tag := number("B")) != 0:
                name = string()
                result[name] = payload(tag)
            return result
        raise ValueError(f"Unexpected NBT tag in street template: {kind}")

    if number("B") != 10 or string():
        raise ValueError("Expected an unnamed root compound")
    return payload(10)


def surface(template):
    return {
        tuple(block["pos"]): (template["palette"][block["state"]], block.get("nbt"))
        for block in template["blocks"]
    }


def neighbors(x, z):
    return ((x - 1, z), (x + 1, z), (x, z - 1), (x, z + 1))


def pave(template, biome, path):
    if template["entities"] or template["size"][1] != 2 or "palettes" in template:
        raise ValueError(f"Unexpected street layout: {path}")

    builder = nbt.StructureBuilder(*template["size"], fill_block=None)
    states = surface(template)
    paving, curb, marker = BIOMES[biome]
    road = {(x, z) for (x, y, z), (state, _) in states.items() if y == 0 and state["id"] in GROUND}
    connectors = [(x, z) for (x, _, z), (state, _) in states.items() if state["id"] == "minecraft:jigsaw"]

    for (x, y, z), (state, block_nbt) in states.items():
        if y == 0 and (x, z) in road:
            edge = sum(pos in road for pos in neighbors(x, z)) < 4
            builder.set(x, y, z, curb if edge and (x + z) % 4 else paving)
        else:
            builder.set(x, y, z, (state["id"], state.get("properties", {})), block_nbt)

    def is_clear(x, z):
        for y in (0, 1):
            state, block_nbt = states.get((x, y, z), ({"id": AIR}, None))
            if state["id"] != AIR or block_nbt:
                return False
        return True

    # Pull-offs sit beside travel lanes and avoid sockets, farm tiles, and template edges.
    # Each starts with a three-block paved shoulder. The center marker is off the road.
    added = set()
    for x, z in sorted(road):
        for dx, dz in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            bay = [(x + dx - dz * i, z + dz + dx * i) for i in (-1, 0, 1)]
            if not all(0 < px < builder.sx - 1 and 0 < pz < builder.sz - 1 for px, pz in bay):
                continue
            if not all(is_clear(px, pz) for px, pz in bay):
                continue
            if any(abs(px - cx) + abs(pz - cz) < 3 for px, pz in bay for cx, cz in connectors):
                continue
            if any(abs(px - bx) + abs(pz - bz) < 4 for px, pz in bay for bx, bz in added):
                continue
            for index, (px, pz) in enumerate(bay):
                builder.set(px, 0, pz, paving if index == 1 else curb)
            px, pz = bay[1]
            builder.set(px, 1, pz, marker)
            added.update(bay)
            break
        if len(added) >= 6:
            break
    return builder


def collect_pools(vanilla):
    prefix = "data/minecraft/worldgen/template_pool/"
    for name in sorted(vanilla.namelist()):
        if not name.startswith(prefix + "village/") or not name.endswith(("/streets.json", "/terminators.json")):
            continue
        relative = Path(name[len(prefix):])
        if relative.parts[1] in BIOMES:
            yield relative, json.loads(vanilla.read(name))


def save_json(destination, document):
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(document, indent=2) + "\n")


def processor_with_paved_crossings(vanilla, name, biome):
    original = json.loads(vanilla.read(f"data/minecraft/worldgen/processor_list/{name}.json"))
    rules = original["processors"][0]["rules"]
    replacements = [
        {**rule, "input_predicate": {**rule["input_predicate"], "block": material}}
        for rule in rules
        if rule["input_predicate"].get("block") == "minecraft:dirt_path"
        and rule["location_predicate"].get("block") in ("minecraft:water", "minecraft:ice")
        for material in BIOMES[biome][:2]
    ]
    rules[:0] = replacements
    return original


def generate(vanilla, output):
    processed = set()
    counts = Counter()
    previous = nbt.STRUCT_DIR
    nbt.STRUCT_DIR = output / "canopycavern/structure"
    try:
        for relative, pool in collect_pools(vanilla):
            biome = relative.parts[1]
            for entry in pool["elements"]:
                element = entry["element"]
                original_id = element["location"].removeprefix("minecraft:")
                variant = relative.parent.relative_to(POOL_DIR / biome)
                path = Path(f"vanilla_revamp/{biome}/roads") / variant / relative.stem / Path(original_id).name
                if path not in processed:
                    template = read_template(vanilla.read(f"data/minecraft/structure/{original_id}.nbt"))
                    pave(template, biome, path).save(path.as_posix() + ".nbt")
                    processed.add(path)
                    counts[biome] += 1
                element["location"] = "canopycavern:" + path.as_posix()
                if isinstance(element["processors"], str):
                    original = element["processors"].removeprefix("minecraft:")
                    processor = f"village_roads/{biome}"
                    save_json(
                        output / "canopycavern/worldgen/processor_list" / (processor + ".json"),
                        processor_with_paved_crossings(vanilla, original, biome),
                    )
                    element["processors"] = f"canopycavern:{processor}"
            save_json(output / "minecraft/worldgen/template_pool" / relative, pool)
    finally:
        nbt.STRUCT_DIR = previous
    return dict(counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jar", type=Path, default=os.environ.get("MINECRAFT_JAR", DEFAULT_JAR))
    parser.add_argument("--output", type=Path, default=DATA)
    args = parser.parse_args()
    with ZipFile(args.jar) as vanilla:
        print(generate(vanilla, args.output))


if __name__ == "__main__":
    main()
