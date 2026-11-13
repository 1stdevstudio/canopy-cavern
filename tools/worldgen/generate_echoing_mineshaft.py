"""Build the new Echoing Mineshaft pieces alongside the original saved-world templates."""

import json
from pathlib import Path

import generate_v03_structures as nbt

FAMILY = "echoing_mineshaft_hub"
LOOT = "canopycavern:chests/echoing_mineshaft"
TUNNELS = f"canopycavern:{FAMILY}/tunnels"
CAPS = f"canopycavern:{FAMILY}/caps"
AIR = "minecraft:air"
DEEPSLATE = "minecraft:deepslate_bricks"
TILES = "minecraft:deepslate_tiles"
WOOD = "minecraft:dark_oak_planks"
LOG = ("minecraft:stripped_dark_oak_log", {"axis": "y"})


def rail(piece, x, z, shape):
    piece.set(x, 1, z, ("minecraft:rail", {"shape": shape, "waterlogged": "false"}))


def portal(piece, x, z, orientation, pool):
    along_x = orientation in {"north_up", "south_up"}
    for offset in (-1, 0, 1):
        for y in range(1, 4):
            piece.set(x + (offset if along_x else 0), y, z + (0 if along_x else offset), AIR)
    piece.jigsaw(x, 2, z, orientation, "canopycavern:shaft", "canopycavern:shaft",
                 pool, AIR, "aligned")


