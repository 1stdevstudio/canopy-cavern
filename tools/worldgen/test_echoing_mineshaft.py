import gzip
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import generate_v03_structures as legacy

DATA = Path(__file__).resolve().parents[2] / "src/main/resources/data/canopycavern"
FAMILY = "echoing_mineshaft_hub"


def block(piece, x, y, z):
    return piece.grid.get((x, y, z), ("minecraft:structure_void", ()))[0]


class EchoingMineshaftTest(unittest.TestCase):
    def test_new_pools_preserve_legacy_assets_and_use_new_geometry(self):
        expected = {"start": "ore_exchange", "tunnels": "haulage_gallery", "caps": "ore_vault"}
        for name, piece in expected.items():
            pool = json.loads((DATA / f"worldgen/template_pool/{FAMILY}/{name}.json").read_text())
            self.assertEqual(f"canopycavern:{FAMILY}/{piece}", pool["elements"][0]["element"]["location"])
            self.assertTrue((DATA / f"structure/{FAMILY}/{piece}.nbt").is_file())
        for old in (FAMILY, "echoing_mineshaft_tunnel", "echoing_mineshaft_vault"):
            self.assertTrue((DATA / f"structure/{old}.nbt").is_file())

    def test_track_and_upper_gallery_remain_accessible(self):
        from generate_echoing_mineshaft import build_exchange, build_gallery

        exchange = build_exchange()
        for x, z, orientation in (
            (0, 13, "west_up"), (26, 13, "east_up"), (13, 0, "north_up"), (13, 26, "south_up"),
        ):
            self.assertEqual("minecraft:rail", block(exchange, x, 1, z))
            connector, state = exchange.grid[x, 2, z]
            self.assertEqual("minecraft:jigsaw", connector)
            self.assertEqual(orientation, dict(state)["orientation"])
            self.assertEqual("minecraft:air", block(exchange, x, 3, z))
        for x in (7, 8):
            for y, z in ((1, 9), (2, 8), (3, 7)):
                self.assertEqual("minecraft:dark_oak_stairs", block(exchange, x, y, z))
                self.assertEqual("minecraft:air", block(exchange, x, y + 1, z))
                self.assertEqual("minecraft:air", block(exchange, x, y + 2, z))
            self.assertEqual("minecraft:dark_oak_planks", block(exchange, x, 3, 6))
            self.assertEqual("minecraft:air", block(exchange, x, 4, 6))

        gallery = build_gallery()
        for piece in (exchange, gallery):
            rails = [pos for pos, (material, _) in piece.grid.items() if material == "minecraft:rail"]
            self.assertGreater(len(rails), 10)
            for x, y, z in rails:
                self.assertNotIn(block(piece, x, y - 1, z), {"minecraft:air", "minecraft:structure_void"})
        for x in range(13):
            self.assertEqual("minecraft:rail", block(gallery, x, 1, 3))
        vault_connector = gallery.block_nbts[(6, 2, 6)]
        self.assertEqual(f"canopycavern:{FAMILY}/caps", vault_connector["pool"])

    def test_checked_in_templates_match_generator(self):
        from generate_echoing_mineshaft import TEMPLATES

        with TemporaryDirectory() as directory:
            output = Path(directory)
            with patch.object(legacy, "STRUCT_DIR", output):
                for name, build in TEMPLATES.items():
                    build().save(name)
                    actual = gzip.decompress((output / name).read_bytes())
                    expected = gzip.decompress((DATA / "structure" / name).read_bytes())
                    self.assertEqual(expected, actual, name)
