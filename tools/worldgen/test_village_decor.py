import gzip
import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zipfile import ZipFile

import generate_v03_structures as nbt

THEMES = ("plains", "desert", "savanna", "snowy", "taiga")
RESOURCES = nbt.DATA.parent
MINECRAFT_JAR = Path(os.environ.get(
    "MINECRAFT_JAR", str(Path.home() / ".gradle/caches/fabric-loom/26.3/minecraft-common.jar")
))


class VillageDecorTest(unittest.TestCase):
    def test_normal_and_zombie_pools_replace_only_structure_locations(self):
        with ZipFile(MINECRAFT_JAR) as vanilla:
            for theme in THEMES:
                for variant in ("", "zombie/"):
                    path = f"minecraft/worldgen/template_pool/village/{theme}/{variant}decor.json"
                    with self.subTest(pool=path):
                        before = json.loads(vanilla.read("data/" + path))
                        after = json.loads((RESOURCES / path).read_text())
                        for entry in before["elements"]:
                            element = entry["element"]
                            if "location" in element:
                                original = element["location"].split("/")[-1]
                                path_name = f"vanilla_revamp/{theme}/decor/{original}"
                                element["location"] = "canopycavern:" + path_name
                                self.assertTrue((nbt.STRUCT_DIR / (path_name + ".nbt")).is_file())
                        self.assertEqual(before, after)

    def test_all_templates_attach_from_below_and_preserve_lit_campfires(self):
        from generate_village_decor import build_pieces

        pieces = build_pieces()
        self.assertEqual(13, len(pieces))
        for path, piece in pieces.items():
            with self.subTest(piece=path):
                jigsaws = [(pos, value) for pos, value in piece.block_nbts.items()
                           if value["id"] == "minecraft:jigsaw"]
                self.assertEqual(1, len(jigsaws))
                pos, data = jigsaws[0]
                self.assertEqual("down_south", dict(piece.grid[pos][1])["orientation"])
                self.assertEqual("minecraft:bottom", data["name"])
                self.assertEqual("minecraft:bottom", data["target"])
                self.assertEqual("minecraft:empty", data["pool"])
                self.assertEqual("rollable", data["joint"])
                if path.endswith(("taiga_decoration_5.nbt", "taiga_decoration_6.nbt")):
                    fires = [dict(props) for block, props in piece.grid.values()
                             if block == "minecraft:campfire"]
                    self.assertEqual(1, len(fires))
                    self.assertEqual("true", fires[0]["lit"])

    def test_checked_in_nbt_matches_regenerated_templates(self):
        from generate_village_decor import build_pieces

        pieces = build_pieces()
        with TemporaryDirectory() as tmp:
            out = Path(tmp)
            with patch.object(nbt, "STRUCT_DIR", out):
                for name, builder in pieces.items():
                    builder.save(name)
                    expected = gzip.decompress((RESOURCES / "canopycavern/structure" / name).read_bytes())
                    self.assertEqual(expected, gzip.decompress((out / name).read_bytes()), name)

class SnowyLampSilhouetteTest(unittest.TestCase):
    def test_snowy_lamps_have_exposed_lanterns_and_single_center_cap(self):
        from generate_village_decor import build_pieces

        for name, lamp in build_pieces().items():
            if "/snowy/" not in name:
                continue
            self.assertEqual(1, sum(y == 5 for (_, y, _), (block, _) in lamp.grid.items()
                                    if block not in ("minecraft:air", "minecraft:structure_void")))
            for (x, y, z), (block, _) in lamp.grid.items():
                if block == "minecraft:lantern":
                    self.assertEqual("minecraft:spruce_planks", lamp.grid[x, y + 1, z][0])
