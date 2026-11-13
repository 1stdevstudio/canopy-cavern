import gzip
import subprocess
import sys
import tempfile
import unittest
from collections import deque
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ASSET = (
    TOOLS.parents[1] / "src/main/resources/data/canopycavern/structure"
    / "underground_hollow_village/cavern_borough.nbt"
)


class UndergroundVillageTest(unittest.TestCase):
    def test_grand_hall_has_connected_entrances_and_accessible_villager_quarters(self):
        from generate_underground_village import build_underground_village

        hall = build_underground_village()
        self.assertEqual((47, 23, 47), (hall.sx, hall.sy, hall.sz))
        self.assertLessEqual(max(hall.sx, hall.sy, hall.sz), 48)

        def block(x, y, z):
            return hall.grid.get((x, y, z), ("minecraft:structure_void", ()))[0]

        def passable(x, z):
            if not (0 <= x < hall.sx and 0 <= z < hall.sz):
                return False
            headroom = [block(x, y, z) for y in (1, 2)]
            return (
                block(x, 0, z) not in ("minecraft:air", "minecraft:structure_void")
                and all(b == "minecraft:air" or b.endswith("_door") for b in headroom)
            )

        def adjacent(x, z):
            return ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1))

        start = (23, 0)
        seen = {start}
        queue = deque([start])
        self.assertTrue(passable(*start))
        while queue:
            for neighbor in adjacent(*queue.popleft()):
                if neighbor not in seen and passable(*neighbor):
                    seen.add(neighbor)
                    queue.append(neighbor)

        for exit_cell in ((0, 23), (46, 23), (23, 46)):
            self.assertIn(exit_cell, seen)

        shell = {(x, y, z) for (x, y, z), (kind, _) in hall.grid.items()
                 if y >= 7 and kind in {"minecraft:deepslate", "minecraft:tuff",
                                       "minecraft:cobbled_deepslate"}}
        self.assertGreater(len(shell), 100)
        self.assertTrue(any((46 - x, y, z) not in shell for x, y, z in shell))
        # Quarry facades should form stepped silhouettes instead of four flat house roofs.
        roofs = [max(y for (x, y, z), (kind, _) in hall.grid.items()
                     if x == px and z == pz and kind == "minecraft:polished_deepslate"
                     and 4 <= y <= 8)
                 for px, pz in ((9, 11), (12, 11), (15, 11))]
        self.assertGreater(len(set(roofs)), 1)

        villager_count = 0
        for entity in hall.entities:
            if entity["nbt"]["id"] == "minecraft:villager":
                villager_count += 1
                x, y, z = entity["blockPos"].value
                self.assertEqual(1, y)
                self.assertIn((x, z), seen)
        self.assertEqual(4, villager_count)

        for material in ("blue_bed", "lectern", "composter", "cartography_table", "smithing_table"):
            cells = [
                (x, z) for (x, y, z), (block_id, _) in hall.grid.items()
                if y == 1 and block_id == f"minecraft:{material}"
            ]
            self.assertEqual(8 if material == "blue_bed" else 1, len(cells))
            for cell in cells:
                self.assertTrue(any(pos in seen for pos in adjacent(*cell)), (material, cell))

    def test_checked_in_template_matches_generator_with_different_hash_seeds(self):
        for seed in ("0", "47"):
            with self.subTest(seed=seed), tempfile.TemporaryDirectory() as tmp:
                import os

                env = {**os.environ, "PYTHONHASHSEED": seed}
                subprocess.run(
                    [sys.executable, str(TOOLS / "generate_underground_village.py"), tmp],
                    check=True, env=env,
                )
                actual = Path(tmp) / "underground_hollow_village/cavern_borough.nbt"
                self.assertEqual(gzip.decompress(ASSET.read_bytes()), gzip.decompress(actual.read_bytes()))
