import gzip
import tempfile
import unittest
from collections import deque
from pathlib import Path
from unittest.mock import patch


class AbandonedVillageTest(unittest.TestCase):
    def test_ruins_have_routes_to_reward_chests_and_a_varied_silhouette(self):
        from generate_abandoned_village import ASSET, LOOT, build_ruins, v3

        ruins = build_ruins()
        self.assertEqual((47, 20, 47), (ruins.sx, ruins.sy, ruins.sz))
        self.assertEqual(
            ["minecraft:zombie_villager"] * 2,
            [entity["nbt"]["id"] for entity in ruins.entities],
        )
        self.assertTrue(any(y > 15 and "air" not in block
                            for (_, y, _), (block, _) in ruins.grid.items()))
        self.assertGreater(sum(kind.endswith("_stairs") for kind, _ in ruins.grid.values()), 20)

        def block(x, y, z):
            return ruins.grid.get((x, y, z), ("minecraft:structure_void", ()))[0]

        def adjacent(x, z):
            return ((x + 1, z), (x - 1, z), (x, z + 1), (x, z - 1))

        def can_walk(x, z):
            return block(x, 0, z) not in ("minecraft:structure_void", "minecraft:air") and all(
                block(x, y, z) in ("minecraft:air", "minecraft:cobweb")
                or block(x, y, z).endswith("_door") for y in (1, 2)
            )

        seen = {(23, 0)}
        queue = deque(seen)
        self.assertTrue(can_walk(*queue[0]))
        while queue:
            for candidate in adjacent(*queue.popleft()):
                if candidate not in seen and can_walk(*candidate):
                    seen.add(candidate)
                    queue.append(candidate)
        for exit_cell in ((23, 46), (0, 23), (46, 23)):
            self.assertIn(exit_cell, seen)

        chests = [(x, y, z) for (x, y, z), data in ruins.block_nbts.items()
                  if data.get("LootTable") == LOOT]
        self.assertEqual(4, len(chests))
        for x, y, z in chests:
            self.assertEqual(1, y)
            self.assertTrue(any(pos in seen for pos in adjacent(x, z)))

        original = Path(v3.STRUCT_DIR) / ASSET
        with tempfile.TemporaryDirectory() as folder, patch.object(v3, "STRUCT_DIR", Path(folder)):
            ruins.save(ASSET)
            self.assertEqual(gzip.decompress(original.read_bytes()),
                             gzip.decompress((Path(folder) / ASSET).read_bytes()))
