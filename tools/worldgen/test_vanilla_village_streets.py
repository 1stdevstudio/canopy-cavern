import gzip
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "src/main/resources/data"
JAR = Path(os.environ.get(
    "MINECRAFT_JAR",
    Path.home() / ".gradle/caches/fabric-loom/26.3/minecraft-common.jar",
))


class VillageStreetTest(unittest.TestCase):
    def test_street_pools_use_biome_specific_pavement(self):
        for biome in ("plains", "desert", "savanna", "snowy", "taiga"):
            for suffix in ("streets", "zombie/streets", "terminators"):
                pool = DATA / f"minecraft/worldgen/template_pool/village/{biome}/{suffix}.json"
                self.assertTrue(pool.is_file(), str(pool))
                document = json.loads(pool.read_text())
                for entry in document["elements"]:
                    self.assertTrue(entry["element"]["location"].startswith(
                        f"canopycavern:vanilla_revamp/{biome}/roads/"
                    ))

    @unittest.skipUnless(JAR.is_file(), "Minecraft 26.3 game JAR required for source comparison")
    def test_generation_keeps_all_junctions_and_terrain_settings(self):
        from generate_vanilla_village_streets import (
            BIOMES, collect_pools, generate, read_template, surface,
        )

        with zipfile.ZipFile(JAR) as vanilla, tempfile.TemporaryDirectory() as temp:
            output = Path(temp)
            generate(vanilla, output)
            pools = list(collect_pools(vanilla))
            self.assertEqual(17, len(pools))
            variants = set()
            plazas = set()
            for relative, source in pools:
                biome = relative.parts[1]
                generated = json.loads((output / "minecraft/worldgen/template_pool" / relative).read_text())
                self.assertEqual(source["fallback"], generated["fallback"])
                self.assertEqual(len(source["elements"]), len(generated["elements"]))
                for expected, actual in zip(source["elements"], generated["elements"]):
                    self.assertEqual(expected["weight"], actual["weight"])
                    original = expected["element"]
                    transformed = actual["element"]
                    self.assertEqual(original["element_type"], transformed["element_type"])
                    self.assertEqual("terrain_matching", transformed["projection"])
                    if isinstance(original["processors"], str):
                        original_id = original["processors"].split(":")[1]
                        rules = json.loads(vanilla.read(f"data/minecraft/worldgen/processor_list/{original_id}.json"))
                        new_id = transformed["processors"].split(":")[1]
                        generated_rules = json.loads(
                            (output / "canopycavern/worldgen/processor_list" / (new_id + ".json")).read_text()
                        )
                        previous = rules["processors"][0]["rules"]
                        replacements = generated_rules["processors"][0]["rules"]
                        self.assertEqual(previous, replacements[-len(previous):])
                        water_inputs = {
                            r["input_predicate"]["block"] for r in replacements
                            if r["location_predicate"].get("block") == "minecraft:water"
                        }
                        self.assertTrue(set(BIOMES[biome][:2]) <= water_inputs)
                    else:
                        self.assertEqual(original["processors"], transformed["processors"])

                    old_id = original["location"].split(":")[1]
                    new_id = transformed["location"].split(":")[1]
                    if new_id in variants:
                        continue
                    variants.add(new_id)
                    old = read_template(vanilla.read(f"data/minecraft/structure/{old_id}.nbt"))
                    new_path = Path(f"canopycavern/structure/{new_id}.nbt")
                    new = read_template((output / new_path).read_bytes())
                    self.assertEqual(old["size"], new["size"])
                    self.assertEqual(old["entities"], new["entities"])
                    old_states, new_states = surface(old), surface(new)
                    for pos, (state, nbt) in old_states.items():
                        if nbt or state["id"] not in {
                            "minecraft:air", "minecraft:dirt_path", "minecraft:smooth_sandstone",
                        }:
                            self.assertEqual((state, nbt), new_states[pos], (old_id, pos))
                    self.assertNotEqual(old_states, new_states, new_id)
                    for (x, y, z), (state, _) in new_states.items():
                        if y == 1 and state["id"] == BIOMES[biome][2]:
                            self.assertEqual("minecraft:air", old_states.get(
                                (x, y, z), ({"id": "minecraft:air"}, None)
                            )[0]["id"])
                            self.assertIn(new_states[x, 0, z][0]["id"], BIOMES[biome][:2])
                            plazas.add(biome)
                    checked = DATA / new_path
                    self.assertEqual(gzip.decompress((output / new_path).read_bytes()),
                                     gzip.decompress(checked.read_bytes()))
            self.assertEqual(set(BIOMES), plazas)
            self.assertGreaterEqual(len(variants), 165)
