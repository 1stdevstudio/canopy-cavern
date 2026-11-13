from collections import deque
import gzip
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from generate_mining_city_levels import (
    ASSET_ROOT, ASSET_NAMES, LEVELS, ENTRY_Z, build_levels, v3,
)

AIR = "minecraft:air"
WATER = "minecraft:water"


class MiningCityLevelsTest(unittest.TestCase):
    def test_level_entries_reach_all_chests_without_digging(self):
        for name, builder in build_levels().items():
            with self.subTest(level=name):
                self.assertEqual(LEVELS[name], (builder.sx, builder.sy, builder.sz))
                for z in range(ENTRY_Z - 1, ENTRY_Z + 2):
                    self.assertNotIn(builder.grid[0, 0, z][0], (AIR, "minecraft:structure_void"))
                    for y in (1, 2, 3):
                        self.assertEqual(AIR, builder.grid[0, y, z][0])

                def walkable(x, z):
                    floor = builder.grid.get((x, 0, z), ("",))[0]
                    return floor not in ("", AIR, WATER, "minecraft:structure_void") and all(
                        builder.grid.get((x, y, z), ("",))[0] == AIR for y in (1, 2))

                seen = {(0, ENTRY_Z)}
                pending = deque(seen)
                while pending:
                    x, z = pending.popleft()
                    for point in ((x+1,z),(x-1,z),(x,z+1),(x,z-1)):
                        if point not in seen and walkable(*point):
                            seen.add(point)
                            pending.append(point)
                chests = [pos for pos, nbt in builder.block_nbts.items() if "LootTable" in nbt]
                self.assertTrue(chests)
                for x, y, z in chests:
                    self.assertEqual(1, y)
                    self.assertTrue({(x+1,z),(x-1,z),(x,z+1),(x,z-1)} & seen, (x, y, z))
                    self.assertEqual(AIR, builder.grid[x, y+1, z][0])

    def test_pump_water_is_contained_by_full_blocks(self):
        industry = build_levels()["industry"]
        water = {pos for pos, (block, _) in industry.grid.items() if block == WATER}
        self.assertGreaterEqual(len(water), 8)
        for x, y, z in water:
            for point in ((x-1,y,z),(x+1,y,z),(x,y,z-1),(x,y,z+1),(x,y-1,z)):
                block = industry.grid.get(point, ("",))[0]
                self.assertIn(block, (WATER, "minecraft:deepslate_bricks", "minecraft:glass"))

    def test_lower_levels_are_sealed_except_for_shaft_connections(self):
        allowed = {(0, y, z) for y in range(1, 4) for z in range(ENTRY_Z - 1, ENTRY_Z + 2)}
        levels = build_levels()
        for name in ("industry", "excavation"):
            builder = levels[name]
            builder.verify_watertight(name, [(1, 1, ENTRY_Z)], allowed)

    def test_rails_and_hoist_have_support(self):
        levels = build_levels()
        for name, builder in levels.items():
            with self.subTest(level=name):
                rails = [(x, y, z) for (x, y, z), (block, _) in builder.grid.items()
                         if block == "minecraft:rail"]
                self.assertTrue(rails)
                for x, y, z in rails:
                    self.assertTrue(builder._is_full_face_solid(builder.grid[x, y - 1, z][0]))
        for x in range(2, 9):
            self.assertTrue(levels["surface"]._is_full_face_solid(levels["surface"].grid[x, 8, 12][0]))

    def test_runtime_assets_match_generator(self):
        original = v3.STRUCT_DIR
        with TemporaryDirectory() as tmp, patch.object(v3, "STRUCT_DIR", Path(tmp)):
            for name, builder in build_levels().items():
                asset = f"{ASSET_ROOT}/{ASSET_NAMES.get(name, name)}.nbt"
                builder.save(asset)
                self.assertEqual(gzip.decompress((original / asset).read_bytes()),
                                 gzip.decompress((Path(tmp) / asset).read_bytes()), asset)


    def test_industrial_district_has_distinct_workshop_and_dispatch_pavilions(self):
        site = build_levels()["industry"]
        for x, y, z, block in (
            (4, 1, 4, "minecraft:polished_deepslate"),
            (5, 5, 7, "minecraft:deepslate_tile_stairs"),
            (14, 1, 20, "minecraft:spruce_planks"),
            (18, 4, 21, "minecraft:spruce_stairs"),
            (16, 1, 20, "minecraft:cartography_table"),
        ):
            self.assertEqual(block, site.grid[x, y, z][0], (x, y, z))

    def test_excavation_has_a_survey_hut_and_fractured_crystal_face(self):
        site = build_levels()["excavation"]
        self.assertEqual("minecraft:lectern", site.grid[21, 1, 19][0])
        self.assertEqual("minecraft:dark_oak_stairs", site.grid[19, 4, 18][0])
        for x, z in ((21, 5), (22, 5), (23, 5), (24, 6), (25, 7)):
            self.assertEqual("minecraft:amethyst_block", site.grid[x, 2, z][0])
        self.assertEqual("minecraft:stonecutter", site.grid[20, 1, 8][0])


if __name__ == "__main__":
    unittest.main()

class SurfacePortalTest(unittest.TestCase):
    def test_portal_has_a_clear_approach_and_marked_stone_arch(self):
        from generate_mining_city_levels import surface
        site = surface()
        for z in (11, 12, 13):
            self.assertEqual("minecraft:air", site.grid[3, 1, z][0])
            self.assertEqual("minecraft:polished_deepslate", site.grid[0, 5, z][0])
        for z in (10, 14):
            self.assertEqual("minecraft:lantern", site.grid[1, 3, z][0])

    def test_surface_rail_links_the_distant_sorting_yard(self):
        from generate_mining_city_levels import surface
        site = surface()
        self.assertGreaterEqual(site.sx, 85)
        for x in range(11, 85):
            self.assertEqual("minecraft:rail", site.grid[x, 1, 10][0])
            self.assertEqual(AIR, site.grid[x, 1, 12][0])
        self.assertEqual("minecraft:lantern", site.grid[75, 4, 13][0])
