import json
import unittest
from pathlib import Path
from zipfile import ZipFile

from generate_v04_ocean_and_villages import THEMES, VANILLA_JAR, v3


class ZombieVillageTest(unittest.TestCase):
    def test_all_five_themes_keep_rare_weights_and_route_to_new_ruins(self):
        root = Path(v3.STRUCT_DIR).parents[1]
        pools = root / "minecraft/worldgen/template_pool/village"
        with ZipFile(VANILLA_JAR) as vanilla:
            for theme in THEMES:
                with self.subTest(theme=theme):
                    path = f"{theme}/town_centers.json"
                    current = json.loads((pools / path).read_text())
                    original = json.loads(vanilla.read(f"data/minecraft/worldgen/template_pool/village/{path}"))
                    rare_weight = sum(row["weight"] for row in original["elements"]
                                      if "/zombie/" in row["element"].get("location", ""))
                    zombie = [row for row in current["elements"]
                              if "/zombie/" in row["element"].get("location", "")]
                    self.assertEqual(rare_weight, sum(row["weight"] for row in zombie))
                    self.assertEqual(1, len(zombie))
                    self.assertEqual(f"canopycavern:vanilla_revamp/{theme}/zombie/ruined_plaza",
                                     zombie[0]["element"]["location"])
                    self.assertTrue((Path(v3.STRUCT_DIR) / f"vanilla_revamp/{theme}/zombie/ruined_plaza.nbt").exists())
                    self.assertTrue(any(row["element"].get("location") ==
                                        f"canopycavern:vanilla_revamp/{theme}/grand_town_center"
                                        for row in current["elements"]))

                    houses_path = f"{theme}/zombie/houses.json"
                    current_houses = json.loads((pools / houses_path).read_text())
                    original_houses = json.loads(vanilla.read(f"data/minecraft/worldgen/template_pool/village/{houses_path}"))
                    self.assertEqual(original_houses["fallback"], current_houses["fallback"])
                    self.assertEqual(sum(row["weight"] for row in original_houses["elements"]),
                                     sum(row["weight"] for row in current_houses["elements"]))
                    for row in current_houses["elements"]:
                        location = row["element"].get("location")
                        if location:
                            self.assertTrue(location.startswith(f"canopycavern:vanilla_revamp/{theme}/zombie/"))
                            self.assertTrue((Path(v3.STRUCT_DIR) / (location.split(":")[1] + ".nbt")).exists())

    def test_connectors_route_only_to_zombie_streets_and_villagers(self):
        from generate_zombie_villages import build_cottage, build_plaza

        for theme, palette in THEMES.items():
            with self.subTest(theme=theme):
                plaza = build_plaza(theme, palette)
                street = f"minecraft:village/{theme}/zombie/streets"
                residents = f"minecraft:village/{theme}/zombie/villagers"
                connectors = [data for data in plaza.block_nbts.values() if data["id"] == "minecraft:jigsaw"]
                self.assertEqual(4, sum(data["pool"] == street and data["name"] == "minecraft:street"
                                        for data in connectors))
                self.assertEqual(2, sum(data["pool"] == residents for data in connectors))
                for index in range(3):
                    cottage = build_cottage(theme, palette, index)
                    entrance = cottage.block_nbts[4, 1, 0]
                    self.assertEqual("minecraft:building_entrance", entrance["name"])
                    self.assertEqual("north_up", dict(cottage.grid[4, 1, 0][1])["orientation"])
                    self.assertEqual(residents, cottage.block_nbts[4, 0, 4]["pool"])
                    self.assertFalse(cottage.entities)
