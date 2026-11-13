import gzip
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class FrontierOutpostTest(unittest.TestCase):
    def test_ladder_reaches_decks_and_caged_golem_has_full_clearance(self):
        from generate_frontier_outpost import ASSET, LOOT, build_stockade, v3

        stockade = build_stockade()
        self.assertEqual((47, 24, 47), (stockade.sx, stockade.sy, stockade.sz))

        def block(x, y, z):
            return stockade.grid.get((x, y, z), ("minecraft:structure_void", ()))[0]

        for y in range(1, 15):
            self.assertEqual(block(24, y, 24), "minecraft:ladder")
            self.assertEqual(block(25, y, 24), "minecraft:stripped_dark_oak_log")
        for y in (7, 14):
            self.assertEqual(block(23, y, 24), "minecraft:dark_oak_planks")
            for headroom in (y + 1, y + 2):
                self.assertEqual(block(23, headroom, 24), "minecraft:air")
        self.assertEqual(stockade.block_nbts[22, 15, 20]["LootTable"], LOOT)
        self.assertEqual(block(22, 15, 21), "minecraft:air")
        self.assertGreater(sum(b.endswith("_stairs") for b, _ in stockade.grid.values()), 100)

        pillagers = [entity for entity in stockade.entities if entity["nbt"]["id"] == "minecraft:pillager"]
        self.assertEqual(3, len(pillagers))
        for entity in pillagers:
            x, y, z = entity["blockPos"].value
            self.assertEqual(block(x, y, z), "minecraft:air")
            self.assertEqual(block(x, y + 1, z), "minecraft:air")
            self.assertNotIn(block(x, y - 1, z), ("minecraft:air", "minecraft:campfire", "minecraft:structure_void"))

        golem, = [entity for entity in stockade.entities if entity["nbt"]["id"] == "minecraft:iron_golem"]
        x, y, z = golem["blockPos"].value
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                self.assertEqual(block(x + dx, y - 1, z + dz), "minecraft:cobblestone")
                for level in range(y, y + 3):
                    self.assertEqual(block(x + dx, level, z + dz), "minecraft:air")
        for dx, dz in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            self.assertEqual(block(x + dx, y + 1, z + dz), "minecraft:iron_bars")

        asset = Path(v3.STRUCT_DIR) / ASSET
        with tempfile.TemporaryDirectory() as folder, patch.object(v3, "STRUCT_DIR", Path(folder)):
            stockade.save(ASSET)
            self.assertEqual(gzip.decompress(asset.read_bytes()),
                             gzip.decompress((Path(folder) / ASSET).read_bytes()))
