import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "src/main/resources/data/canopycavern"


class ExpeditionEnchantmentsTest(unittest.TestCase):
    def test_active_enchantments_have_distinct_supported_gear(self):
        for name, supported in {
            "trail_echo": "minecraft:compass",
            "torchkeeper": "#minecraft:pickaxes",
            "resonant_survey": "#minecraft:pickaxes",
        }.items():
            data = json.loads((ROOT / "enchantment" / f"{name}.json").read_text())
            self.assertEqual(supported, data["supported_items"])
            self.assertEqual(1, data["max_level"])

    def test_mod_gear_is_in_vanilla_enchantment_item_tags(self):
        item_tags = ROOT.parent / "minecraft" / "tags" / "item"
        for tag, items in {
            "head_armor": ("thermal_hood", "mossweave_cap"),
            "chest_armor": ("thermal_parka", "mossweave_tunic"),
            "leg_armor": ("thermal_leggings", "mossweave_trousers"),
            "foot_armor": ("thermal_boots", "mossweave_boots"),
            "pickaxes": ("grotto_crystal_pickaxe",),
        }.items():
            with self.subTest(tag=tag):
                data = json.loads((item_tags / f"{tag}.json").read_text())
                self.assertFalse(data["replace"])
                self.assertCountEqual(data["values"], [f"canopycavern:{item}" for item in items])
