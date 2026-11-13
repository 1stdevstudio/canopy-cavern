import unittest
from unittest.mock import patch

from generate_v04_ocean_and_villages import V4StructureBuilder, build_reef_lighthouse_keep


class ReefFoundationTest(unittest.TestCase):
    def test_foundations_reach_below_the_pieces_without_moving_the_dock(self):
        pieces = {}

        def collect(builder, path):
            pieces[path.rsplit("/", 1)[-1]] = builder

        with patch.object(V4StructureBuilder, "save", collect):
            build_reef_lighthouse_keep()

        for name, support, connector in (
            ("island_keep_anchored.nbt", (13, 12), (13, 26)),
            ("sunken_flagship_wreck_anchored.nbt", (8, 14), (8, 0)),
        ):
            with self.subTest(piece=name):
                self.assertIn(name, pieces)
                piece = pieces[name]
                x, z = support
                # Solid rock reaches 48 blocks below the previous footprint.
                for y in range(48):
                    self.assertIn(piece.grid[x, y, z][0], ("minecraft:tuff", "minecraft:andesite"))
                dock_x, dock_z = connector
                self.assertEqual(
                    "canopycavern:harbor_bay",
                    piece.block_nbts[dock_x, 69, dock_z]["name"],
                )
                self.assertLessEqual(piece.sy, 128)
                self.assertNotIn((0, 0, 0), piece.grid)
