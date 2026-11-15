#!/usr/bin/env python3
from __future__ import annotations
"""
Generates outer-island The End Canopy Cavern Jigsaw structures, template pools,
structure sets, biome tags, and MC 26.3 chest loot tables (strictly excluding the
central dragon island minecraft:the_end, small_end_islands, and end_barrens):
  - canopycavern:chorus_monastery_citadel (end_highlands)
  - canopycavern:void_beacon_observatory (end_highlands, end_midlands)
  - canopycavern:ender_archive_vault (end_midlands, min_solid_thickness=14)
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
import dimension_structure_helpers as dsh
import generate_v04_ocean_and_villages as v4


def _write_end_structure(
    sid: str,
    biomes: list[str],
    spacing: int,
    separation: int,
    salt: int,
    terrain_guard: dict,
    start_height: int = 0,
    terrain_adaptation: str = "beard_thin",
):
    dsh.write_biome_tag(sid, biomes)
    v4.write_ns_json(
        dsh.CANOPY_DATA,
        f"worldgen/structure/{sid}.json",
        {
            "type": "canopycavern:surface_jigsaw",
            "biomes": f"#canopycavern:has_structure/{sid}",
            "max_distance_from_center": 48,
            "project_start_to_heightmap": "WORLD_SURFACE_WG",
            "size": 2,
            "spawn_overrides": {},
            "start_height": {"absolute": start_height},
            "start_pool": f"canopycavern:{sid}/start",
            "step": "surface_structures",
            "terrain_adaptation": terrain_adaptation,
            "terrain_guard": terrain_guard,
            "use_expansion_hack": False,
        },
    )
    dsh.write_structure_set(sid, spacing, separation, salt)


# ===========================================================================
# 1. CHORUS MONASTERY CITADEL (end_highlands)
# ===========================================================================
def build_chorus_monastery_citadel():
    sid = "chorus_monastery_citadel"
    pool_prefix = f"canopycavern:{sid}"

    # --- Cloister Start Piece (15x20x15) ---
    b = dsh.ExtradimensionalBuilder(15, 20, 15)
    b.chamfered_rect(0, 0, 14, 14, 0, "minecraft:end_stone_bricks")
    for x in range(2, 13):
        for z in range(2, 13):
            blk = "minecraft:purpur_block" if (x + z) % 3 == 0 else "minecraft:end_stone_bricks"
            b.set(x, 0, z, blk)

    # Cloister walls y=1..6 with stained tinted-glass & amethyst lancet windows
    for y in range(1, 7):
        for x in range(1, 14):
            for z in range(1, 14):
                if (x in (1, 13)) and (z in (1, 13)):
                    continue
                if x in (1, 13) or z in (1, 13):
                    if y in (3, 4) and (x in (4, 10) or z in (4, 10)):
                        b.set(x, y, z, "minecraft:tinted_glass")
                    elif x in (3, 11) or z in (3, 11):
                        b.set(x, y, z, ("minecraft:purpur_pillar", {"axis": "y"}))
                    else:
                        b.set(x, y, z, "minecraft:end_stone_bricks" if y <= 2 else "minecraft:purpur_block")

    for px, pz in ((2, 2), (12, 2), (2, 12), (12, 12)):
        b.pillar(px, 0, 7, pz, "minecraft:purpur_pillar", axis="y")
        b.end_rod(px, 8, pz, "up")

    # Upper scriptorium gallery y=6, accessed by interior stair along North aisle (x=4..10, z=3)
    b.fill(2, 6, 2, 12, 6, 12, "minecraft:purpur_block")
    for x in range(4, 11):
        for z in range(4, 11):
            b.set(x, 6, z, "minecraft:end_stone_bricks")
    b.build_straight_staircase(4, 3, 6, 1, "minecraft:purpur_stairs", "minecraft:purpur_block", headroom=4)

    # Upper clerestory columns & multi-tiered sweeping purpur pagoda roof (y=7..15)
    for px, pz in ((3, 3), (11, 3), (3, 11), (11, 11), (7, 2), (7, 12), (2, 7), (12, 7)):
        b.pillar(px, 7, 10, pz, "minecraft:purpur_pillar", axis="y")
    for x in range(2, 13):
        for z in range(2, 13):
            if x in (2, 12) or z in (2, 12):
                b.set(x, 7, z, "minecraft:end_stone_brick_wall")
    b.stepped_vault_roof(0, 0, 14, 14, 10, "minecraft:purpur_stairs", "minecraft:purpur_slab", "minecraft:purpur_block", "minecraft:sea_lantern")

    # Ground sanctuary centerpiece & upper vault chests
    b.set(7, 1, 7, "minecraft:amethyst_block")
    b.end_rod(7, 2, 7, "up")
    b.chest(7, 7, 10, "north", "canopycavern:chests/end_monastery_vault")
    b.chest(5, 7, 10, "north", "canopycavern:chests/end_monastery_vault")
    b.set(9, 7, 10, ("minecraft:lectern", {"facing": "north", "has_book": "false", "powered": "false"}))
    b.set(4, 1, 10, "minecraft:enchanting_table")

    # Entrance & 3 outgoing cloister sockets
    b.open_arch_portal_z(7, 1, 13, 1, 4, "minecraft:purpur_stairs", "minecraft:purpur_pillar", "minecraft:purpur_block")
    b.open_arch_portal_z(7, 1, 14, 1, 4, "minecraft:purpur_stairs", "minecraft:end_stone_bricks", "minecraft:end_stone_bricks")

    b.open_arch_portal_x(1, 1, 7, 1, 3, "minecraft:purpur_stairs", "minecraft:purpur_pillar", "minecraft:end_stone_bricks")
    b.open_arch_portal_x(0, 1, 7, 1, 3, "minecraft:purpur_stairs", "minecraft:end_stone_bricks", "minecraft:end_stone_bricks")
    b.jigsaw(0, 1, 7, "west_up", "canopycavern:monastery_entry", "canopycavern:monastery_dock", f"{pool_prefix}/wings", "minecraft:air")

    b.open_arch_portal_x(13, 1, 7, 1, 3, "minecraft:purpur_stairs", "minecraft:purpur_pillar", "minecraft:end_stone_bricks")
    b.open_arch_portal_x(14, 1, 7, 1, 3, "minecraft:purpur_stairs", "minecraft:end_stone_bricks", "minecraft:end_stone_bricks")
    b.jigsaw(14, 1, 7, "east_up", "canopycavern:monastery_entry", "canopycavern:monastery_dock", f"{pool_prefix}/wings", "minecraft:air")

    b.open_arch_portal_z(7, 1, 1, 1, 3, "minecraft:purpur_stairs", "minecraft:purpur_pillar", "minecraft:end_stone_bricks")
    b.open_arch_portal_z(7, 1, 0, 1, 3, "minecraft:purpur_stairs", "minecraft:end_stone_bricks", "minecraft:end_stone_bricks")
    b.jigsaw(7, 1, 0, "north_up", "canopycavern:monastery_entry", "canopycavern:monastery_dock", f"{pool_prefix}/wings", "minecraft:air")

    # 2 Shulker sentinels with generous clear pedestals
    b.add_shulker_guard(10, 1, 5)
    b.add_shulker_guard(7, 7, 6)

    b.validate_extra(f"{sid}/cloister", max_guards=3)
    b.save(f"{sid}/cloister.nbt")

    # --- Wing 1: Scriptorium Hall (9x13x9) ---
    m1 = dsh.ExtradimensionalBuilder(9, 13, 9)
    m1.chamfered_rect(0, 0, 8, 8, 0, "minecraft:end_stone_bricks")
    for y in range(1, 6):
        for x in range(1, 8):
            for z in range(1, 8):
                if x in (1, 7) or z in (1, 7):
                    m1.set(x, y, z, "minecraft:tinted_glass" if (y == 3 and (x == 4 or z == 4)) else "minecraft:purpur_block")
    m1.stepped_vault_roof(0, 0, 8, 8, 6, "minecraft:purpur_stairs", "minecraft:purpur_slab", "minecraft:end_stone_bricks", "minecraft:amethyst_block")
    m1.open_arch_portal_z(4, 1, 7, 1, 3, "minecraft:purpur_stairs", "minecraft:purpur_pillar", "minecraft:end_stone_bricks")
    m1.open_arch_portal_z(4, 1, 8, 1, 3, "minecraft:purpur_stairs", "minecraft:end_stone_bricks", "minecraft:end_stone_bricks")
    m1.jigsaw(4, 1, 8, "south_up", "canopycavern:monastery_dock", "canopycavern:monastery_entry", "minecraft:empty", "minecraft:air")
    m1.chest(4, 1, 2, "south", "canopycavern:chests/end_monastery_vault")
    m1.set(2, 1, 2, ("minecraft:lectern", {"facing": "east", "has_book": "false", "powered": "false"}))
    m1.end_rod(6, 1, 2, "up")
    m1.add_shulker_guard(5, 1, 4)
    m1.validate_extra(f"{sid}/scriptorium_hall", max_guards=2)
    m1.save(f"{sid}/scriptorium_hall.nbt")

    # --- Wing 2: Reliquary Chapel (9x14x9) ---
    m2 = dsh.ExtradimensionalBuilder(9, 14, 9)
    m2.chamfered_rect(0, 0, 8, 8, 0, "minecraft:end_stone_bricks")
    m2.fill(2, 0, 2, 6, 0, 6, "minecraft:amethyst_block")
    for y in range(1, 7):
        for x in range(1, 8):
            for z in range(1, 8):
                if x in (1, 7) or z in (1, 7):
                    m2.set(x, y, z, "minecraft:end_stone_bricks" if y <= 3 else "minecraft:purpur_block")
    m2.stepped_vault_roof(0, 0, 8, 8, 7, "minecraft:end_stone_brick_stairs", "minecraft:end_stone_brick_slab", "minecraft:purpur_block", "minecraft:sea_lantern")
    m2.open_arch_portal_z(4, 1, 7, 1, 3, "minecraft:purpur_stairs", "minecraft:purpur_pillar", "minecraft:end_stone_bricks")
    m2.open_arch_portal_z(4, 1, 8, 1, 3, "minecraft:purpur_stairs", "minecraft:end_stone_bricks", "minecraft:end_stone_bricks")
    m2.jigsaw(4, 1, 8, "south_up", "canopycavern:monastery_dock", "canopycavern:monastery_entry", "minecraft:empty", "minecraft:air")
    m2.chest(4, 1, 2, "south", "canopycavern:chests/end_monastery_vault")
    m2.end_rod(2, 1, 2, "up")
    m2.end_rod(6, 1, 2, "up")
    m2.validate_extra(f"{sid}/reliquary_chapel", max_guards=1)
    m2.save(f"{sid}/reliquary_chapel.nbt")

    # --- Fallback Cap (5x7x3) ---
    cap = dsh.ExtradimensionalBuilder(5, 7, 3)
    cap.fill(0, 0, 0, 4, 0, 2, "minecraft:end_stone_bricks")
    for x in range(0, 5):
        for y in range(1, 5):
            cap.set(x, y, 1, "minecraft:purpur_block")
            cap.set(x, y, 0, "minecraft:purpur_pillar" if x in (0, 4) else "minecraft:end_stone_bricks")
    cap.set(2, 2, 1, "minecraft:tinted_glass")
    cap.set(2, 3, 1, "minecraft:tinted_glass")
    cap.end_rod(2, 4, 2, "south")
    cap.slab(2, 5, 1, "minecraft:purpur_slab", "bottom")
    cap.jigsaw(2, 1, 2, "south_up", "canopycavern:monastery_dock", "canopycavern:monastery_entry", "minecraft:empty", "minecraft:air")
    cap.validate_extra(f"{sid}/cloister_arch_cap", max_guards=0)
    cap.save(f"{sid}/cloister_arch_cap.nbt")

    dsh.write_jigsaw_pool(f"{sid}/start", [(f"{pool_prefix}/cloister", 1, "rigid")])
    dsh.write_jigsaw_pool(
        f"{sid}/wings",
        [
            (f"{pool_prefix}/scriptorium_hall", 3, "rigid"),
            (f"{pool_prefix}/reliquary_chapel", 2, "rigid"),
            (f"{pool_prefix}/cloister_arch_cap", 1, "rigid"),
        ],
        fallback=f"{pool_prefix}/caps",
    )
    dsh.write_jigsaw_pool(f"{sid}/caps", [(f"{pool_prefix}/cloister_arch_cap", 1, "rigid")])

    dsh.write_loot_table("end_monastery_vault", [
        {"rolls": {"type": "minecraft:uniform", "min": 2, "max": 4}, "entries": [
            dsh.loot_item("minecraft:diamond", 7, 2, 6),
            dsh.loot_item("minecraft:ender_pearl", 9, 3, 8),
            dsh.loot_item("minecraft:chorus_fruit", 9, 5, 14),
            dsh.loot_item("minecraft:amethyst_shard", 8, 6, 14),
            dsh.loot_item("minecraft:emerald", 5, 3, 8),
            dsh.loot_item("minecraft:shulker_shell", 3, 1, 2),
        ]},
        {"rolls": 1, "entries": [
            dsh.loot_item("minecraft:potion", 5, 1, 1, potion_id="minecraft:slow_falling"),
            dsh.loot_item("minecraft:diamond_pickaxe", 3, enchant_levels=(22, 34)),
            dsh.loot_item("minecraft:diamond_sword", 2, enchant_levels=(22, 34)),
            dsh.loot_item("canopycavern:grotto_relic_compass", 2, 1, 1),
        ]},
    ])

    _write_end_structure(
        sid,
        ["minecraft:end_highlands"],
        spacing=38,
        separation=16,
        salt=8243107,
        terrain_guard={
            "core_probe_radius": 7,
            "max_core_relief": 6,
            "max_piece_relief": 7,
            "max_piece_embed": 4,
            "max_foundation_depth": 10,
            "min_rigid_pieces": 2,
            "min_piece_y_above_sea": 46,
            "allow_water": False,
            "max_water_depth": 0,
            "foundation_start_only": False,
            "foundation_block": "minecraft:end_stone_bricks",
            "min_solid_thickness": 6,
        },
    )


# ===========================================================================
# 2. VOID BEACON OBSERVATORY (end_highlands, end_midlands)
# ===========================================================================
def build_void_beacon_observatory():
    sid = "void_beacon_observatory"
    pool_prefix = f"canopycavern:{sid}"

    # --- Base Tower Start (13x20x13) ---
    b = dsh.ExtradimensionalBuilder(13, 20, 13)
    b.chamfered_rect(0, 0, 12, 12, 0, "minecraft:end_stone_bricks")
    for y in range(1, 7):
        for x in range(1, 12):
            for z in range(1, 12):
                if (x in (1, 11)) and (z in (1, 11)):
                    continue
                if x in (1, 11) or z in (1, 11):
                    b.grate(x, y, z, "minecraft:waxed_oxidized_copper_grate") if (y in (3, 4) and (x == 6 or z == 6)) else b.set(x, y, z, "minecraft:end_stone_bricks")

    # Second floor gallery y=6 (interior stairs ascending x=3..8 to landing x=9, y=6)
    b.fill(1, 6, 1, 11, 6, 11, "minecraft:purpur_block")
    b.build_straight_staircase(3, 2, 6, 1, "minecraft:purpur_stairs", "minecraft:purpur_block", headroom=4)

    # Safe ground-floor explorer shelter campfire corner + arrival lanterns
    b.set(3, 0, 9, "minecraft:end_stone_bricks")
    b.set(3, 1, 9, ("minecraft:campfire", {"facing": "north", "lit": "true", "signal_fire": "false", "waterlogged": "false"}))
    b.slab(4, 1, 9, "minecraft:end_stone_brick_slab", "bottom")
    b.slab(3, 1, 8, "minecraft:end_stone_brick_slab", "bottom")

    # Upper parapet & copper dome on y=7..12
    for x in range(1, 12):
        for z in range(1, 12):
            if (x in (1, 11)) and (z in (1, 11)):
                continue
            if x in (1, 11) or z in (1, 11):
                b.set(x, 7, z, "minecraft:end_stone_brick_wall")
    for px, pz in ((2, 2), (10, 2), (2, 10), (10, 10)):
        b.pillar(px, 7, 10, pz, "minecraft:purpur_pillar", axis="y")
    b.stepped_vault_roof(0, 0, 12, 12, 11, "minecraft:purpur_stairs", "minecraft:purpur_slab", "minecraft:tinted_glass", "minecraft:sea_lantern")

    b.chest(9, 7, 10, "north", "canopycavern:chests/end_observatory_cache")
    b.chest(3, 7, 10, "north", "canopycavern:chests/end_observatory_cache")
    b.set(6, 7, 6, "minecraft:amethyst_block")
    b.end_rod(6, 8, 6, "up")
    b.end_rod(2, 1, 3, "up")
    b.end_rod(10, 1, 3, "up")

    # South door + elevated East cantilevered balcony socket at y=7 (> startMinY + 2!)
    b.open_arch_portal_z(6, 1, 11, 1, 4, "minecraft:purpur_stairs", "minecraft:purpur_pillar", "minecraft:end_stone_bricks")
    b.open_arch_portal_z(6, 1, 12, 1, 4, "minecraft:purpur_stairs", "minecraft:end_stone_bricks", "minecraft:end_stone_bricks")

    b.open_arch_portal_x(11, 7, 6, 1, 3, "minecraft:purpur_stairs", "minecraft:purpur_pillar", "minecraft:purpur_block")
    b.open_arch_portal_x(12, 7, 6, 1, 3, "minecraft:purpur_stairs", "minecraft:purpur_block", "minecraft:purpur_block")
    b.jigsaw(12, 7, 6, "east_up", "canopycavern:obs_entry", "canopycavern:obs_dock", f"{pool_prefix}/arms", "minecraft:air")

    b.add_shulker_guard(9, 7, 6)
    b.validate_extra(f"{sid}/base_tower", max_guards=2)
    b.save(f"{sid}/base_tower.nbt")

    # --- Elevated Cantilever Sky Arm (9x11x9) ---
    arm = dsh.ExtradimensionalBuilder(9, 11, 9)
    arm.chamfered_rect(0, 0, 8, 8, 0, "minecraft:end_stone_bricks")
    for x in range(1, 8):
        for z in range(1, 8):
            if x in (1, 7) or z in (1, 7):
                arm.set(x, 1, z, "minecraft:end_stone_brick_wall")
    for px, pz in ((1, 1), (7, 1), (1, 7), (7, 7)):
        arm.pillar(px, 1, 3, pz, "minecraft:purpur_pillar", axis="y")
    arm.stepped_vault_roof(0, 0, 8, 8, 4, "minecraft:purpur_stairs", "minecraft:purpur_slab", "minecraft:waxed_oxidized_copper_grate", "minecraft:sea_lantern")
    arm.open_arch_portal_z(4, 1, 7, 1, 3, "minecraft:purpur_stairs", "minecraft:purpur_pillar", "minecraft:purpur_block")
    arm.open_arch_portal_z(4, 1, 8, 1, 3, "minecraft:purpur_stairs", "minecraft:purpur_block", "minecraft:purpur_block")
    arm.jigsaw(4, 1, 8, "south_up", "canopycavern:obs_dock", "canopycavern:obs_entry", "minecraft:empty", "minecraft:air")
    arm.chest(4, 1, 2, "south", "canopycavern:chests/end_observatory_cache")
    arm.end_rod(4, 2, 2, "up")
    arm.validate_extra(f"{sid}/sky_arm", max_guards=1)
    arm.save(f"{sid}/sky_arm.nbt")

    # --- Cap Balcony ---
    cap = dsh.ExtradimensionalBuilder(5, 6, 3)
    cap.fill(0, 0, 0, 4, 0, 2, "minecraft:purpur_block")
    for x in range(0, 5):
        cap.set(x, 1, 1, "minecraft:end_stone_brick_wall")
    cap.pillar(0, 1, 3, 1, "minecraft:purpur_pillar", axis="y")
    cap.pillar(4, 1, 3, 1, "minecraft:purpur_pillar", axis="y")
    cap.end_rod(2, 1, 0, "up")
    cap.jigsaw(2, 1, 2, "south_up", "canopycavern:obs_dock", "canopycavern:obs_entry", "minecraft:empty", "minecraft:air")
    cap.validate_extra(f"{sid}/arm_cap", max_guards=0)
    cap.save(f"{sid}/arm_cap.nbt")

    dsh.write_jigsaw_pool(f"{sid}/start", [(f"{pool_prefix}/base_tower", 1, "rigid")])
    dsh.write_jigsaw_pool(
        f"{sid}/arms",
        [(f"{pool_prefix}/sky_arm", 3, "rigid"), (f"{pool_prefix}/arm_cap", 1, "rigid")],
        fallback=f"{pool_prefix}/caps",
    )
    dsh.write_jigsaw_pool(f"{sid}/caps", [(f"{pool_prefix}/arm_cap", 1, "rigid")])

    dsh.write_loot_table("end_observatory_cache", [
        {"rolls": {"type": "minecraft:uniform", "min": 2, "max": 4}, "entries": [
            dsh.loot_item("minecraft:ender_pearl", 9, 2, 6),
            dsh.loot_item("minecraft:amethyst_shard", 8, 5, 12),
            dsh.loot_item("minecraft:spyglass", 3, 1, 1),
            dsh.loot_item("minecraft:gold_ingot", 8, 4, 9),
            dsh.loot_item("minecraft:diamond", 4, 1, 3),
            dsh.loot_item("minecraft:experience_bottle", 6, 4, 8),
        ]},
        {"rolls": 1, "entries": [
            dsh.loot_item("minecraft:potion", 5, 1, 1, potion_id="minecraft:slow_falling"),
            dsh.loot_item("minecraft:iron_chestplate", 2, enchant_levels=(16, 28)),
            dsh.loot_item("canopycavern:grotto_relic_compass", 2, 1, 1),
        ]},
    ])

    _write_end_structure(
        sid,
        ["minecraft:end_highlands", "minecraft:end_midlands"],
        spacing=34,
        separation=14,
        salt=8243209,
        terrain_guard={
            "core_probe_radius": 6,
            "max_core_relief": 6,
            "max_piece_relief": 7,
            "max_piece_embed": 4,
            "max_foundation_depth": 10,
            "min_rigid_pieces": 1,
            "min_piece_y_above_sea": 46,
            "allow_water": False,
            "max_water_depth": 0,
            "foundation_start_only": True,
            "foundation_block": "minecraft:end_stone_bricks",
            "min_solid_thickness": 6,
        },
    )


# ===========================================================================
# 3. ENDER ARCHIVE VAULT (end_midlands, semi-embedded, min_solid_thickness=14)
# ===========================================================================
def build_ender_archive_vault():
    sid = "ender_archive_vault"
    pool_prefix = f"canopycavern:{sid}"

    # Semi-embedded sunken rotunda (start_height = -4):
    # y=0..4 sits in island bedrock (archive hall floor at y=1), y=5 is ground surface entry!
    b = dsh.ExtradimensionalBuilder(15, 19, 15)
    b.chamfered_rect(0, 0, 14, 14, 0, "minecraft:end_stone_bricks")
    for x in range(2, 13):
        for z in range(2, 13):
            b.set(x, 0, z, "minecraft:polished_blackstone_bricks" if (x + z) % 2 == 0 else "minecraft:end_stone_bricks")

    # Embedded vault walls y=1..5 + above-ground rotunda dome y=6..13
    for y in range(1, 9):
        for x in range(1, 14):
            for z in range(1, 14):
                if (x in (1, 13)) and (z in (1, 13)):
                    continue
                if x in (1, 13) or z in (1, 13):
                    if y in (6, 7) and (x in (4, 10) or z in (4, 10)):
                        b.set(x, y, z, "minecraft:tinted_glass")
                    else:
                        b.set(x, y, z, "minecraft:end_stone_bricks" if y <= 5 else "minecraft:purpur_block")

    for px, pz in ((2, 2), (12, 2), (2, 12), (12, 12)):
        b.pillar(px, 0, 9, pz, "minecraft:purpur_pillar", axis="y")
    b.stepped_vault_roof(0, 0, 14, 14, 9, "minecraft:end_stone_brick_stairs", "minecraft:end_stone_brick_slab", "minecraft:purpur_block", "minecraft:sea_lantern")

    # Grand surface entry staircase descending smoothly from South surface (z=14, y=5 -> floor y=1 at z=9)
    b.open_arch_portal_z(7, 5, 13, 1, 4, "minecraft:purpur_stairs", "minecraft:purpur_pillar", "minecraft:purpur_block")
    b.open_arch_portal_z(7, 5, 14, 1, 4, "minecraft:purpur_stairs", "minecraft:end_stone_bricks", "minecraft:end_stone_bricks")
    for step in range(4):
        z = 12 - step
        y_step = 4 - step
        for sx in (6, 7, 8):
            b.set(sx, y_step - 1 if y_step > 1 else 0, z, "minecraft:end_stone_bricks")
            b.stairs(sx, y_step, z, "minecraft:end_stone_brick_stairs", "south", half="bottom")
            for clr_y in range(y_step + 1, y_step + 5):
                b.set(sx, clr_y, z, "minecraft:air")

    # Treasure vault chests, reading carrels & crystal display
    b.chest(6, 1, 3, "south", "canopycavern:chests/end_archive_vault")
    b.chest(8, 1, 3, "south", "canopycavern:chests/end_archive_vault")
    b.set(4, 1, 3, ("minecraft:lectern", {"facing": "south", "has_book": "false", "powered": "false"}))
    b.set(10, 1, 3, ("minecraft:lectern", {"facing": "south", "has_book": "false", "powered": "false"}))
    b.set(3, 1, 7, "minecraft:amethyst_block")
    b.end_rod(3, 2, 7, "up")
    b.set(11, 1, 7, "minecraft:amethyst_block")
    b.end_rod(11, 2, 7, "up")

    # 1 Shulker guardian in crystal vault niche
    b.add_shulker_guard(7, 1, 6)
    b.validate_extra(f"{sid}/rotunda", max_guards=2)
    b.save(f"{sid}/rotunda.nbt")

    dsh.write_jigsaw_pool(f"{sid}/start", [(f"{pool_prefix}/rotunda", 1, "rigid")])

    dsh.write_loot_table("end_archive_vault", [
        {"rolls": {"type": "minecraft:uniform", "min": 2, "max": 4}, "entries": [
            dsh.loot_item("minecraft:diamond", 6, 2, 5),
            dsh.loot_item("minecraft:amethyst_shard", 8, 6, 16),
            dsh.loot_item("minecraft:ender_pearl", 9, 4, 10),
            dsh.loot_item("minecraft:emerald", 6, 4, 10),
            dsh.loot_item("minecraft:shulker_shell", 3, 1, 2),
        ]},
        {"rolls": 1, "entries": [
            dsh.loot_item("minecraft:enchanted_book", 5, enchant_levels=(24, 36)),
            dsh.loot_item("minecraft:potion", 4, 1, 1, potion_id="minecraft:slow_falling"),
            dsh.loot_item("minecraft:diamond_leggings", 2, enchant_levels=(22, 34)),
            dsh.loot_item("canopycavern:grotto_relic_compass", 2, 1, 1),
        ]},
    ])

    _write_end_structure(
        sid,
        ["minecraft:end_midlands"],
        spacing=36,
        separation=14,
        salt=8243311,
        start_height=-4,
        terrain_adaptation="none",
        terrain_guard={
            "core_probe_radius": 7,
            "max_core_relief": 5,
            "max_piece_relief": 6,
            "max_piece_embed": 8,
            "max_foundation_depth": 10,
            "min_rigid_pieces": 1,
            "min_piece_y_above_sea": 42,
            "allow_water": False,
            "max_water_depth": 0,
            "foundation_start_only": False,
            "foundation_block": "minecraft:end_stone_bricks",
            "min_solid_thickness": 14,
        },
    )


def build_all():
    build_chorus_monastery_citadel()
    build_void_beacon_observatory()
    build_ender_archive_vault()
    print("Generated all 3 The End outer-island Jigsaw structures, pools, tags, sets, and loot tables.")


if __name__ == "__main__":
    build_all()
