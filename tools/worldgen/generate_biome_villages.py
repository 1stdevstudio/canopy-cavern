"""Generate sprawling, non-boxy grand cities and branching road networks for the six biome villages."""

from __future__ import annotations

from dataclasses import dataclass

from generate_v04_ocean_and_villages import v3
from grand_city_architecture import CityPalette, generate_city


@dataclass(frozen=True)
class BiomeCitySpec:
    palette: CityPalette
    salt: int
    spacing: int
    separation: int


BIOME_CITIES: tuple[BiomeCitySpec, ...] = (
    BiomeCitySpec(
        palette=CityPalette(
            city_id="jungle_canopy_hamlet",
            biomes=("minecraft:jungle", "minecraft:bamboo_jungle", "minecraft:sparse_jungle"),
            villager_type="minecraft:jungle",
            profile="jungle",
            plinth="minecraft:mossy_cobblestone",
            plinth_alt="minecraft:mossy_stone_bricks",
            wall="minecraft:jungle_planks",
            wall_alt="minecraft:bamboo_mosaic",
            log="minecraft:stripped_jungle_log",
            floor="minecraft:bamboo_mosaic",
            road="minecraft:packed_mud",
            roof_stair="minecraft:bamboo_stairs",
            roof_slab="minecraft:bamboo_slab",
            roof_solid="minecraft:bamboo_planks",
            accent_roof="minecraft:moss_block",
            fence="minecraft:bamboo_fence",
            door="minecraft:jungle_door",
            pane="minecraft:glass_pane",
            stained_pane="minecraft:lime_stained_glass_pane",
            bed="minecraft:lime_bed",
            flower="minecraft:flowering_azalea",
            awning_a="minecraft:lime_wool",
            awning_b="minecraft:yellow_wool",
            garden_soil="minecraft:grass_block",
            foundation="minecraft:mossy_cobblestone",
            core_relief=4,
            piece_relief=5,
        ),
        salt=6741041,
        spacing=29,
        separation=10,
    ),
    BiomeCitySpec(
        palette=CityPalette(
            city_id="mangrove_marsh_village",
            biomes=("minecraft:swamp", "minecraft:mangrove_swamp"),
            villager_type="minecraft:swamp",
            profile="canopy",
            plinth="minecraft:mud_bricks",
            plinth_alt="minecraft:packed_mud",
            wall="minecraft:mangrove_planks",
            wall_alt="minecraft:packed_mud",
            log="minecraft:stripped_mangrove_log",
            floor="minecraft:mud_bricks",
            road="minecraft:mangrove_planks",
            roof_stair="minecraft:mangrove_stairs",
            roof_slab="minecraft:mangrove_slab",
            roof_solid="minecraft:mangrove_planks",
            accent_roof="minecraft:mud_bricks",
            fence="minecraft:mangrove_fence",
            door="minecraft:mangrove_door",
            pane="minecraft:glass_pane",
            stained_pane="minecraft:cyan_stained_glass_pane",
            bed="minecraft:brown_bed",
            flower="minecraft:blue_orchid",
            awning_a="minecraft:cyan_wool",
            awning_b="minecraft:light_gray_wool",
            garden_soil="minecraft:grass_block",
            foundation="minecraft:mud_bricks",
            stilt_height=2,
            allow_water=True,
            max_water_depth=2,
            min_piece_y_above_sea=0,
            start_y=1,
            terrain_adaptation="none",
            core_relief=4,
            piece_relief=5,
        ),
        salt=6741042,
        spacing=31,
        separation=11,
    ),
    BiomeCitySpec(
        palette=CityPalette(
            city_id="badlands_pueblo",
            biomes=("minecraft:badlands", "minecraft:eroded_badlands", "minecraft:wooded_badlands"),
            villager_type="minecraft:desert",
            profile="adobe",
            plinth="minecraft:red_sandstone",
            plinth_alt="minecraft:chiseled_red_sandstone",
            wall="minecraft:orange_terracotta",
            wall_alt="minecraft:yellow_terracotta",
            log="minecraft:stripped_acacia_log",
            floor="minecraft:smooth_red_sandstone",
            road="minecraft:cut_red_sandstone",
            roof_stair="minecraft:red_sandstone_stairs",
            roof_slab="minecraft:red_sandstone_slab",
            roof_solid="minecraft:smooth_red_sandstone",
            accent_roof="minecraft:terracotta",
            fence="minecraft:acacia_fence",
            door="minecraft:acacia_door",
            pane="minecraft:glass_pane",
            stained_pane="minecraft:orange_stained_glass_pane",
            bed="minecraft:orange_bed",
            flower="minecraft:dead_bush",
            awning_a="minecraft:orange_wool",
            awning_b="minecraft:yellow_wool",
            garden_soil="minecraft:red_sand",
            foundation="minecraft:red_sandstone",
            core_relief=5,
            piece_relief=5,
        ),
        salt=6741043,
        spacing=31,
        separation=11,
    ),
    BiomeCitySpec(
        palette=CityPalette(
            city_id="cherry_grove_hamlet",
            biomes=("minecraft:cherry_grove", "minecraft:meadow"),
            villager_type="minecraft:plains",
            profile="pagoda",
            plinth="minecraft:cobblestone",
            plinth_alt="minecraft:polished_diorite",
            wall="minecraft:cherry_planks",
            wall_alt="minecraft:white_terracotta",
            log="minecraft:stripped_cherry_log",
            floor="minecraft:cherry_planks",
            road="minecraft:polished_andesite",
            roof_stair="minecraft:dark_oak_stairs",
            roof_slab="minecraft:dark_oak_slab",
            roof_solid="minecraft:dark_oak_planks",
            accent_roof="minecraft:pink_wool",
            fence="minecraft:cherry_fence",
            door="minecraft:cherry_door",
            pane="minecraft:glass_pane",
            stained_pane="minecraft:pink_stained_glass_pane",
            bed="minecraft:pink_bed",
            flower="minecraft:pink_tulip",
            awning_a="minecraft:pink_wool",
            awning_b="minecraft:white_wool",
            garden_soil="minecraft:grass_block",
            foundation="minecraft:cobblestone",
            core_relief=4,
            piece_relief=5,
        ),
        salt=6741044,
        spacing=32,
        separation=11,
    ),
    BiomeCitySpec(
        palette=CityPalette(
            city_id="mushroom_island_outpost",
            biomes=("minecraft:mushroom_fields",),
            villager_type="minecraft:plains",
            profile="mushroom",
            plinth="minecraft:mossy_cobblestone",
            plinth_alt="minecraft:mossy_stone_bricks",
            wall="minecraft:oak_planks",
            wall_alt="minecraft:white_terracotta",
            log="minecraft:stripped_birch_log",
            floor="minecraft:moss_block",
            road="minecraft:mycelium",
            roof_stair="minecraft:oak_stairs",
            roof_slab="minecraft:oak_slab",
            roof_solid="minecraft:red_mushroom_block",
            accent_roof="minecraft:brown_mushroom_block",
            fence="minecraft:oak_fence",
            door="minecraft:oak_door",
            pane="minecraft:glass_pane",
            stained_pane="minecraft:red_stained_glass_pane",
            bed="minecraft:red_bed",
            flower="minecraft:red_mushroom",
            awning_a="minecraft:red_wool",
            awning_b="minecraft:white_wool",
            garden_soil="minecraft:mycelium",
            foundation="minecraft:mossy_cobblestone",
            core_relief=4,
            piece_relief=5,
        ),
        salt=6741045,
        spacing=32,
        separation=11,
    ),
    BiomeCitySpec(
        palette=CityPalette(
            city_id="frozen_ridge_village",
            biomes=(
                "minecraft:snowy_slopes",
                "minecraft:frozen_peaks",
                "minecraft:jagged_peaks",
                "minecraft:grove",
                "minecraft:ice_spikes",
            ),
            villager_type="minecraft:snow",
            profile="alpine",
            plinth="minecraft:cobblestone",
            plinth_alt="minecraft:stone_bricks",
            wall="minecraft:spruce_planks",
            wall_alt="minecraft:packed_ice",
            log="minecraft:stripped_spruce_log",
            floor="minecraft:spruce_planks",
            road="minecraft:stone_bricks",
            roof_stair="minecraft:deepslate_tile_stairs",
            roof_slab="minecraft:deepslate_tile_slab",
            roof_solid="minecraft:deepslate_tiles",
            accent_roof="minecraft:packed_ice",
            fence="minecraft:spruce_fence",
            door="minecraft:spruce_door",
            pane="minecraft:glass_pane",
            stained_pane="minecraft:light_blue_stained_glass_pane",
            bed="minecraft:light_blue_bed",
            flower="minecraft:blue_orchid",
            awning_a="minecraft:light_blue_wool",
            awning_b="minecraft:white_wool",
            garden_soil="minecraft:grass_block",
            foundation="minecraft:cobblestone",
            core_relief=5,
            piece_relief=6,
        ),
        salt=6741046,
        spacing=34,
        separation=12,
    ),
)

