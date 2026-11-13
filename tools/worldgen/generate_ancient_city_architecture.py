"""Add ribbed deepslate architecture to ancient cities without changing connector contracts."""

import argparse
import os
from pathlib import Path
from zipfile import ZipFile

from generate_vanilla_template_architecture import (
    AIR, DEFAULT_JAR, Layout, OUTPUT, PREFIX, STEPS, decode, encode, stair, state,
)

MASONRY = {"minecraft:deepslate", "minecraft:deepslate_bricks",
           "minecraft:deepslate_tiles", "minecraft:cobbled_deepslate",
           "minecraft:polished_deepslate", "minecraft:cracked_deepslate_bricks"}
SENSITIVE = ("sculk", "wool", "reinforced_deepslate", "redstone", "ladder", "piston",
             "repeater", "comparator", "lever", "skull", "head", "soul_fire")


def buttress(layout, x, y, z, facing, dx, dz):
    """Grow a vertical rib on an unused face, capped by stair corbels."""
    root = (x, y, z)
    front = (x + dx, y, z + dz)
    if layout.block(root) not in MASONRY or layout.block(front) not in AIR:
        return False
    # Keep travel space intact: a tall exterior face must continue above and below the rib.
    if any(layout.block((x, y + step, z)) not in MASONRY for step in (-2, -1, 1, 2)):
        return False
    cells = [(front[0], y + step, front[2]) for step in (-1, 0, 1)]
    if any(not layout.safe(cell, 1) or layout.block(cell) not in AIR for cell in cells):
        return False
    # Skip ribs which would hang over an existing path, wool sound shield, or redstone.
    if any(layout.block((front[0], level, front[2])) not in AIR for level in range(y - 4, y - 1)):
        return False
    layout.put(cells[0], stair("deepslate_brick_stairs", facing, "top"))
    layout.put(cells[1], state("chiseled_deepslate"))
    layout.put(cells[2], stair("deepslate_brick_stairs", facing))
    return True


def reshape(layout, relative):
    # Protect sculk sensors/shriekers, silently walkable wool, and the central frame and circuitry.
    layout.protected.update(pos for pos, block in layout.original_ids.items()
                            if any(term in block for term in SENSITIVE))
    # Layout.safe() tests every protected position; trim this set to only nearby calls via lookup.
    protected = layout.protected
    base_safe = layout.safe

    def safe(pos, radius=1):
        if not all(0 <= coordinate < limit for coordinate, limit in zip(pos, layout.size)):
            return False
        x, y, z = pos
        return not any((x + dx, y + dy, z + dz) in protected
                       for dx in range(-radius, radius + 1)
                       for dy in range(-radius, radius + 1)
                       for dz in range(-radius, radius + 1)
                       if abs(dx) + abs(dy) + abs(dz) <= radius)

    layout.safe = safe
    try:
        # Taller originals get ribs on spaced outer faces. Avoid the occupied central vault zone.
        width, _, depth = layout.size
        core = relative.parts[0] == "city_center" and len(relative.parts) == 2
        ribs = 0
        for x, y, z in sorted(layout.original_ids):
            if y < 5 or (x * 3 + z * 5) % 7 or y % 6 != 3:
                continue
            if min(x, width - 1 - x, z, depth - 1 - z) > (4 if not core else 2):
                continue
            for facing, dx, dz in STEPS:
                if buttress(layout, x, y, z, facing, dx, dz):
                    ribs += 1
                    break
            if ribs >= 10:
                break

        # Bevel only crown and rubble edges, so no blocks are raised into walking paths.
        beveled = 0
        for x, y, z in sorted(layout.original_ids):
            pos = (x, y, z)
            if y < 1 or layout.block(pos) not in MASONRY or not safe(pos, 2):
                continue
            if layout.block((x, y + 1, z)) not in AIR or layout.block((x, y - 1, z)) not in MASONRY:
                continue
            open_sides = [(f, dx, dz) for f, dx, dz in STEPS
                          if layout.block((x + dx, y, z + dz)) in AIR
                          and layout.block((x - dx, y, z - dz)) in MASONRY]
            if not open_sides or (x + z) % 2:
                continue
            layout.put(pos, stair("deepslate_tile_stairs", open_sides[0][0]))
            beveled += 1
        if beveled + ribs * 2 < 2:
            for x, y, z in sorted(layout.original_ids):
                pos = (x, y, z)
                if layout.block(pos) not in MASONRY or not safe(pos, 2):
                    continue
                if layout.block((x, y + 1, z)) not in AIR:
                    continue
                open_sides = [facing for facing, dx, dz in STEPS if layout.block((x + dx, y, z + dz)) in AIR]
                if open_sides:
                    layout.put(pos, stair("cobbled_deepslate_stairs", open_sides[0]))
                    beveled += 1
                if beveled + ribs * 2 >= 2:
                    break
        if beveled + ribs * 2 < 2:
            # Top/side shell pieces are often full-thickness overlays with no exposed top.
            # Recess their outside edges with upside-down stair corbels, preserving all joins.
            for x, y, z in sorted(layout.original_ids):
                pos = (x, y, z)
                if layout.block(pos) not in MASONRY or not safe(pos, 0):
                    continue
                open_sides = [facing for facing, dx, dz in STEPS
                              if layout.block((x + dx, y, z + dz)) in AIR]
                if open_sides:
                    layout.put(pos, stair("deepslate_brick_stairs", open_sides[0], "top"))
                    beveled += 1
                if beveled + ribs * 2 >= 6:
                    break
        if beveled + ribs * 2 < 2:
            raise ValueError(f"Not enough safe faces for {relative}")
    finally:
        layout.safe = base_safe


def generate(jar, output):
    count = 0
    for name in sorted(jar.namelist()):
        if not name.startswith(PREFIX + "ancient_city/") or not name.endswith(".nbt"):
            continue
        relative = Path(name[len(PREFIX + "ancient_city/"):])
        layout = Layout(decode(jar.read(name)))
        reshape(layout, relative)
        layout.finish()
        destination = output / "ancient_city" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(encode(layout.document))
        count += 1
    if count != 58:
        raise ValueError(f"Expected 58 Minecraft 26.3 ancient-city pieces, got {count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, nargs="?", default=OUTPUT)
    with ZipFile(Path(os.environ.get("MINECRAFT_JAR", str(DEFAULT_JAR)))) as archive:
        generate(archive, parser.parse_args().output)
