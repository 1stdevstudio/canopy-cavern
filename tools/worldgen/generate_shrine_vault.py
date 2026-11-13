"""Build the shrine's ribbed nave with lower side aisles."""

from generate_v03_structures import StructureBuilder, write_json


def build():
    shrine = StructureBuilder(19, 14, 15, fill_block="minecraft:structure_void")
    brick = "minecraft:deepslate_bricks"
    tiles = "minecraft:deepslate_tiles"
    for x in range(19):
        ceiling = min(13, 5 + min(x, 18 - x))
        for z in range(15):
            shrine.set(x, 0, z, "minecraft:polished_deepslate")
            for y in range(1, ceiling):
                shrine.set(x, y, z, brick if x in (0, 18) or z in (0, 14) else "minecraft:air")
            shrine.set(x, ceiling, z, tiles if z % 4 else "minecraft:chiseled_deepslate")
    for x in (0, 18):
        for z in range(6, 9):
            for y in range(1, 4):
                shrine.set(x, y, z, "minecraft:air")
        shrine.jigsaw(x, 1, 7, "west_up" if x == 0 else "east_up",
                      "canopycavern:wing", "canopycavern:wing",
                      "canopycavern:cavern_shrine/wings", "minecraft:air")
    for x in (4, 14):
        for z in (3, 11):
            shrine.fill(x, 1, z, x, 8, z, brick)
            shrine.set(x, 7, z, "minecraft:sea_lantern")
    shrine.fill(7, 1, 5, 11, 1, 9, tiles)
    for x in range(7, 12):
        shrine.stairs(x, 1, 4, "minecraft:deepslate_tile_stairs", "south")
    shrine.fill(8, 2, 6, 10, 2, 8, "minecraft:chiseled_deepslate")
    shrine.fill(9, 3, 7, 9, 5, 7, "minecraft:amethyst_block")
    shrine.set(9, 6, 7, ("minecraft:amethyst_cluster", {"facing": "up", "waterlogged": "false"}))
    shrine.chest(8, 2, 5, "north", "canopycavern:chests/cavern_shrine")
    shrine.chest(15, 1, 10, "west", "canopycavern:chests/cavern_shrine")
    return shrine


if __name__ == "__main__":
    build().save("cavern_shrine/vaulted_nave.nbt")
    write_json("worldgen/template_pool/cavern_shrine/start.json", {
        "elements": [{
            "element": {
                "element_type": "minecraft:single_pool_element",
                "location": "canopycavern:cavern_shrine/vaulted_nave",
                "processors": {"processors": []},
                "projection": "rigid"
            },
            "weight": 1
        }],
        "fallback": "minecraft:empty"
    })
