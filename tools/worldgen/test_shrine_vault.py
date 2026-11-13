import unittest

from generate_shrine_vault import build


class ShrineVaultTest(unittest.TestCase):
    def test_vault_rises_above_side_aisles_and_keeps_wing_connectors(self):
        shrine = build()
        grid = shrine.grid
        self.assertEqual("minecraft:air", grid[9, 10, 7][0])
        self.assertEqual("minecraft:deepslate_tiles", grid[9, 13, 7][0])
        self.assertEqual("minecraft:deepslate_tiles", grid[2, 7, 7][0])
        for x in (0, 18):
            self.assertEqual("canopycavern:cavern_shrine/wings", shrine.block_nbts[x, 1, 7]["pool"])
        self.assertEqual(2, sum(data.get("LootTable") == "canopycavern:chests/cavern_shrine"
                                for data in shrine.block_nbts.values()))
