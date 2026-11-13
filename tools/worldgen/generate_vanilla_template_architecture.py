"""Generate architecture variants for Minecraft 26.3 template-driven structures."""

import argparse
import gzip
import os
import struct
from collections import Counter
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

DEFAULT_JAR = Path.home() / ".gradle/caches/fabric-loom/26.3/minecraft-common.jar"
OUTPUT = Path(__file__).resolve().parents[2] / "src/main/resources/data/minecraft/structure"
PREFIX = "data/minecraft/structure/"
FAMILIES = {
    "end_city": 20, "igloo": 3, "nether_fossils": 14, "ruined_portal": 13,
    "shipwreck": 20, "underwater_ruin": 48, "woodland_mansion": 73,
}
FORMATS = {1: "b", 2: "h", 3: "i", 4: "q", 5: "f", 6: "d"}
AIR = {"minecraft:air", "minecraft:structure_void"}
STEPS = (("west", -1, 0), ("east", 1, 0), ("north", 0, -1), ("south", 0, 1))


@dataclass(frozen=True)
class Tag:
    kind: int
    value: object
    element: int = 0


def decode(compressed):
    stream = BytesIO(gzip.decompress(compressed))

    def number(fmt):
        return struct.unpack(">" + fmt, stream.read(struct.calcsize(fmt)))[0]

    def string():
        return stream.read(number("H")).decode("utf-8")

    def payload(kind):
        if kind in FORMATS:
            return Tag(kind, number(FORMATS[kind]))
        if kind == 7:
            return Tag(kind, stream.read(number("i")))
        if kind == 8:
            return Tag(kind, string())
        if kind == 9:
            element = number("B")
            return Tag(kind, [payload(element) for _ in range(number("i"))], element)
        if kind == 10:
            result = {}
            while (tag := number("B")) != 0:
                name = string()
                result[name] = payload(tag)
            return Tag(kind, result)
        if kind in (11, 12):
            fmt = "i" if kind == 11 else "q"
            return Tag(kind, [number(fmt) for _ in range(number("i"))])
        raise ValueError(f"Unsupported NBT tag {kind}")

    if number("B") != 10 or string():
        raise ValueError("Expected unnamed structure compound")
    result = payload(10).value
    if stream.read(1):
        raise ValueError("Unexpected bytes after structure compound")
    return result


def encode(root):
    stream = BytesIO()

    def number(fmt, value):
        stream.write(struct.pack(">" + fmt, value))

    def string(value):
        value = value.encode("utf-8")
        number("H", len(value))
        stream.write(value)

    def payload(tag):
        kind, value = tag.kind, tag.value
        if kind in FORMATS:
            number(FORMATS[kind], value)
        elif kind == 7:
            number("i", len(value))
            stream.write(value)
        elif kind == 8:
            string(value)
        elif kind == 9:
            number("B", tag.element)
            number("i", len(value))
            for item in value:
                if item.kind != tag.element:
                    raise ValueError("Mismatched NBT list element")
                payload(item)
        elif kind == 10:
            for name, item in value.items():
                number("B", item.kind)
                string(name)
                payload(item)
            number("B", 0)
        elif kind in (11, 12):
            number("i", len(value))
            for item in value:
                number("i" if kind == 11 else "q", item)
        else:
            raise ValueError(f"Unsupported NBT tag {kind}")

    number("B", 10)
    string("")
    payload(Tag(10, root))
    return gzip.compress(stream.getvalue(), mtime=0)


def normalized(tag):
    if isinstance(tag, Tag):
        if tag.kind == 10:
            return normalized(tag.value)
        if tag.kind == 9:
            return [normalized(value) for value in tag.value]
        return tag.value
    if isinstance(tag, dict):
        return {key: normalized(value) for key, value in tag.items()}
    return tag


def template_palettes(root):
    if "palettes" in root:
        return [[entry.value for entry in palette.value] for palette in root["palettes"].value]
    return [[entry.value for entry in root["palette"].value]]


def template_cells(root):
    return {tuple(normalized(block.value["pos"])): block.value for block in root["blocks"].value}


def state(block, **props):
    result = {"id": Tag(8, "minecraft:" + block)}
    if props:
        result["properties"] = Tag(10, {key: Tag(8, value) for key, value in props.items()})
    return result


def stair(block, facing, half="bottom"):
    return state(block, facing=facing, half=half, shape="straight", waterlogged="false")


