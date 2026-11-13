"""Generate the four-district Hollow Village city."""

from uuid import NAMESPACE_URL, uuid5

from generate_underground_village import (
    AIR, COPPER, FLOOR, NATURAL_STONE, SUPPLY, TREASURY, TRIM,
    V4StructureBuilder, build_quarters, v3,
)

ASSET = "underground_hollow_village/cavern_city.nbt"
DISTRICTS = (
    (17, 17, 14, 12, "farmer", "minecraft:composter", "fisherman", "minecraft:barrel"),
    (57, 17, 15, 16, "toolsmith", "minecraft:smithing_table", "armorer", "minecraft:blast_furnace"),
    (17, 57, 16, 18, "librarian", "minecraft:bookshelf", "cartographer", "minecraft:cartography_table"),
    (57, 57, 13, 14, "mason", "minecraft:stonecutter", "cleric", "minecraft:brewing_stand"),
)


def build():
    city = V4StructureBuilder(75, 30, 75, fill_block="minecraft:structure_void")
    chambers = [(37, 37, 21, 27)] + [d[:4] for d in DISTRICTS]
    for x in range(75):
        for z in range(75):
            roof = 0
            for cx, cz, radius, height in chambers:
                distance = ((x - cx)**2 + (z - cz)**2) / radius**2
                if distance < 1:
                    roof = max(roof, int(height * (1 - distance)**0.5))
            if roof < 4:
                continue
            rock = NATURAL_STONE[(x * 7 + z * 11) % len(NATURAL_STONE)]
            city.set(x, 0, z, rock)
            city.fill(x, 1, z, x, roof - 1, z, AIR)
            city.set(x, roof, z, rock)

    def road(x0, z0, x1, z1):
        city.fill(x0, 0, z0, x1, 0, z1, TRIM)
        city.fill(x0, 1, z0, x1, 4, z1, AIR)
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if city.grid[x, 5, z][0] == "minecraft:structure_void":
                    city.set(x, 5, z, FLOOR)

    road(0, 35, 74, 39)
    road(35, 0, 39, 74)
    for x, z, _, _, job1, station1, job2, station2 in DISTRICTS:
        road(x - 2, min(z, 37), x + 2, max(z, 37))
        road(x - 7, z - 2, x + 7, z + 2)
        build_quarters(city, x - 9, z - 8, job1, station1)
        build_quarters(city, x + 3, z + 2, job2, station2)
        # Old quarter helper faces the original borough center; open a frontage toward the new street.
        for px, pz in ((x - 6, z - 2), (x + 6, z + 2)):
            city.door(px, 1, pz, "minecraft:dark_oak_door", "south" if pz < z else "north")
        city.set(x + 2, 0, z - 2, COPPER)
        city.chest(x + 2, 1, z - 2, "south", SUPPLY)
        for side in (-1, 1):
            for dx in (-5, -4, 4, 5):
                px, pz = x + dx, z + side * 4
                city.set(px, 0, pz, FLOOR)

    city.fill(29, 0, 29, 45, 0, 45, FLOOR)
    # Four civic columns and overhead ribs frame the public market.
    for x in (30, 44):
        for z in (30, 44):
            city.fill(x, 1, z, x, 10, z, "minecraft:polished_tuff")
            city.set(x, 5, z, "minecraft:amethyst_block")
            city.set(x, 10, z, COPPER)
        city.fill(x, 10, 30, x, 10, 44, COPPER)
        city.lantern(x, 9, 37, hanging=True)
    city.fill(30, 10, 37, 44, 10, 37, COPPER)
    city.lantern(37, 9, 37, hanging=True)
    city.set(40, 1, 37, ("minecraft:bell", {"attachment": "floor", "facing": "north", "powered": "false"}))
    city.chest(41, 1, 41, "north", TREASURY)
    city.add_sentinel(34, 1, 41)
    for index, entity in enumerate(city.entities):
        value = uuid5(NAMESPACE_URL, f"canopycavern:{ASSET}/{index}").bytes
        entity["nbt"]["UUID"] = v3.nbt_int_array(
            [int.from_bytes(value[i:i + 4], "big", signed=True) for i in range(0, 16, 4)]
        )
    return city


if __name__ == "__main__":
    build().save(ASSET)