LEGACY_ROLES = ("farmer", "librarian", "weaponsmith", "cartographer")


def _cleanup_legacy_city_files(city_id: str):
    struct_dir = v3.STRUCT_DIR / city_id
    if struct_dir.exists():
        for obsolete in ["hillside_village.nbt"] + [
            f"{prefix}_{role}.nbt" for prefix in ("street", "house") for role in LEGACY_ROLES
        ]:
            p = struct_dir / obsolete
            if p.exists():
                p.unlink()

    pool_dir = v3.DATA / "worldgen" / "template_pool" / city_id
    if pool_dir.exists():
        for obsolete in ["side_gardens.json"] + [
            f"{prefix}_{role}.json" for prefix in ("wing", "house") for role in LEGACY_ROLES
        ]:
            p = pool_dir / obsolete
            if p.exists():
                p.unlink()


def generate_all_biome_cities():
    for spec in BIOME_CITIES:
        _cleanup_legacy_city_files(spec.palette.city_id)
        generate_city(
            spec.palette,
            v3.write_json,
            salt=spec.salt,
            spacing=spec.spacing,
            separation=spec.separation,
            write_structure_set=True,
        )


if __name__ == "__main__":
    generate_all_biome_cities()
    print("Generated 6 non-boxy grand biome villager cities!")