class Layout:
    def __init__(self, document):
        self.document = document
        self.size = normalized(document["size"])
        self.palette_lists = template_palettes(document)
        self.cells = template_cells(document)
        self.original = self.cells.copy()
        self.original_ids = {pos: self.block(pos) for pos in self.cells}
        self.protected = {pos for pos, cell in self.cells.items() if "nbt" in cell}
        self.changes = 0

    def block(self, pos):
        entry = self.cells.get(pos)
        return self.palette_lists[0][entry["state"].value]["id"].value if entry else "minecraft:air"

    def safe(self, pos, radius=1):
        return all(0 <= coordinate < limit for coordinate, limit in zip(pos, self.size)) and all(
            sum(abs(a - b) for a, b in zip(pos, marker)) > radius for marker in self.protected
        )

    def put(self, pos, palettes):
        if not self.safe(pos, 0):
            raise ValueError(f"Attempt to overwrite protected cell {pos}")
        variants = [palettes] * len(self.palette_lists) if isinstance(palettes, dict) else palettes
        if len(variants) != len(self.palette_lists):
            raise ValueError("Incorrect palette variant count")
        for index in range(len(self.palette_lists[0])):
            if all(palette[index] == replacement for palette, replacement in zip(self.palette_lists, variants)):
                break
        else:
            index = len(self.palette_lists[0])
            for palette, replacement in zip(self.palette_lists, variants):
                palette.append(replacement)
        if self.cells.get(pos, {}).get("state") == Tag(3, index):
            return
        self.cells[pos] = {
            "pos": Tag(9, [Tag(3, value) for value in pos], 3),
            "state": Tag(3, index),
        }
        self.changes += 1

    def finish(self):
        wrapped = [Tag(9, [Tag(10, entry) for entry in palette], 10) for palette in self.palette_lists]
        if "palettes" in self.document:
            self.document["palettes"] = Tag(9, wrapped, 9)
        else:
            self.document["palette"] = wrapped[0]
        self.document["blocks"] = Tag(9, [Tag(10, cell) for cell in self.cells.values()], 10)


def shaped_rim(layout, source_blocks, trim, skip=None):
    """Give exposed solid surfaces a shallow bevel without raising the floor."""
    for (x, y, z), kind in layout.original_ids.items():
        pos = (x, y, z)
        if kind not in source_blocks or not layout.safe(pos, 2) or (skip and skip(pos)):
            continue
        if layout.original_ids.get((x, y + 1, z), "minecraft:air") not in AIR:
            continue
        open_sides = [
            facing for facing, dx, dz in STEPS
            if layout.original_ids.get((x + dx, y, z + dz), "minecraft:air") in AIR
        ]
        if len(open_sides) != 1:
            continue
        facing = open_sides[0]
        back = next((dx, dz) for label, dx, dz in STEPS if label == facing)
        if layout.original_ids.get((x - back[0], y, z - back[1]), "minecraft:air") not in AIR:
            layout.put(pos, stair(trim, facing))


def end_architecture(layout, name):
    if name.endswith("_roof"):
        sx, _, sz = layout.size
        # Taper the roof edges and add low crenels in the unoccupied crown.
        shaped_rim(layout, {"minecraft:purpur_block"}, "purpur_stairs")
        for x in range(3, sx - 2, 3):
            for z in (2, sz - 3):
                pos = (x, 1, z)
                if layout.block(pos) in AIR and layout.safe(pos, 2):
                    layout.put(pos, state("purpur_slab", type="bottom", waterlogged="false"))
    else:
        shaped_rim(layout, {"minecraft:purpur_block"}, "purpur_stairs",
                   lambda p: p[1] == 0 or (p[0] + p[2]) % 3 != 0)
        for pos, block in layout.original_ids.items():
            if block == "minecraft:purpur_pillar" and layout.safe(pos, 2) and (sum(pos) % 3 == 1):
                layout.put(pos, state("end_stone_bricks"))


def igloo_architecture(layout, name):
    if name == "top":
        # Buttress the arch and preserve the vanilla carpet/trapdoor access.
        for x in (1, 5):
            for y, z in ((1, 0), (1, 1), (2, 1)):
                if layout.safe((x, y, z), 1) and layout.block((x, y, z)) in AIR:
                    layout.put((x, y, z), stair("quartz_stairs", "east" if x == 1 else "west"))
        shaped_rim(layout, {"minecraft:snow_block"}, "quartz_stairs", lambda p: p[1] < 3)
    elif name == "middle":
        # The four stone faces around the ladder are a recessed, ribbed shaft.
        for x, y, z in layout.cells.copy():
            if y == 1 and x in (0, 2):
                layout.put((x, y, z), stair("stone_brick_stairs", "west" if x == 0 else "east", "top"))
    else:
        # Recessed masonry on the outside avoids the curing cells and ladder.
        shaped_rim(layout, {"minecraft:stone_bricks", "minecraft:mossy_stone_bricks"},
                   "stone_brick_stairs", lambda p: p[0] not in (0, 6) or p[1] != 3)
        for x in (0, 6):
            for z in (4, 6):
                pos = (x, 1, z)
                if layout.safe(pos, 2) and layout.block(pos) == "minecraft:mossy_stone_bricks":
                    layout.put(pos, state("chiseled_stone_bricks"))


