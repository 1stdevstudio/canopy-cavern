import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent))
import dimension_structure_helpers as dsh
import generate_nether_structures as gen
from generate_vanilla_template_architecture import decode


NETHER_SPECS = {
    "cinder_vault_bastion": {
        "biomes": ["minecraft:nether_wastes", "minecraft:crimson_forest"],
        "start": "sanctum_core",
        "min_rigid_pieces": 2,
        "loot_tables": {"canopycavern:chests/nether_bastion_vault", "canopycavern:chests/nether_bastion_supply"},
        "advancement": "discover_cinder_vault",
    },
    "soul_catacomb_reliquary": {
        "biomes": ["minecraft:soul_sand_valley"],
        "start": "nave",
        "min_rigid_pieces": 2,
        "loot_tables": {"canopycavern:chests/nether_soul_reliquary"},
        "advancement": "discover_soul_reliquary",
    },
    "basalt_thermal_spire": {
        "biomes": ["minecraft:basalt_deltas"],
        "start": "keep",
        "min_rigid_pieces": 1,
        "loot_tables": {"canopycavern:chests/nether_thermal_spire"},
        "advancement": "discover_basalt_spire",
    },
}


class NetherStructuresTest(unittest.TestCase):
    def test_nether_structures_generate_valid_configs_templates_and_guards(self):
        gen.build_cinder_vault_bastion()
        gen.build_soul_catacomb_reliquary()
        gen.build_basalt_thermal_spire()

        salts = set()
        for sid, spec in NETHER_SPECS.items():
            s_json = json.loads((dsh.CANOPY_DATA / "worldgen/structure" / f"{sid}.json").read_text())
            self.assertEqual("canopycavern:nether_cavern_jigsaw", s_json["type"])
            self.assertEqual("none", s_json["terrain_adaptation"])
            self.assertEqual("underground_structures", s_json["step"])
            guard = s_json["cavern_guard"]
            self.assertGreaterEqual(guard["min_floor_y"], 33)
            self.assertLessEqual(guard["max_ceiling_y"], 118)
            self.assertEqual(spec["min_rigid_pieces"], guard["min_rigid_pieces"])

            set_json = json.loads((dsh.CANOPY_DATA / "worldgen/structure_set" / f"{sid}.json").read_text())
            salts.add(set_json["placement"]["salt"])

            tag_json = json.loads((dsh.CANOPY_DATA / "tags/worldgen/biome/has_structure" / f"{sid}.json").read_text())
            self.assertEqual(spec["biomes"], tag_json["values"])

            start_pool = json.loads((dsh.CANOPY_DATA / "worldgen/template_pool" / sid / "start.json").read_text())
            self.assertEqual(
                f"canopycavern:{sid}/{spec['start']}",
                start_pool["elements"][0]["element"]["location"],
            )

            seen_loot = set()
            nbt_dir = dsh.CANOPY_DATA / "structure" / sid
            self.assertTrue(any(nbt_dir.glob("*.nbt")))
            for nbt_path in sorted(nbt_dir.glob("*.nbt")):
                root = decode(nbt_path.read_bytes())
                sx, sy, sz = (int(v.value) for v in root["size"].value)
                palette = [
                    (e.value.get("Name") or e.value.get("id")).value
                    for e in root["palette"].value
                ]
                blocks = {}
                for raw_b in root["blocks"].value:
                    b = raw_b.value
                    bx, by, bz = (int(v.value) for v in b["pos"].value)
                    self.assertTrue(0 <= bx < sx and 0 <= by < sy and 0 <= bz < sz)
                    name = palette[int(b["state"].value)]
                    blocks[(bx, by, bz)] = name
                    self.assertNotIn(name, ("minecraft:lava", "minecraft:fire", "minecraft:magma_block"))
                    be = b.get("nbt")
                    if be is not None and "LootTable" in be.value:
                        seen_loot.add(be.value["LootTable"].value)

                for raw_ent in root["entities"].value:
                    ent = raw_ent.value
                    ex, ey, ez = (int(v.value) for v in ent["blockPos"].value)
                    ent_nbt = ent["nbt"].value
                    self.assertEqual(1, int(ent_nbt["PersistenceRequired"].value))
                    ent_id = ent_nbt["id"].value
                    if ent_id in ("minecraft:piglin", "minecraft:piglin_brute"):
                        self.assertEqual(1, int(ent_nbt["CannotHunt"].value))
                    self.assertEqual("minecraft:air", blocks.get((ex, ey, ez)), f"{nbt_path.name} entity feet {ex, ey, ez}")
                    self.assertEqual("minecraft:air", blocks.get((ex, ey + 1, ez)), f"{nbt_path.name} entity head {ex, ey + 1, ez}")

            self.assertTrue(spec["loot_tables"].issubset(seen_loot), f"{sid} missing chest loot tables: {seen_loot}")
            adv = json.loads((dsh.CANOPY_DATA / "advancement" / f"{spec['advancement']}.json").read_text())
            self.assertIn(sid, json.dumps(adv))

        self.assertEqual(len(NETHER_SPECS), len(salts))


if __name__ == "__main__":
    unittest.main()
