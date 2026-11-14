import json
import unittest
from collections import deque
from pathlib import Path

from generate_abandoned_village import DIRECTIONS, LOOT, VILLAGE_ID
from generate_vanilla_template_architecture import decode
from test_biome_village_redesign import nbt_blocks, nbt_entities

DATA = Path(__file__).resolve().parents[2] / "src/main/resources/data/canopycavern"


class AbandonedVillageTest(unittest.TestCase):
    def test_modular_ruins_chest_routes_belfry_and_zombie_villagers(self):
        struct_dir = DATA / "structure" / VILLAGE_ID
        self.assertFalse((struct_dir / "ruins.nbt").exists())

        cfg = json.loads((DATA / "worldgen/structure" / f"{VILLAGE_ID}.json").read_text())
        self.assertEqual("canopycavern:surface_jigsaw", cfg["type"])
        self.assertEqual("beard_thin", cfg["terrain_adaptation"])
        self.assertGreaterEqual(cfg["terrain_guard"]["min_rigid_pieces"], 4)

        belfry_nbt = decode((struct_dir / "belfry_plaza.nbt").read_bytes())
        self.assertEqual([13, 20, 13], [v.value for v in belfry_nbt["size"].value])
        belfry_grid = nbt_blocks(belfry_nbt)
        max_y = max(y for (_, y, _), (b, _, _) in belfry_grid.items() if b not in ("minecraft:air", "minecraft:structure_void"))
        self.assertGreaterEqual(max_y, 16)
        self.assertIn("minecraft:bell", [b for b, _, _ in belfry_grid.values()])

        all_entities = list(nbt_entities(belfry_nbt))
        chests = 0
        blocks_seen = set()

        for d in DIRECTIONS:
            self.assertTrue((struct_dir / f"ruined_street_{d}.nbt").is_file())
            hall_nbt = decode((struct_dir / f"ruined_hall_{d}.nbt").read_bytes())
            self.assertEqual([11, 11, 11], [v.value for v in hall_nbt["size"].value])
            grid = nbt_blocks(hall_nbt)
            all_entities.extend(nbt_entities(hall_nbt))
            blocks_seen |= {b for b, _, _ in grid.values()}

            hall_chests = [pos for pos, (b, _, be) in grid.items() if b == "minecraft:chest" and be and be.get("LootTable") == LOOT]
            self.assertEqual(1, len(hall_chests))
            chests += len(hall_chests)
            cx, cy, cz = hall_chests[0]

            # BFS from front doorstep (5, 1, 0) to adjacent tile before chest (7, 1, 8)
            seen = {(5, 1, 0)}
            q = deque([(5, 1, 0)])
            while q:
                x, y, z = q.popleft()
                for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = (x + dx, y, z + dz)
                    if nxt in seen or not (0 <= nxt[0] < 11 and 0 <= nxt[2] < 11):
                        continue
                    bid = grid.get(nxt, ("minecraft:structure_void", {}, None))[0]
                    if bid in ("minecraft:air", "minecraft:structure_void", "minecraft:dark_oak_door"):
                        seen.add(nxt)
                        q.append(nxt)
            self.assertTrue(
                any((cx + dx, cy, cz + dz) in seen for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))),
                f"chest unreachable in ruined_hall_{d}",
            )

        for required in ("minecraft:mossy_stone_bricks", "minecraft:cracked_stone_bricks", "minecraft:cobweb", "minecraft:dark_oak_door", "minecraft:iron_bars", "minecraft:dark_oak_stairs"):
            self.assertIn(required, blocks_seen)
        self.assertGreaterEqual(chests, 4)

        entity_ids = [e["id"] for e in all_entities]
        self.assertEqual(0, entity_ids.count("minecraft:villager"))
        self.assertGreaterEqual(entity_ids.count("minecraft:zombie_villager"), 2)


if __name__ == "__main__":
    unittest.main()