def build_exchange():
    chamber = nbt.StructureBuilder(27, 13, 27, fill_block=None)
    heights = {}
    for x in range(27):
        for z in range(27):
            dx, dz = abs(x - 13), abs(z - 13)
            if max(dx, dz) <= 11 and dx + dz <= 17:
                heights[x, z] = 12 - max(0, (max(dx, dz) - 5) // 2)
            elif min(dx, dz) <= 2:
                heights[x, z] = 5
    for (x, z), ceiling in heights.items():
        wall = any((x + dx, z + dz) not in heights for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        chamber.set(x, 0, z, TILES)
        for y in range(1, ceiling + 1):
            exposed = any(heights.get((x + dx, z + dz), 0) < y
                          for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if wall or exposed or y == ceiling:
                masonry = ("minecraft:tuff", "minecraft:cobbled_deepslate", DEEPSLATE)
                chamber.set(x, y, z, masonry[(x * 3 + y * 7 + z) % len(masonry)])
            else:
                chamber.set(x, y, z, AIR)
    for x, z, orientation in (
        (0, 13, "west_up"), (26, 13, "east_up"),
        (13, 0, "north_up"), (13, 26, "south_up"),
    ):
        portal(chamber, x, z, orientation, TUNNELS)
    for x in (*range(13), *range(17, 27)):
        rail(chamber, x, 13, "east_west")
    for z in (*range(13), *range(17, 27)):
        rail(chamber, 13, z, "north_south")
    rail(chamber, 13, 13, "north_west")
    rail(chamber, 16, 13, "south_east")
    for z in (14, 15):
        rail(chamber, 16, z, "north_south")
    rail(chamber, 16, 16, "north_west")
    for x in (14, 15):
        rail(chamber, x, 16, "east_west")
    rail(chamber, 13, 16, "south_east")

    # Raise the dispatch office above the track and leave two blocks clear over each stair.
    chamber.fill(5, 3, 5, 10, 3, 6, WOOD)
    chamber.fill(5, 3, 4, 10, 3, 4, WOOD)
    chamber.fill(5, 4, 4, 10, 4, 4, "minecraft:dark_oak_fence")
    for x in (5, 10):
        chamber.fill(x, 4, 5, x, 4, 6, "minecraft:dark_oak_fence")
    for x in (6, 9):
        chamber.set(x, 4, 6, "minecraft:dark_oak_fence")
    for x in (7, 8):
        for y, z in ((1, 9), (2, 8), (3, 7)):
            chamber.fill(x, 0, z, x, y - 1, z, WOOD)
            chamber.stairs(x, y, z, "minecraft:dark_oak_stairs", "north")
    chamber.chest(9, 4, 5, "west", LOOT)
    chamber.set(6, 4, 5, "minecraft:cartography_table")
    for x, z in ((5, 5), (10, 5), (5, 21), (21, 5), (21, 21)):
        chamber.fill(x, 1, z, x, heights[x, z] - 1, z, LOG)
    for z in (8, 18):
        for x in (6, 20):
            chamber.set(x, 8, z, WOOD)
            chamber.lantern(x, 7, z, hanging=True)
    for x in range(18, 22):
        chamber.set(x, 0, 19, "minecraft:smooth_basalt")
        chamber.set(x, 1, 20, "minecraft:raw_copper_block" if x < 20 else "minecraft:raw_iron_block")
    chamber.set(20, 1, 18, ("minecraft:blast_furnace", {"facing": "west", "lit": "false"}))
    chamber.chest(18, 1, 18, "west", LOOT)
    return chamber


def build_gallery():
    gallery = nbt.StructureBuilder(13, 7, 7, fill_block=None)
    gallery.hollow_box(0, 0, 0, 12, 6, 6, DEEPSLATE)
    gallery.fill(0, 0, 1, 12, 0, 5, "minecraft:polished_deepslate")
    portal(gallery, 0, 3, "west_up", TUNNELS)
    portal(gallery, 12, 3, "east_up", TUNNELS)
    portal(gallery, 6, 6, "south_up", CAPS)
    for x in range(13):
        rail(gallery, x, 3, "east_west")
    for x in (2, 4, 8, 10):
        gallery.fill(x, 1, 1, x, 4, 1, LOG)
        gallery.fill(x, 1, 5, x, 4, 5, LOG)
        gallery.fill(x, 5, 1, x, 5, 5, WOOD)
        gallery.lantern(x, 4, 3, hanging=True)
    gallery.chest(3, 1, 1, "south", LOOT)
    return gallery


def build_vault():
    vault = nbt.StructureBuilder(9, 8, 9, fill_block=None)
    vault.hollow_box(0, 0, 0, 8, 7, 8, "minecraft:chiseled_deepslate")
    vault.fill(1, 0, 1, 7, 0, 7, TILES)
    portal(vault, 0, 4, "west_up", "minecraft:empty")
    for x in range(1, 8):
        vault.set(x, 6, 1, DEEPSLATE)
        vault.set(x, 6, 7, DEEPSLATE)
    for x in (2, 6):
        vault.fill(x, 1, 1, x, 5, 1, LOG)
        vault.fill(x, 1, 7, x, 5, 7, LOG)
        vault.lantern(x, 6, 4, hanging=True)
    vault.fill(5, 1, 3, 6, 1, 5, "minecraft:polished_deepslate")
    for z, material in ((3, "minecraft:raw_copper_block"), (4, "minecraft:amethyst_block"),
                        (5, "minecraft:raw_iron_block")):
        vault.set(7, 1, z, material)
    vault.chest(5, 2, 4, "west", LOOT)
    return vault


TEMPLATES = {
    f"{FAMILY}/ore_exchange.nbt": build_exchange,
    f"{FAMILY}/haulage_gallery.nbt": build_gallery,
    f"{FAMILY}/ore_vault.nbt": build_vault,
}


def generate():
    for name, build in TEMPLATES.items():
        build().save(name)
    for pool, piece, fallback in (
        ("start", "ore_exchange", "minecraft:empty"),
        ("tunnels", "haulage_gallery", CAPS),
        ("caps", "ore_vault", "minecraft:empty"),
    ):
        path = Path(nbt.DATA) / f"worldgen/template_pool/{FAMILY}/{pool}.json"
        payload = json.loads(path.read_text())
        payload["elements"][0]["element"]["location"] = f"canopycavern:{FAMILY}/{piece}"
        payload["fallback"] = fallback
        path.write_text(json.dumps(payload, indent=2) + "\n")


if __name__ == "__main__":
    generate()
