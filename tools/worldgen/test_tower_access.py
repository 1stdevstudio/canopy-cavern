import unittest
from unittest.mock import patch

import generate_v03_structures as generator


class TowerAccessTest(unittest.TestCase):
    def test_watchtower_ladder_reaches_roof_with_solid_backing(self):
        templates = {}
        with patch.object(generator.StructureBuilder, "save",
                          lambda builder, name: templates.update({name: builder})), patch.object(generator, "write_json"):
            generator.build_peak_watchtower_ruin()
        grid = templates["peak_watchtower_ruin.nbt"].grid
        for y in range(2, 12):
            self.assertEqual("minecraft:ladder", grid[8, y, 8][0], y)
            self.assertEqual("minecraft:stone_bricks", grid[9, y, 8][0], y)
        for y in (12, 13):
            self.assertEqual("minecraft:air", grid[8, y, 8][0], y)
