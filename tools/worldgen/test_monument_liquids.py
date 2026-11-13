import json
import unittest
from pathlib import Path


class MonumentLiquidsTest(unittest.TestCase):
    def test_monument_does_not_inherit_water_in_railings(self):
        root = Path(__file__).resolve().parents[2]
        path = root / "src/main/resources/data/canopycavern/worldgen/structure/abyssal_sanctum_monument.json"
        self.assertEqual("ignore_waterlogging", json.loads(path.read_text()).get("liquid_settings"))
