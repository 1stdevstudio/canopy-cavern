import json
from collections import Counter
from zipfile import ZipFile
import unittest
from pathlib import Path

import generate_v03_structures as nbt

DATA = Path(nbt.DATA).parent
POOLS = DATA / "minecraft/worldgen/template_pool"


class VanillaOutpostCampsTest(unittest.TestCase):
    def test_outpost_keeps_original_mechanics_and_loads_new_tower(self):
        from generate_vanilla_outpost_camps import OUTPOST_ASSET, build_tower

        pool = json.loads((POOLS / "pillager_outpost/towers.json").read_text())
        self.assertEqual([f"canopycavern:{OUTPOST_ASSET}"],
                         [row["element"]["location"] for row in pool["elements"]])
        self.assertFalse((DATA / "minecraft/worldgen/structure/pillager_outpost.json").exists())
        self.assertTrue((nbt.STRUCT_DIR / f"{OUTPOST_ASSET}.nbt").exists())
        tower = build_tower()
        self.assertEqual("minecraft:entrance", tower.block_nbts[7, 1, 13]["name"])
        self.assertEqual("south_up", dict(tower.grid[7, 1, 13][1])["orientation"])
        self.assertEqual("minecraft:chests/pillager_outpost", tower.block_nbts[8, 15, 10]["LootTable"])
        for y in range(1, 15):
            self.assertEqual("minecraft:ladder", tower.grid[8, y, 7][0])
        for y in (7, 14):
            self.assertEqual("minecraft:dark_oak_planks", tower.grid[7, y, 7][0])
            for step in (1, 2):
                self.assertEqual("minecraft:air", tower.grid[7, y + step, 7][0])
        banners = [data for data in tower.block_nbts.values() if data["id"] == "minecraft:banner"]
        self.assertEqual(8, len(banners))
        self.assertTrue(all(len(data["patterns"].value) == 8 for data in banners))

    def test_all_18_camp_start_and_attachment_pools_keep_loot_and_tree_connections(self):
        from generate_vanilla_outpost_camps import (BIOMES, MINECRAFT_JAR, build_tent, build_campsite,
                                                    read_template, vanilla_template)

        self.assertEqual(18, len(BIOMES))
        for biome, theme in BIOMES.items():
            with self.subTest(biome=biome):
                path = POOLS / f"abandoned_camp/tent/{biome}.json"
                pool = json.loads(path.read_text())
                self.assertEqual(10, sum(row["weight"] for row in pool["elements"]))
                for row in pool["elements"]:
                    location = row["element"]["location"].split(":")[1]
                    self.assertTrue(location.startswith(f"vanilla_revamp/abandoned_camp/{biome}/tent_"))
                    self.assertTrue((nbt.STRUCT_DIR / (location + ".nbt")).exists())
                tent = build_tent(biome, theme, 0)
                ports = [data for data in tent.block_nbts.values() if data["id"] == "minecraft:jigsaw"]
                self.assertIn(f"minecraft:abandoned_camp/camp/{biome}", [data["pool"] for data in ports])
                self.assertTrue(any(data.get("LootTable") == "minecraft:barrels/abandoned_camp_barrel"
                                    for data in tent.block_nbts.values()))
                vanilla_pool = f"data/minecraft/worldgen/template_pool/abandoned_camp/tent/{biome}.json"
                with ZipFile(MINECRAFT_JAR) as vanilla:
                    original = json.loads(vanilla.read(vanilla_pool))["elements"]
                    for old, new in zip(original, pool["elements"]):
                        before = vanilla_template(vanilla, old["element"]["location"])
                        path = nbt.STRUCT_DIR / (new["element"]["location"].split(":")[1] + ".nbt")
                        after = read_template(path.read_bytes())
                        for field in ("LootTable", "pool"):
                            def values(template):
                                return Counter(block["nbt"][field] for block in template["blocks"]
                                               if field in block.get("nbt", {}))
                            self.assertEqual(values(before), values(after), (biome, field))
                path = POOLS / f"abandoned_camp/camp/{biome}.json"
                campsite = json.loads(path.read_text())
                self.assertEqual(sorted([4, 15, 15, 15]), sorted(row["weight"] for row in campsite["elements"]))
                for role in ("chest", "barrel", "secret", "rest"):
                    piece = build_campsite(theme, role)
                    self.assertEqual("minecraft:end_connector", piece.block_nbts[8, 0, 4]["name"])
                    self.assertEqual("minecraft:cushion", piece.entities[0]["nbt"]["id"])
