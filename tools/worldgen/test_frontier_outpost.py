import json
import unittest
from pathlib import Path

from generate_frontier_outpost import LOOT, OUTPOST_ID
from generate_vanilla_template_architecture import decode
from test_biome_village_redesign import nbt_blocks, nbt_entities

DATA = Path(__file__).resolve().parents[2] / "src/main/resources/data"


class FrontierOutpostTest(unittest.TestCase):
    def test_modular_templates_ladder_caged_golem_and_surface_guard(self):
        struct_dir = DATA / "canopycavern/structure" / OUTPOST_ID
        self.assertFalse((struct_dir / "stockade.nbt").exists())
        self.assertFalse((DATA / "minecraft/worldgen/structure/pillager_outpost.json").exists())

        cfg = json.loads((DATA / "canopycavern/worldgen/structure" / f"{OUTPOST_ID}.json").read_text())
        self.assertEqual("canopycavern:surface_jigsaw", cfg["type"])
        self.assertEqual("beard_thin", cfg["terrain_adaptation"])
        self.assertGreaterEqual(cfg["terrain_guard"]["min_rigid_pieces"], 3)

        keep_nbt = decode((struct_dir / "watchtower_keep.nbt").read_bytes())
        self.assertEqual([15, 25, 15], [v.value for v in keep_nbt["size"].value])
        keep_grid = nbt_blocks(keep_nbt)

        # Continuous climbable ladder reaching Floor 1 (y=7) and Floor 2 (y=14)
        for y in range(1, 15):
            self.assertEqual("minecraft:ladder", keep_grid[(8, y, 8)][0])
            self.assertEqual("minecraft:dark_oak_log", keep_grid[(9, y, 8)][0])
        self.assertEqual("minecraft:air", keep_grid[(8, 15, 8)][0])

        stairs = sum(1 for b, _, _ in keep_grid.values() if b == "minecraft:dark_oak_stairs")
        self.assertGreaterEqual(stairs, 100)

        cage_nbt = decode((struct_dir / "golem_cage.nbt").read_bytes())
        cage_grid = nbt_blocks(cage_nbt)
        bars = sum(1 for b, _, _ in cage_grid.values() if b == "minecraft:iron_bars")
        self.assertGreaterEqual(bars, 24)
        cage_golems = [e for e in nbt_entities(cage_nbt) if e["id"] == "minecraft:iron_golem"]
        self.assertEqual(1, len(cage_golems))

        gx, gy, gz = cage_golems[0]["blockPos"]
        for dx in (-1, 0, 1):
            for dy in (0, 1, 2):
                for dz in (-1, 0, 1):
                    self.assertEqual("minecraft:air", cage_grid[(gx + dx, gy + dy, gz + dz)][0])

        pieces = ("watchtower_keep.nbt", "golem_cage.nbt", "tent_west.nbt", "tent_east.nbt", "gate_palisade.nbt")
        all_entities = []
        all_chests = []
        for fname in pieces:
            nbt = decode((struct_dir / fname).read_bytes())
            grid = nbt_blocks(nbt)
            all_entities.extend(e["id"] for e in nbt_entities(nbt))
            for block, props, be in grid.values():
                if block == "minecraft:campfire":
                    self.assertEqual("false", props.get("lit"))
                if be and "LootTable" in be:
                    all_chests.append(be["LootTable"])

        self.assertGreaterEqual(all_entities.count("minecraft:pillager"), 4)
        self.assertEqual(0, all_entities.count("minecraft:villager"))
        self.assertGreaterEqual(len(all_chests), 3)
        self.assertTrue(all(t == LOOT for t in all_chests))


if __name__ == "__main__":
    unittest.main()
