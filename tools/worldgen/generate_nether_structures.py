#!/usr/bin/env python3
from __future__ import annotations
"""
Generates Nether Canopy Cavern Jigsaw structures, template pools, structure sets,
biome tags, and MC 26.3 chest loot tables:
  - canopycavern:cinder_vault_bastion (nether_wastes, crimson_forest)
  - canopycavern:soul_catacomb_reliquary (soul_sand_valley)
  - canopycavern:basalt_thermal_spire (basalt_deltas)
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
import dimension_structure_helpers as dsh
import generate_v04_ocean_and_villages as v4


def _write_nether_structure(sid: str, biomes: list[str], spacing: int, separation: int, salt: int, cavern_guard: dict):
    dsh.write_biome_tag(sid, biomes)
    v4.write_ns_json(
        dsh.CANOPY_DATA,
        f"worldgen/structure/{sid}.json",
        {
            "type": "canopycavern:nether_cavern_jigsaw",
            "biomes": f"#canopycavern:has_structure/{sid}",
            "max_distance_from_center": 48,
            "size": 2,
            "spawn_overrides": {},
            "start_pool": f"canopycavern:{sid}/start",
            "step": "underground_structures",
            "terrain_adaptation": "none",
            "cavern_guard": cavern_guard,
            "use_expansion_hack": False,
        },
    )
    dsh.write_structure_set(sid, spacing, separation, salt)


# ===========================================================================
# 1. CINDER VAULT BASTION (nether_wastes, crimson_forest)
# ===========================================================================
def build_cinder_vault_bastion():
    sid = "cinder_vault_bastion"
    pool_prefix = f"canopycavern:{sid}"

    # --- Core Sanctum (15x19x15) ---
    b = dsh.ExtradimensionalBuilder(15, 19, 15)
    # Chamfered blackstone plinth & patterned floor at y=0
    b.chamfered_rect(0, 0, 14, 14, 0, "minecraft:polished_blackstone_bricks")
    for x in range(2, 13):
        for z in range(2, 13):
            blk = "minecraft:gilded_blackstone" if (x in (5, 9) and z in (5, 9)) or (x == 7 and z == 7) else "minecraft:polished_blackstone"
            b.set(x, 0, z, blk)
    b.fill(5, 0, 5, 9, 0, 9, "minecraft:polished_blackstone_bricks")

    # Outer walls & buttresses (y=1..8) with chamfered corners (cut 1x1 corners)
    for y in range(1, 9):
        for x in range(1, 14):
            for z in range(1, 14):
                is_corner = (x in (1, 13)) and (z in (1, 13))
                is_wall = x in (1, 13) or z in (1, 13)
                if is_corner or not is_wall:
                    continue
                if y >= 8:
                    b.set(x, y, z, "minecraft:gilded_blackstone" if (x + z) % 3 == 0 else "minecraft:polished_blackstone_bricks")
                elif y in (4, 5, 6) and (x in (4, 10) or z in (4, 10)):
                    b.grate(x, y, z, "minecraft:waxed_copper_grate")
                else:
                    blk = "minecraft:cracked_polished_blackstone_bricks" if (x + y + z) % 5 == 0 else "minecraft:polished_blackstone_bricks"
                    b.set(x, y, z, blk)

    # Corner chamfer piers + crimson beams + glowing grate sconces
    for px, pz in ((2, 2), (12, 2), (2, 12), (12, 12)):
        b.pillar(px, 0, 9, pz, "minecraft:chiseled_polished_blackstone")
        b.set(px, 6, pz, "minecraft:gilded_blackstone")
    for px, pz in ((1, 4), (1, 10), (13, 4), (13, 10), (4, 1), (10, 1), (4, 13), (10, 13)):
        b.set(px, 5, pz, "minecraft:shroomlight")

    # Interior double-height crimson crossbeams & chandelier (y=8)
    for x in range(2, 13):
        b.set(x, 8, 7, ("minecraft:crimson_stem", {"axis": "x"}))
    for z in range(2, 13):
        b.set(7, 8, z, ("minecraft:crimson_stem", {"axis": "z"}))
    b.iron_chain_lantern(7, 8, 7, chain_len=1, lantern_id="minecraft:soul_lantern")

    # Stepped cascading vault roof (y=9..13) -> never a flat cube!
    b.stepped_vault_roof(
        0, 0, 14, 14, 9,
        "minecraft:polished_blackstone_brick_stairs",
        "minecraft:polished_blackstone_brick_slab",
        "minecraft:red_nether_bricks",
        "minecraft:gilded_blackstone",
    )

    # Central raised gilded shrine dais with double vault chests
    b.fill(6, 1, 6, 8, 1, 8, "minecraft:chiseled_polished_blackstone")
    b.set(7, 1, 6, "minecraft:gilded_blackstone")
    b.chest(6, 2, 6, "south", "canopycavern:chests/nether_bastion_vault")
    b.chest(8, 2, 6, "south", "canopycavern:chests/nether_bastion_vault")
    b.soul_lantern(7, 2, 7, hanging=False)

    # Cool safe forge corner (blast furnace + smithing table + shroomlight grate hearth)
    b.set(3, 1, 3, "minecraft:gilded_blackstone")
    b.set(3, 2, 3, "minecraft:shroomlight")
    b.grate(4, 1, 3, "minecraft:waxed_copper_grate")
    b.set(3, 1, 4, ("minecraft:blast_furnace", {"facing": "east", "lit": "false"}))
    b.set(3, 1, 5, "minecraft:smithing_table")
    b.set(11, 1, 3, ("minecraft:brewing_stand", {"has_bottle_0": "false", "has_bottle_1": "false", "has_bottle_2": "false"}))

    # Grand South entrance arch (walk-in)
    b.open_arch_portal_z(7, 1, 13, 1, 4, "minecraft:polished_blackstone_brick_stairs", "minecraft:chiseled_polished_blackstone", "minecraft:gilded_blackstone")
    b.open_arch_portal_z(7, 1, 14, 1, 4, "minecraft:polished_blackstone_brick_stairs", "minecraft:polished_blackstone_bricks", "minecraft:polished_blackstone_bricks")

    # 3 Outgoing modular sockets (West, East, North)
    b.open_arch_portal_x(1, 1, 7, 1, 3, "minecraft:polished_blackstone_brick_stairs", "minecraft:chiseled_polished_blackstone", "minecraft:polished_blackstone_bricks")
    b.open_arch_portal_x(0, 1, 7, 1, 3, "minecraft:polished_blackstone_brick_stairs", "minecraft:polished_blackstone_bricks", "minecraft:polished_blackstone_bricks")
    b.jigsaw(0, 1, 7, "west_up", "canopycavern:cinder_entry", "canopycavern:cinder_dock", f"{pool_prefix}/branches", "minecraft:air")

    b.open_arch_portal_x(13, 1, 7, 1, 3, "minecraft:polished_blackstone_brick_stairs", "minecraft:chiseled_polished_blackstone", "minecraft:polished_blackstone_bricks")
    b.open_arch_portal_x(14, 1, 7, 1, 3, "minecraft:polished_blackstone_brick_stairs", "minecraft:polished_blackstone_bricks", "minecraft:polished_blackstone_bricks")
    b.jigsaw(14, 1, 7, "east_up", "canopycavern:cinder_entry", "canopycavern:cinder_dock", f"{pool_prefix}/branches", "minecraft:air")

    b.open_arch_portal_z(7, 1, 1, 1, 3, "minecraft:polished_blackstone_brick_stairs", "minecraft:chiseled_polished_blackstone", "minecraft:polished_blackstone_bricks")
    b.open_arch_portal_z(7, 1, 0, 1, 3, "minecraft:polished_blackstone_brick_stairs", "minecraft:polished_blackstone_bricks", "minecraft:polished_blackstone_bricks")
    b.jigsaw(7, 1, 0, "north_up", "canopycavern:cinder_entry", "canopycavern:cinder_dock", f"{pool_prefix}/branches", "minecraft:air")

    # Vanilla-Plus guard quota: 1 Brute + 1 Piglin in clear floor lanes
    b.add_piglin_brute(4, 1, 10)
    b.add_piglin_guard(10, 1, 10)

    b.validate_extra(f"{sid}/sanctum_core", max_guards=3)
    b.save(f"{sid}/sanctum_core.nbt")

    # --- Branch 1: Treasury Wing (9x13x9) ---
    w1 = dsh.ExtradimensionalBuilder(9, 13, 9)
    w1.chamfered_rect(0, 0, 8, 8, 0, "minecraft:polished_blackstone_bricks")
    w1.fill(1, 0, 1, 7, 0, 7, "minecraft:gilded_blackstone")
    for y in range(1, 6):
        for x in range(1, 8):
            for z in range(1, 8):
                if x in (1, 7) or z in (1, 7):
                    w1.grate(x, y, z, "minecraft:waxed_copper_grate") if (y == 3 and (x == 4 or z == 4)) else w1.set(x, y, z, "minecraft:polished_blackstone_bricks")
    w1.pillar(1, 1, 6, 1, "minecraft:chiseled_polished_blackstone")
    w1.pillar(7, 1, 6, 1, "minecraft:chiseled_polished_blackstone")
    w1.stepped_vault_roof(0, 0, 8, 8, 6, "minecraft:polished_blackstone_brick_stairs", "minecraft:polished_blackstone_brick_slab", "minecraft:red_nether_bricks", "minecraft:gilded_blackstone")
    w1.open_arch_portal_z(4, 1, 7, 1, 3, "minecraft:polished_blackstone_brick_stairs", "minecraft:chiseled_polished_blackstone", "minecraft:polished_blackstone_bricks")
    w1.open_arch_portal_z(4, 1, 8, 1, 3, "minecraft:polished_blackstone_brick_stairs", "minecraft:polished_blackstone_bricks", "minecraft:polished_blackstone_bricks")
    w1.jigsaw(4, 1, 8, "south_up", "canopycavern:cinder_dock", "canopycavern:cinder_entry", "minecraft:empty", "minecraft:air")
    w1.chest(4, 1, 2, "south", "canopycavern:chests/nether_bastion_vault")
    w1.soul_lantern(2, 1, 2, hanging=False)
    w1.soul_lantern(6, 1, 2, hanging=False)
    w1.add_piglin_guard(5, 1, 4)
    w1.validate_extra(f"{sid}/treasury_wing", max_guards=2)
    w1.save(f"{sid}/treasury_wing.nbt")

    # --- Branch 2: Crimson Dormitory & Apothecary (9x13x9) ---
    w2 = dsh.ExtradimensionalBuilder(9, 13, 9)
    w2.chamfered_rect(0, 0, 8, 8, 0, "minecraft:polished_blackstone_bricks")
    w2.fill(2, 0, 2, 6, 0, 6, "minecraft:crimson_planks")
    for y in range(1, 6):
        for x in range(1, 8):
            for z in range(1, 8):
                if x in (1, 7) or z in (1, 7):
                    w2.set(x, y, z, "minecraft:crimson_planks" if y == 3 else "minecraft:polished_blackstone_bricks")
    w2.stepped_vault_roof(0, 0, 8, 8, 6, "minecraft:crimson_stairs", "minecraft:crimson_slab", "minecraft:crimson_planks", "minecraft:shroomlight")
    w2.open_arch_portal_z(4, 1, 7, 1, 3, "minecraft:crimson_stairs", "minecraft:crimson_stem", "minecraft:polished_blackstone_bricks")
    w2.open_arch_portal_z(4, 1, 8, 1, 3, "minecraft:polished_blackstone_brick_stairs", "minecraft:polished_blackstone_bricks", "minecraft:polished_blackstone_bricks")
    w2.jigsaw(4, 1, 8, "south_up", "canopycavern:cinder_dock", "canopycavern:cinder_entry", "minecraft:empty", "minecraft:air")
    w2.chest(2, 1, 2, "east", "canopycavern:chests/nether_bastion_supply")
    w2.set(6, 1, 2, ("minecraft:brewing_stand", {"has_bottle_0": "false", "has_bottle_1": "false", "has_bottle_2": "false"}))
    w2.iron_chain_lantern(4, 6, 4, chain_len=1)
    w2.add_piglin_guard(4, 1, 4)
    w2.validate_extra(f"{sid}/crimson_dormitory", max_guards=2)
    w2.save(f"{sid}/crimson_dormitory.nbt")

    # --- Branch 3: Gilded Watch Turret (9x15x9) ---
    w3 = dsh.ExtradimensionalBuilder(9, 15, 9)
    w3.chamfered_rect(0, 0, 8, 8, 0, "minecraft:polished_blackstone_bricks")
    for y in range(1, 5):
        for x in range(1, 8):
            for z in range(1, 8):
                if x in (1, 7) or z in (1, 7):
                    w3.set(x, y, z, "minecraft:polished_blackstone_bricks")
    # Upper lookout floor (y=4) with unobstructed stair ascent along z=2 (landing x=6, y=4)
    w3.fill(1, 4, 1, 7, 4, 7, "minecraft:polished_blackstone_bricks")
    w3.build_straight_staircase(2, 2, 4, 1, "minecraft:polished_blackstone_brick_stairs", "minecraft:polished_blackstone_bricks", headroom=4)
    # Parapet wall & corner posts on y=5..7
    for x in range(1, 8):
        for z in range(1, 8):
            if x in (1, 7) or z in (1, 7):
                w3.set(x, 5, z, "minecraft:polished_blackstone_brick_wall")
    for px, pz in ((1, 1), (7, 1), (1, 7), (7, 7)):
        w3.pillar(px, 5, 7, pz, "minecraft:gilded_blackstone")
    w3.stepped_vault_roof(0, 0, 8, 8, 8, "minecraft:polished_blackstone_brick_stairs", "minecraft:polished_blackstone_brick_slab", "minecraft:gilded_blackstone", "minecraft:soul_lantern")
    w3.open_arch_portal_z(4, 1, 7, 1, 3, "minecraft:polished_blackstone_brick_stairs", "minecraft:chiseled_polished_blackstone", "minecraft:polished_blackstone_bricks")
    w3.open_arch_portal_z(4, 1, 8, 1, 3, "minecraft:polished_blackstone_brick_stairs", "minecraft:polished_blackstone_bricks", "minecraft:polished_blackstone_bricks")
    w3.jigsaw(4, 1, 8, "south_up", "canopycavern:cinder_dock", "canopycavern:cinder_entry", "minecraft:empty", "minecraft:air")
    w3.chest(4, 5, 6, "north", "canopycavern:chests/nether_bastion_supply")
    w3.soul_lantern(4, 5, 4, hanging=False)
    w3.validate_extra(f"{sid}/gilded_watch_turret", max_guards=2)
    w3.save(f"{sid}/gilded_watch_turret.nbt")

    # --- Fallback Cap (5x6x3) ---
    cap = dsh.ExtradimensionalBuilder(5, 6, 3)
    cap.fill(0, 0, 0, 4, 0, 2, "minecraft:polished_blackstone_bricks")
    for x in range(0, 5):
        for y in range(1, 5):
            cap.set(x, y, 1, "minecraft:polished_blackstone_bricks")
            cap.set(x, y, 0, "minecraft:chiseled_polished_blackstone" if x in (0, 4) else "minecraft:polished_blackstone_bricks")
    cap.grate(2, 2, 1, "minecraft:waxed_copper_grate")
    cap.grate(2, 3, 1, "minecraft:waxed_copper_grate")
    cap.set(2, 4, 2, "minecraft:chiseled_polished_blackstone")
    cap.soul_lantern(2, 3, 2, hanging=True)
    cap.slab(2, 5, 1, "minecraft:polished_blackstone_brick_slab", "bottom")
    cap.jigsaw(2, 1, 2, "south_up", "canopycavern:cinder_dock", "canopycavern:cinder_entry", "minecraft:empty", "minecraft:air")
    cap.validate_extra(f"{sid}/buttress_cap", max_guards=0)
    cap.save(f"{sid}/buttress_cap.nbt")

    dsh.write_jigsaw_pool(f"{sid}/start", [(f"{pool_prefix}/sanctum_core", 1, "rigid")])
    dsh.write_jigsaw_pool(
        f"{sid}/branches",
        [
            (f"{pool_prefix}/treasury_wing", 3, "rigid"),
            (f"{pool_prefix}/crimson_dormitory", 2, "rigid"),
            (f"{pool_prefix}/gilded_watch_turret", 2, "rigid"),
            (f"{pool_prefix}/buttress_cap", 1, "rigid"),
        ],
        fallback=f"{pool_prefix}/caps",
    )
    dsh.write_jigsaw_pool(f"{sid}/caps", [(f"{pool_prefix}/buttress_cap", 1, "rigid")])

    dsh.write_loot_table("nether_bastion_vault", [
        {"rolls": {"type": "minecraft:uniform", "min": 2, "max": 3}, "entries": [
            dsh.loot_item("minecraft:gold_ingot", 10, 4, 10),
            dsh.loot_item("minecraft:gilded_blackstone", 6, 3, 8),
            dsh.loot_item("minecraft:netherite_scrap", 4, 1, 2),
            dsh.loot_item("minecraft:ancient_debris", 1, 1, 1),
            dsh.loot_item("minecraft:diamond", 4, 2, 5),
            dsh.loot_item("minecraft:golden_carrot", 6, 4, 9),
        ]},
        {"rolls": 1, "entries": [
            dsh.loot_item("minecraft:potion", 4, 1, 1, potion_id="minecraft:fire_resistance"),
            dsh.loot_item("minecraft:crossbow", 3, enchant_levels=(16, 28)),
            dsh.loot_item("minecraft:golden_sword", 2, enchant_levels=(18, 30)),
            dsh.loot_item("minecraft:spectral_arrow", 5, 6, 14),
        ]},
    ])
    dsh.write_loot_table("nether_bastion_supply", [
        {"rolls": {"type": "minecraft:uniform", "min": 2, "max": 4}, "entries": [
            dsh.loot_item("minecraft:quartz", 8, 4, 12),
            dsh.loot_item("minecraft:obsidian", 5, 2, 5),
            dsh.loot_item("minecraft:gold_nugget", 8, 6, 16),
            dsh.loot_item("minecraft:cooked_porkchop", 7, 3, 7),
            dsh.loot_item("minecraft:magma_cream", 4, 1, 4),
            dsh.loot_item("minecraft:potion", 2, 1, 1, potion_id="minecraft:fire_resistance"),
        ]},
    ])

    _write_nether_structure(
        sid,
        ["minecraft:nether_wastes", "minecraft:crimson_forest"],
        spacing=34,
        separation=14,
        salt=8142107,
        cavern_guard={
            "min_floor_y": 34,
            "max_floor_y": 94,
            "min_headroom": 16,
            "max_ceiling_y": 118,
            "core_probe_radius": 7,
            "max_core_relief": 7,
            "max_piece_relief": 8,
            "max_piece_embed": 5,
            "max_foundation_depth": 16,
            "min_rigid_pieces": 2,
            "foundation_block": "minecraft:polished_blackstone_bricks",
        },
    )


# ===========================================================================
# 2. SOUL CATACOMB RELIQUARY (soul_sand_valley)
# ===========================================================================
def build_soul_catacomb_reliquary():
    sid = "soul_catacomb_reliquary"
    pool_prefix = f"canopycavern:{sid}"

    # --- Nave Start Piece (15x18x15) ---
    b = dsh.ExtradimensionalBuilder(15, 18, 15)
    b.chamfered_rect(0, 0, 14, 14, 0, "minecraft:nether_bricks")
    for x in range(2, 13):
        for z in range(2, 13):
            blk = "minecraft:chiseled_nether_bricks" if (x + z) % 4 == 0 else "minecraft:nether_bricks"
            b.set(x, 0, z, blk)

    for y in range(1, 8):
        for x in range(1, 14):
            for z in range(1, 14):
                if (x in (1, 13)) and (z in (1, 13)):
                    continue
                if x in (1, 13) or z in (1, 13):
                    if y in (4, 5) and (x in (4, 10) or z in (4, 10)):
                        b.set(x, y, z, "minecraft:iron_bars")
                    elif x in (3, 11) or z in (3, 11):
                        b.set(x, y, z, ("minecraft:bone_block", {"axis": "y"}))
                    else:
                        blk = "minecraft:cracked_nether_bricks" if (x + y + z) % 5 == 0 else "minecraft:nether_bricks"
                        b.set(x, y, z, blk)

    for px, pz in ((2, 2), (12, 2), (2, 12), (12, 12)):
        b.pillar(px, 0, 8, pz, "minecraft:bone_block", axis="y")
        b.set(px, 4, pz, "minecraft:chiseled_nether_bricks")
    b.stepped_vault_roof(0, 0, 14, 14, 8, "minecraft:nether_brick_stairs", "minecraft:nether_brick_slab", "minecraft:nether_bricks", "minecraft:soul_lantern")

    # Central Soul Campfire warm hearth inset in protective rim (clean 3-block clearance from mobs!)
    b.soul_campfire_hearth(7, 1, 7)
    for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        b.slab(7 + dx, 1, 7 + dz, "minecraft:nether_brick_slab", "bottom")
    b.iron_chain_lantern(7, 8, 7, chain_len=2)

    # Reliquary altar at north nave
    b.chest(7, 1, 2, "south", "canopycavern:chests/nether_soul_reliquary")
    b.set(5, 1, 2, ("minecraft:lectern", {"facing": "south", "has_book": "false", "powered": "false"}))
    b.set(9, 1, 2, ("minecraft:brewing_stand", {"has_bottle_0": "false", "has_bottle_1": "false", "has_bottle_2": "false"}))
    b.soul_lantern(4, 1, 2, hanging=False)
    b.soul_lantern(10, 1, 2, hanging=False)

    # Entrance & 3 outgoing sockets
    b.open_arch_portal_z(7, 1, 13, 1, 4, "minecraft:nether_brick_stairs", "minecraft:chiseled_nether_bricks", "minecraft:nether_bricks")
    b.open_arch_portal_z(7, 1, 14, 1, 4, "minecraft:nether_brick_stairs", "minecraft:nether_bricks", "minecraft:nether_bricks")

    b.open_arch_portal_x(1, 1, 7, 1, 3, "minecraft:nether_brick_stairs", "minecraft:chiseled_nether_bricks", "minecraft:nether_bricks")
    b.open_arch_portal_x(0, 1, 7, 1, 3, "minecraft:nether_brick_stairs", "minecraft:nether_bricks", "minecraft:nether_bricks")
    b.jigsaw(0, 1, 7, "west_up", "canopycavern:soul_entry", "canopycavern:soul_dock", f"{pool_prefix}/branches", "minecraft:air")

    b.open_arch_portal_x(13, 1, 7, 1, 3, "minecraft:nether_brick_stairs", "minecraft:chiseled_nether_bricks", "minecraft:nether_bricks")
    b.open_arch_portal_x(14, 1, 7, 1, 3, "minecraft:nether_brick_stairs", "minecraft:nether_bricks", "minecraft:nether_bricks")
    b.jigsaw(14, 1, 7, "east_up", "canopycavern:soul_entry", "canopycavern:soul_dock", f"{pool_prefix}/branches", "minecraft:air")

    b.open_arch_portal_z(7, 1, 1, 1, 3, "minecraft:nether_brick_stairs", "minecraft:chiseled_nether_bricks", "minecraft:nether_bricks")
    b.open_arch_portal_z(7, 1, 0, 1, 3, "minecraft:nether_brick_stairs", "minecraft:nether_bricks", "minecraft:nether_bricks")
    b.jigsaw(7, 1, 0, "north_up", "canopycavern:soul_entry", "canopycavern:soul_dock", f"{pool_prefix}/branches", "minecraft:air")

    # 2 Wither Skeleton crypt sentries safely away from campfire
    b.add_wither_skeleton(3, 1, 10)
    b.add_wither_skeleton(11, 1, 10)

    b.validate_extra(f"{sid}/nave", max_guards=3)
    b.save(f"{sid}/nave.nbt")

    # --- Branch 1: Ossuary Alcove (9x13x9) ---
    o1 = dsh.ExtradimensionalBuilder(9, 13, 9)
    o1.chamfered_rect(0, 0, 8, 8, 0, "minecraft:nether_bricks")
    for y in range(1, 6):
        for x in range(1, 8):
            for z in range(1, 8):
                if x in (1, 7) or z in (1, 7):
                    o1.set(x, y, z, ("minecraft:bone_block", {"axis": "y"}) if (x in (2, 6) or z in (2, 6)) else "minecraft:nether_bricks")
    o1.stepped_vault_roof(0, 0, 8, 8, 6, "minecraft:nether_brick_stairs", "minecraft:nether_brick_slab", "minecraft:chiseled_nether_bricks", "minecraft:soul_lantern")
    o1.open_arch_portal_z(4, 1, 7, 1, 3, "minecraft:nether_brick_stairs", "minecraft:chiseled_nether_bricks", "minecraft:nether_bricks")
    o1.open_arch_portal_z(4, 1, 8, 1, 3, "minecraft:nether_brick_stairs", "minecraft:nether_bricks", "minecraft:nether_bricks")
    o1.jigsaw(4, 1, 8, "south_up", "canopycavern:soul_dock", "canopycavern:soul_entry", "minecraft:empty", "minecraft:air")
    o1.chest(4, 1, 2, "south", "canopycavern:chests/nether_soul_reliquary")
    o1.soul_lantern(3, 1, 2, hanging=False)
    o1.add_wither_skeleton(5, 1, 4)
    o1.validate_extra(f"{sid}/ossuary_alcove", max_guards=2)
    o1.save(f"{sid}/ossuary_alcove.nbt")

    # --- Branch 2: Alchemist Chantry (9x13x9) ---
    o2 = dsh.ExtradimensionalBuilder(9, 13, 9)
    o2.chamfered_rect(0, 0, 8, 8, 0, "minecraft:nether_bricks")
    o2.fill(2, 0, 2, 6, 0, 6, "minecraft:soul_soil")
    o2.fill(3, 0, 3, 5, 0, 5, "minecraft:polished_blackstone_bricks")
    for y in range(1, 6):
        for x in range(1, 8):
            for z in range(1, 8):
                if x in (1, 7) or z in (1, 7):
                    o2.set(x, y, z, "minecraft:iron_bars" if (y == 3 and (x == 4 or z == 4)) else "minecraft:nether_bricks")
    o2.stepped_vault_roof(0, 0, 8, 8, 6, "minecraft:nether_brick_stairs", "minecraft:nether_brick_slab", "minecraft:nether_bricks", "minecraft:shroomlight")
    o2.open_arch_portal_z(4, 1, 7, 1, 3, "minecraft:nether_brick_stairs", "minecraft:chiseled_nether_bricks", "minecraft:nether_bricks")
    o2.open_arch_portal_z(4, 1, 8, 1, 3, "minecraft:nether_brick_stairs", "minecraft:nether_bricks", "minecraft:nether_bricks")
    o2.jigsaw(4, 1, 8, "south_up", "canopycavern:soul_dock", "canopycavern:soul_entry", "minecraft:empty", "minecraft:air")
    o2.chest(2, 1, 2, "east", "canopycavern:chests/nether_soul_reliquary")
    o2.set(6, 1, 2, ("minecraft:brewing_stand", {"has_bottle_0": "false", "has_bottle_1": "false", "has_bottle_2": "false"}))
    o2.iron_chain_lantern(4, 6, 4, chain_len=1)
    o2.validate_extra(f"{sid}/alchemist_chantry", max_guards=1)
    o2.save(f"{sid}/alchemist_chantry.nbt")

    # --- Branch 3: Spire Belfry (9x15x9) ---
    o3 = dsh.ExtradimensionalBuilder(9, 15, 9)
    o3.chamfered_rect(0, 0, 8, 8, 0, "minecraft:nether_bricks")
    for y in range(1, 5):
        for x in range(1, 8):
            for z in range(1, 8):
                if x in (1, 7) or z in (1, 7):
                    o3.set(x, y, z, "minecraft:nether_bricks")
    o3.fill(1, 4, 1, 7, 4, 7, "minecraft:nether_bricks")
    o3.build_straight_staircase(2, 2, 4, 1, "minecraft:nether_brick_stairs", "minecraft:nether_bricks", headroom=4)
    for x in range(1, 8):
        for z in range(1, 8):
            if x in (1, 7) or z in (1, 7):
                o3.set(x, 5, z, "minecraft:nether_brick_fence")
    for px, pz in ((1, 1), (7, 1), (1, 7), (7, 7)):
        o3.pillar(px, 5, 7, pz, "minecraft:bone_block", axis="y")
    o3.stepped_vault_roof(0, 0, 8, 8, 8, "minecraft:nether_brick_stairs", "minecraft:nether_brick_slab", "minecraft:chiseled_nether_bricks", "minecraft:soul_lantern")
    o3.open_arch_portal_z(4, 1, 7, 1, 3, "minecraft:nether_brick_stairs", "minecraft:chiseled_nether_bricks", "minecraft:nether_bricks")
    o3.open_arch_portal_z(4, 1, 8, 1, 3, "minecraft:nether_brick_stairs", "minecraft:nether_bricks", "minecraft:nether_bricks")
    o3.jigsaw(4, 1, 8, "south_up", "canopycavern:soul_dock", "canopycavern:soul_entry", "minecraft:empty", "minecraft:air")
    o3.chest(4, 5, 6, "north", "canopycavern:chests/nether_soul_reliquary")
    o3.soul_lantern(4, 5, 4, hanging=False)
    o3.validate_extra(f"{sid}/spire_belfry", max_guards=1)
    o3.save(f"{sid}/spire_belfry.nbt")

    # --- Fallback Cap (5x6x3) ---
    cap = dsh.ExtradimensionalBuilder(5, 6, 3)
    cap.fill(0, 0, 0, 4, 0, 2, "minecraft:nether_bricks")
    for x in range(0, 5):
        for y in range(1, 5):
            cap.set(x, y, 1, "minecraft:nether_bricks")
            cap.set(x, y, 0, "minecraft:bone_block" if x in (0, 4) else "minecraft:nether_bricks")
    cap.set(2, 2, 1, "minecraft:iron_bars")
    cap.set(2, 3, 1, "minecraft:iron_bars")
    cap.set(2, 4, 2, "minecraft:chiseled_nether_bricks")
    cap.soul_lantern(2, 3, 2, hanging=True)
    cap.slab(2, 5, 1, "minecraft:nether_brick_slab", "bottom")
    cap.jigsaw(2, 1, 2, "south_up", "canopycavern:soul_dock", "canopycavern:soul_entry", "minecraft:empty", "minecraft:air")
    cap.validate_extra(f"{sid}/buttress_cap", max_guards=0)
    cap.save(f"{sid}/buttress_cap.nbt")

    dsh.write_jigsaw_pool(f"{sid}/start", [(f"{pool_prefix}/nave", 1, "rigid")])
    dsh.write_jigsaw_pool(
        f"{sid}/branches",
        [
            (f"{pool_prefix}/ossuary_alcove", 3, "rigid"),
            (f"{pool_prefix}/alchemist_chantry", 2, "rigid"),
            (f"{pool_prefix}/spire_belfry", 2, "rigid"),
            (f"{pool_prefix}/buttress_cap", 1, "rigid"),
        ],
        fallback=f"{pool_prefix}/caps",
    )
    dsh.write_jigsaw_pool(f"{sid}/caps", [(f"{pool_prefix}/buttress_cap", 1, "rigid")])

    dsh.write_loot_table("nether_soul_reliquary", [
        {"rolls": {"type": "minecraft:uniform", "min": 2, "max": 4}, "entries": [
            dsh.loot_item("minecraft:bone", 10, 4, 12),
            dsh.loot_item("minecraft:gold_ingot", 8, 3, 7),
            dsh.loot_item("minecraft:diamond", 4, 1, 4),
            dsh.loot_item("minecraft:quartz", 8, 5, 14),
            dsh.loot_item("minecraft:soul_lantern", 5, 2, 5),
            dsh.loot_item("minecraft:wither_rose", 2, 1, 2),
        ]},
        {"rolls": 1, "entries": [
            dsh.loot_item("minecraft:enchanted_book", 4, enchant_levels=(15, 28)),
            dsh.loot_item("minecraft:potion", 4, 1, 1, potion_id="minecraft:fire_resistance"),
            dsh.loot_item("minecraft:iron_sword", 3, enchant_levels=(16, 26)),
        ]},
    ])

    _write_nether_structure(
        sid,
        ["minecraft:soul_sand_valley"],
        spacing=32,
        separation=14,
        salt=8142209,
        cavern_guard={
            "min_floor_y": 34,
            "max_floor_y": 95,
            "min_headroom": 15,
            "max_ceiling_y": 118,
            "core_probe_radius": 6,
            "max_core_relief": 7,
            "max_piece_relief": 8,
            "max_piece_embed": 5,
            "max_foundation_depth": 16,
            "min_rigid_pieces": 2,
            "foundation_block": "minecraft:nether_bricks",
        },
    )


# ===========================================================================
# 3. BASALT THERMAL SPIRE (basalt_deltas)
# ===========================================================================
def build_basalt_thermal_spire():
    sid = "basalt_thermal_spire"
    pool_prefix = f"canopycavern:{sid}"

    # --- Central Spire Keep (13x20x13) ---
    b = dsh.ExtradimensionalBuilder(13, 20, 13)
    b.chamfered_rect(0, 0, 12, 12, 0, "minecraft:basalt")
    b.chamfered_rect(1, 1, 11, 11, 0, "minecraft:polished_basalt")

    # Lower octagonal shell y=1..6
    for y in range(1, 7):
        for x in range(1, 12):
            for z in range(1, 12):
                if (x in (1, 11)) and (z in (1, 11)):
                    continue
                if x in (1, 11) or z in (1, 11):
                    if y in (3, 4) and (x == 6 or z == 6):
                        b.grate(x, y, z, "minecraft:waxed_copper_grate")
                    else:
                        b.set(x, y, z, "minecraft:smooth_basalt" if y % 2 == 0 else "minecraft:polished_basalt")

    # Central glowing thermal core column on ground floor (shroomlight behind copper grates)
    for y in range(1, 6):
        b.set(6, y, 6, "minecraft:shroomlight" if y in (2, 4) else "minecraft:polished_blackstone_bricks")

    # Staircase climbing cleanly from y=1 -> y=6 (landing x=9, y=6)
    b.fill(1, 6, 1, 11, 6, 11, "minecraft:polished_basalt")
    b.chamfered_rect(0, 0, 12, 12, 6, "minecraft:polished_blackstone_bricks")
    b.build_straight_staircase(3, 2, 6, 1, "minecraft:polished_blackstone_brick_stairs", "minecraft:polished_basalt", headroom=4)

    # Upper deck (y=7..10): parapet + corner buttress piers supporting cascading spire crown (y=11..19)
    for x in range(1, 12):
        for z in range(1, 12):
            if (x in (1, 11)) and (z in (1, 11)):
                continue
            if x in (1, 11) or z in (1, 11):
                b.set(x, 7, z, "minecraft:polished_blackstone_wall")
    for px, pz in ((2, 2), (10, 2), (2, 10), (10, 10), (6, 1), (6, 11), (1, 6), (11, 6)):
        b.pillar(px, 7, 10, pz, "minecraft:polished_basalt", axis="y")
    b.stepped_vault_roof(0, 0, 12, 12, 11, "minecraft:polished_blackstone_brick_stairs", "minecraft:polished_blackstone_brick_slab", "minecraft:smooth_basalt", "minecraft:shroomlight")

    # Forge stations & chests (one ground, one upper deck!)
    b.set(3, 1, 3, ("minecraft:blast_furnace", {"facing": "east", "lit": "false"}))
    b.chest(9, 1, 3, "west", "canopycavern:chests/nether_thermal_spire")
    b.chest(6, 7, 10, "north", "canopycavern:chests/nether_thermal_spire")
    b.set(4, 7, 10, ("minecraft:brewing_stand", {"has_bottle_0": "false", "has_bottle_1": "false", "has_bottle_2": "false"}))
    b.soul_lantern(3, 7, 7, hanging=False)
    b.soul_lantern(9, 7, 7, hanging=False)

    # South doorway + West/East viaduct sockets
    b.open_arch_portal_z(6, 1, 11, 1, 4, "minecraft:polished_blackstone_brick_stairs", "minecraft:polished_basalt", "minecraft:smooth_basalt")
    b.open_arch_portal_z(6, 1, 12, 1, 4, "minecraft:polished_blackstone_brick_stairs", "minecraft:basalt", "minecraft:basalt")

    b.open_arch_portal_x(1, 1, 6, 1, 3, "minecraft:polished_blackstone_brick_stairs", "minecraft:polished_basalt", "minecraft:smooth_basalt")
    b.open_arch_portal_x(0, 1, 6, 1, 3, "minecraft:polished_blackstone_brick_stairs", "minecraft:basalt", "minecraft:basalt")
    b.jigsaw(0, 1, 6, "west_up", "canopycavern:basalt_entry", "canopycavern:basalt_dock", f"{pool_prefix}/branches", "minecraft:air")

    b.open_arch_portal_x(11, 1, 6, 1, 3, "minecraft:polished_blackstone_brick_stairs", "minecraft:polished_basalt", "minecraft:smooth_basalt")
    b.open_arch_portal_x(12, 1, 6, 1, 3, "minecraft:polished_blackstone_brick_stairs", "minecraft:basalt", "minecraft:basalt")
    b.jigsaw(12, 1, 6, "east_up", "canopycavern:basalt_entry", "canopycavern:basalt_dock", f"{pool_prefix}/branches", "minecraft:air")

    # 1 Piglin lobby sentry + 1 Blaze hovering cleanly on spacious upper forge balcony
    b.add_piglin_guard(4, 1, 8)
    b.add_blaze_guard(6, 7, 6)

    b.validate_extra(f"{sid}/keep", max_guards=3)
    b.save(f"{sid}/keep.nbt")

    # --- Branch 1: Cantilever Bridge Wing (9x13x9) ---
    r1 = dsh.ExtradimensionalBuilder(9, 13, 9)
    r1.chamfered_rect(0, 0, 8, 8, 0, "minecraft:basalt")
    for y in range(1, 6):
        for x in range(1, 8):
            for z in range(1, 8):
                if x in (1, 7) or z in (1, 7):
                    r1.grate(x, y, z, "minecraft:waxed_copper_grate") if (y == 3 and (x == 4 or z == 4)) else r1.set(x, y, z, "minecraft:polished_basalt")
    r1.stepped_vault_roof(0, 0, 8, 8, 6, "minecraft:polished_blackstone_brick_stairs", "minecraft:polished_blackstone_brick_slab", "minecraft:smooth_basalt", "minecraft:shroomlight")
    r1.open_arch_portal_z(4, 1, 7, 1, 3, "minecraft:polished_blackstone_brick_stairs", "minecraft:polished_basalt", "minecraft:smooth_basalt")
    r1.open_arch_portal_z(4, 1, 8, 1, 3, "minecraft:polished_blackstone_brick_stairs", "minecraft:basalt", "minecraft:basalt")
    r1.jigsaw(4, 1, 8, "south_up", "canopycavern:basalt_dock", "canopycavern:basalt_entry", "minecraft:empty", "minecraft:air")
    r1.chest(4, 1, 2, "south", "canopycavern:chests/nether_thermal_spire")
    r1.soul_lantern(3, 1, 2, hanging=False)
    r1.add_wither_skeleton(5, 1, 5)
    r1.validate_extra(f"{sid}/cantilever_bridge", max_guards=2)
    r1.save(f"{sid}/cantilever_bridge.nbt")

    # --- Branch 2: Cooling Vent (9x14x9) ---
    r2 = dsh.ExtradimensionalBuilder(9, 14, 9)
    r2.chamfered_rect(0, 0, 8, 8, 0, "minecraft:basalt")
    for y in range(1, 7):
        for x in range(1, 8):
            for z in range(1, 8):
                if x in (1, 7) or z in (1, 7):
                    r2.set(x, y, z, "minecraft:smooth_basalt")
    r2.stepped_vault_roof(0, 0, 8, 8, 7, "minecraft:polished_blackstone_brick_stairs", "minecraft:polished_blackstone_brick_slab", "minecraft:basalt", "minecraft:shroomlight")
    r2.open_arch_portal_z(4, 1, 7, 1, 3, "minecraft:polished_blackstone_brick_stairs", "minecraft:polished_basalt", "minecraft:smooth_basalt")
    r2.open_arch_portal_z(4, 1, 8, 1, 3, "minecraft:polished_blackstone_brick_stairs", "minecraft:basalt", "minecraft:basalt")
    r2.jigsaw(4, 1, 8, "south_up", "canopycavern:basalt_dock", "canopycavern:basalt_entry", "minecraft:empty", "minecraft:air")
    r2.chest(2, 1, 4, "east", "canopycavern:chests/nether_thermal_spire")
    r2.iron_chain_lantern(4, 7, 4, chain_len=2)
    r2.validate_extra(f"{sid}/cooling_vent", max_guards=1)
    r2.save(f"{sid}/cooling_vent.nbt")

    # --- Fallback Cap (5x7x3) ---
    cap = dsh.ExtradimensionalBuilder(5, 7, 3)
    cap.fill(0, 0, 0, 4, 0, 2, "minecraft:basalt")
    for x in range(0, 5):
        for y in range(1, 5):
            cap.set(x, y, 1, "minecraft:polished_basalt")
            cap.set(x, y, 0, "minecraft:smooth_basalt")
    cap.grate(2, 2, 1, "minecraft:waxed_copper_grate")
    cap.set(2, 3, 1, "minecraft:shroomlight")
    cap.slab(2, 5, 1, "minecraft:polished_blackstone_brick_slab", "bottom")
    cap.set(2, 4, 2, "minecraft:smooth_basalt")
    cap.soul_lantern(2, 3, 2, hanging=True)
    cap.jigsaw(2, 1, 2, "south_up", "canopycavern:basalt_dock", "canopycavern:basalt_entry", "minecraft:empty", "minecraft:air")
    cap.validate_extra(f"{sid}/pillar_cap", max_guards=0)
    cap.save(f"{sid}/pillar_cap.nbt")

    dsh.write_jigsaw_pool(f"{sid}/start", [(f"{pool_prefix}/keep", 1, "rigid")])
    dsh.write_jigsaw_pool(
        f"{sid}/branches",
        [
            (f"{pool_prefix}/cantilever_bridge", 3, "rigid"),
            (f"{pool_prefix}/cooling_vent", 2, "rigid"),
            (f"{pool_prefix}/pillar_cap", 1, "rigid"),
        ],
        fallback=f"{pool_prefix}/caps",
    )
    dsh.write_jigsaw_pool(f"{sid}/caps", [(f"{pool_prefix}/pillar_cap", 1, "rigid")])

    dsh.write_loot_table("nether_thermal_spire", [
        {"rolls": {"type": "minecraft:uniform", "min": 2, "max": 4}, "entries": [
            dsh.loot_item("minecraft:blaze_rod", 6, 1, 3),
            dsh.loot_item("minecraft:gold_ingot", 8, 3, 8),
            dsh.loot_item("minecraft:magma_cream", 7, 2, 5),
            dsh.loot_item("minecraft:polished_basalt", 8, 8, 16),
            dsh.loot_item("minecraft:netherite_scrap", 2, 1, 1),
            dsh.loot_item("minecraft:diamond", 3, 1, 3),
        ]},
        {"rolls": 1, "entries": [
            dsh.loot_item("minecraft:potion", 5, 1, 1, potion_id="minecraft:fire_resistance"),
            dsh.loot_item("minecraft:iron_pickaxe", 3, enchant_levels=(15, 25)),
            dsh.loot_item("canopycavern:glow_lantern", 2, 1, 1),
        ]},
    ])

    _write_nether_structure(
        sid,
        ["minecraft:basalt_deltas"],
        spacing=30,
        separation=12,
        salt=8142311,
        cavern_guard={
            "min_floor_y": 33,
            "max_floor_y": 94,
            "min_headroom": 18,
            "max_ceiling_y": 118,
            "core_probe_radius": 5,
            "max_core_relief": 8,
            "max_piece_relief": 9,
            "max_piece_embed": 5,
            "max_foundation_depth": 18,
            "min_rigid_pieces": 1,
            "foundation_block": "minecraft:basalt",
        },
    )


def build_all():
    build_cinder_vault_bastion()
    build_soul_catacomb_reliquary()
    build_basalt_thermal_spire()
    print("Generated all 3 Nether cavern Jigsaw structures, pools, tags, sets, and loot tables.")


if __name__ == "__main__":
    build_all()