def fossil_architecture(layout, name):
    # Bridge a one-cell break in the ribs, or grow a bent spur at the end.
    sx, sy, sz = layout.size
    candidates = []
    for x in range(sx):
        for y in range(sy):
            for z in range(sz):
                pos = (x, y, z)
                if layout.block(pos) not in AIR:
                    continue
                touching = [
                    axis for axis, dx, dy, dz in (
                        ("x", -1, 0, 0), ("x", 1, 0, 0), ("y", 0, -1, 0),
                        ("y", 0, 1, 0), ("z", 0, 0, -1), ("z", 0, 0, 1),
                    )
                    if layout.block((x + dx, y + dy, z + dz)) == "minecraft:bone_block"
                ]
                if touching:
                    candidates.append((-len(touching), y, x, z, touching[0]))
    for _, y, x, z, axis in sorted(candidates)[: max(2, sy // 2)]:
        layout.put((x, y, z), state("bone_block", axis=axis))


def portal_architecture(layout, name):
    # Only low platform stone is reshaped. Frame, lava, treasure, and jigsaws remain intact.
    masonry = {"minecraft:stone_bricks", "minecraft:cracked_stone_bricks",
               "minecraft:mossy_stone_bricks", "minecraft:chiseled_stone_bricks", "minecraft:stone"}
    shaped_rim(layout, masonry | {"minecraft:netherrack"}, "polished_blackstone_brick_stairs",
               lambda p: p[1] > 2)
    for (x, y, z), kind in layout.original_ids.items():
        if kind in masonry and y <= 2 and layout.safe((x, y, z), 2) and (x + z) % 2 == 0:
            if layout.block((x, y, z)) == kind:
                layout.put((x, y, z), state("polished_blackstone_bricks"))


def wreck_architecture(layout, name):
    # Ribs are installed only on an exposed flank, away from chests and deck ladders.
    sx, sy, sz = layout.size
    for z in range(2, sz - 2, 4):
        for x, facing in ((1, "west"), (sx - 2, "east")):
            dx = -1 if x == 1 else 1
            for y in range(1, min(sy - 1, 8)):
                pos = (x + dx, y, z)
                if not layout.safe(pos, 2) or layout.block(pos) not in AIR:
                    continue
                side = (x, y, z)
                source = layout.original.get(side)
                if not source or not layout.block(side).endswith("_planks"):
                    continue
                variants = []
                for palette in layout.palette_lists:
                    wood = palette[source["state"].value]["id"].value.removeprefix("minecraft:")
                    if not wood.endswith("_planks"):
                        break
                    variants.append(stair(wood.removesuffix("_planks") + "_stairs", facing,
                                          "top" if y % 2 == 0 else "bottom"))
                if len(variants) == len(layout.palette_lists):
                    layout.put(pos, variants)
                    break


def underwater_architecture(layout, name):
    # Cold ruins are three co-located weathering overlays. Reshape only stone already
    # present in each overlay so the original integrity processing remains coherent.
    warm = "warm_" in name
    stone = {"minecraft:cut_sandstone", "minecraft:chiseled_sandstone"} if warm else {
        "minecraft:stone_bricks", "minecraft:cracked_stone_bricks", "minecraft:mossy_stone_bricks",
    }
    shaped_rim(layout, stone | {"minecraft:mossy_cobblestone"},
               "sandstone_stairs" if warm else "prismarine_brick_stairs", lambda p: p[1] < 1)
    for (x, y, z), kind in layout.original_ids.items():
        if kind in stone and y in (2, 3) and layout.safe((x, y, z), 2) and (x + z * 3) % 5 == 0:
            if layout.block((x, y, z)) == kind:
                layout.put((x, y, z), state("chiseled_sandstone" if warm else "prismarine_bricks"))


def mansion_architecture(layout, name):
    sx, sy, sz = layout.size
    if name.startswith("carpet_"):
        # Corridor overlays are one block tall and share a common runner.
        for pos, kind in layout.original_ids.items():
            if kind == "minecraft:red_carpet" and sum(pos) % 2 == 0:
                layout.put(pos, state("purple_carpet"))
        return
    if name == "corridor_floor":
        for (x, y, z), kind in layout.original_ids.items():
            if kind == "minecraft:red_carpet":
                layout.put((x, y, z), state("purple_carpet"))
            elif kind == "minecraft:birch_planks" and x == z:
                layout.put((x, y, z), state("dark_oak_log", axis="z"))
        return
    if name == "roof":
        for x in range(sx):
            for z in range(sz):
                if (x in (1, sx - 2) and z in (1, sz - 2)) or x == sx // 2:
                    layout.put((x, 0, z), state("dark_oak_log", axis="z"))
        return
    if name.startswith(("wall_", "small_wall", "indoors_", "roof_")):
        for (x, y, z), kind in layout.original_ids.items():
            if kind == "minecraft:cobblestone" and y > 0 and (z + y) % 3 == 0:
                layout.put((x, y, z), stair("stone_brick_stairs", "west"))
            if kind == "minecraft:dark_oak_planks" and y >= 3 and z in (1, sz - 2):
                layout.put((x, y, z), state("dark_oak_log", axis="y"))
        if not layout.changes:
            for (x, y, z), kind in layout.original_ids.items():
                if kind.endswith("_stairs") and y >= 1:
                    new = layout.palette_lists[0][layout.cells[x, y, z]["state"].value].copy()
                    new["id"] = Tag(8, "minecraft:dark_oak_stairs" if kind != "minecraft:dark_oak_stairs"
                                    else "minecraft:polished_blackstone_brick_stairs")
                    layout.put((x, y, z), new)
        return

    # Inset low ceiling braces into existing solid cornices. Never add blocks
    # to stairs, secret rooms, paths, spawners, or trap floors.
    shaped_rim(layout, {"minecraft:dark_oak_planks", "minecraft:birch_planks", "minecraft:cobblestone"},
               "dark_oak_stairs", lambda p: p[1] < 3 or (p[0] + p[2]) % 3 != 0)
    for (x, y, z), kind in layout.original_ids.items():
        if kind == "minecraft:dark_oak_planks" and y >= 3 and layout.safe((x, y, z), 2):
            if (x in (0, sx - 1) or z in (0, sz - 1)) and (x + z) % 4 == 1:
                layout.put((x, y, z), state("dark_oak_log", axis="y"))
        if kind == "minecraft:birch_planks" and y == 0 and layout.safe((x, y, z), 2):
            if x in (1, sx - 2) or z in (1, sz - 2):
                layout.put((x, y, z), state("dark_oak_log", axis="z" if x in (1, sx - 2) else "x"))


BUILDERS = {
    "end_city": end_architecture,
    "igloo": igloo_architecture,
    "nether_fossils": fossil_architecture,
    "ruined_portal": portal_architecture,
    "shipwreck": wreck_architecture,
    "underwater_ruin": underwater_architecture,
    "woodland_mansion": mansion_architecture,
}


def generate(vanilla, output):
    counts = Counter()
    for name in sorted(vanilla.namelist()):
        if not name.startswith(PREFIX) or not name.endswith(".nbt"):
            continue
        relative = Path(name[len(PREFIX):])
        family = relative.parts[0]
        if family not in BUILDERS:
            continue
        layout = Layout(decode(vanilla.read(name)))
        BUILDERS[family](layout, relative.stem)
        if not layout.changes:
            # Some tiny overlays contain no exposed free space or eligible rim.
            # Keep their role and use a single characteristic surface accent.
            for pos, kind in layout.original_ids.items():
                if layout.safe(pos, 2) and kind in {
                    "minecraft:birch_planks", "minecraft:dark_oak_planks", "minecraft:purpur_block",
                    "minecraft:end_stone_bricks", "minecraft:stone_bricks", "minecraft:cobblestone",
                    "minecraft:red_carpet", "minecraft:white_carpet", "minecraft:cut_sandstone",
                    "minecraft:cracked_stone_bricks", "minecraft:mossy_stone_bricks",
                }:
                    accent = {
                        "minecraft:birch_planks": "stripped_birch_wood",
                        "minecraft:dark_oak_planks": "stripped_dark_oak_wood",
                        "minecraft:purpur_block": "purpur_pillar",
                        "minecraft:end_stone_bricks": "purpur_block",
                        "minecraft:stone_bricks": "chiseled_stone_bricks",
                        "minecraft:cobblestone": "mossy_cobblestone",
                        "minecraft:red_carpet": "purple_carpet",
                        "minecraft:white_carpet": "gray_carpet",
                        "minecraft:cut_sandstone": "chiseled_sandstone",
                        "minecraft:cracked_stone_bricks": "prismarine_bricks",
                        "minecraft:mossy_stone_bricks": "dark_prismarine",
                    }[kind]
                    layout.put(pos, state(accent))
                    break
        if not layout.changes:
            raise ValueError(f"No safe architecture change for {relative}")
        layout.finish()
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(encode(layout.document))
        counts[family] += 1
    if dict(counts) != FAMILIES:
        raise ValueError(f"Unexpected source family counts: {dict(counts)}")
    return dict(counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jar", type=Path, default=os.environ.get("MINECRAFT_JAR", DEFAULT_JAR))
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    with ZipFile(args.jar) as vanilla:
        print(generate(vanilla, args.output))


if __name__ == "__main__":
    main()
