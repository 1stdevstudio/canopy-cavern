"""Checks the Grand Farmsteads: in every theme pool, irrigated crops, composters and farmers."""
import gzip
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_biome_village_redesign import decode, nbt_blocks  # noqa: E402

DATA = Path(__file__).resolve().parents[2] / "src/main/resources/data"
THEMES = ("plains", "desert", "savanna", "snowy", "taiga")


class VillageFarmsteadTest(unittest.TestCase):
    def test_farmstead_in_every_theme_pool(self):
        for theme in THEMES:
            pool = json.loads((DATA / f"minecraft/worldgen/template_pool/village/{theme}/houses.json").read_text())
            locs = [e["element"].get("location") for e in pool["elements"]]
            self.assertIn(f"canopycavern:vanilla_revamp/{theme}/grand_farmstead", locs, theme)
            self.assertEqual(pool["elements"][-1]["element"]["element_type"], "minecraft:empty_pool_element")

    def test_farmstead_has_crops_water_workstations_and_farmers(self):
        crop_ids = {"minecraft:wheat", "minecraft:carrots", "minecraft:potatoes", "minecraft:beetroots",
                    "minecraft:melon_stem", "minecraft:pumpkin_stem", "minecraft:sugar_cane", "minecraft:sweet_berry_bush"}
        for theme in THEMES:
            nbt = decode((DATA / f"canopycavern/structure/vanilla_revamp/{theme}/grand_farmstead.nbt").read_bytes())
            counts = {}
            for name, _props, _nbt in nbt_blocks(nbt).values():
                counts[name] = counts.get(name, 0) + 1
            crops = sum(v for k, v in counts.items() if k in crop_ids)
            self.assertGreaterEqual(crops, 80, f"{theme}: only {crops} crop blocks")
            self.assertGreaterEqual(counts.get("minecraft:water", 0), 24, theme)  # berry fields need no channel
            self.assertGreaterEqual(counts.get("minecraft:composter", 0), 2, theme)
            self.assertIn("minecraft:jigsaw", counts, theme)
            farmers = [e for e in (raw.value["nbt"].value for raw in nbt["entities"].value)
                       if e["id"].value == "minecraft:villager"
                       and e["VillagerData"].value["profession"].value == "minecraft:farmer"]
            self.assertEqual(len(farmers), 2, theme)


if __name__ == "__main__":
    unittest.main()
