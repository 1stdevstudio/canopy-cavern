import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent))
import dimension_structure_helpers as dsh
import generate_end_structures as gen
from generate_vanilla_template_architecture import decode


END_SPECS = {
    "chorus_monastery_citadel": {
        "biomes": ["minecraft:end_highlands"],
        "start": "cloister",
        "min_solid_thickness": 6,
        "loot_tables": {"canopycavern:chests/end_monastery_vault"},
        "advancement": "discover_chorus_monastery",
    },
    "void_beacon_observatory": {
        "biomes": ["minecraft:end_highlands", "minecraft:end_midlands"],
        "start": "base_tower",
        "min_solid_thickness": 6,
        "loot_tables": {"canopycavern:chests/end_observatory_cache"},
        "advancement": "discover_void_beacon",
    },
    "ender_archive_vault": {
        "biomes": ["minecraft:end_midlands"],
        "start": "rotunda",
        "min_solid_thickness": 14,
        "loot_tables": {"canopycavern:chests/end_archive_vault"},
        "advancement": "discover_ender_archive",
    },
}


class EndStructuresTest(unittest.TestCase):
    def test_end_structures_exclude_central_and_small_islands_and_enforce_guards(self):
        gen.build_chorus_monastery_citadel()
        gen.build_void_beacon_observatory()
        gen.build_ender_archive_vault()

        salts = set()
        forbidden_biomes = {"minecraft:the_end", "minecraft:small_end_islands", "minecraft:end_barrens"}
        for sid, spec in END_SPECS.items():
            s_json = json.loads((dsh.CANOPY_DATA / "worldgen/structure" / f"{sid}.json").read_text())
            self.assertEqual("canopycavern:surface_jigsaw", s_json["type"])
            self.assertEqual("surface_structures", s_json["step"])
            self.assertNotEqual("beard_box", s_json["terrain_adaptation"])
            guard = s_json["terrain_guard"]
            self.assertFalse(guard["allow_water"])
            self.assertEqual(spec["min_solid_thickness"], guard["min_solid_thickness"])

            set_json = json.loads((dsh.CANOPY_DATA / "worldgen/structure_set" / f"{sid}.json").read_text())
            salts.add(set_json["placement"]["salt"])

            tag_json = json.loads((dsh.CANOPY_DATA / "tags/worldgen/biome/has_structure" / f"{sid}.json").read_text())
            self.assertEqual(spec["biomes"], tag_json["values"])
            self.assertTrue(forbidden_biomes.isdisjoint(tag_json["values"]))

            start_pool = json.loads((dsh.CANOPY_DATA / "worldgen/template_pool" / sid / "start.json").read_text())
            self.assertEqual(
                f"canopycavern:{sid}/{spec['start']}",
                start_pool["elements"][0]["element"]["location"],
            )

            seen_loot = set()
            nbt_dir = dsh.CANOPY_DATA / "structure" / sid
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
                    self.assertNotIn(name, ("minecraft:lava", "minecraft:water"))
                    be = b.get("nbt")
                    if be is not None and "LootTable" in be.value:
                        seen_loot.add(be.value["LootTable"].value)

                for raw_ent in root["entities"].value:
                    ent = raw_ent.value
                    ex, ey, ez = (int(v.value) for v in ent["blockPos"].value)
                    ent_nbt = ent["nbt"].value
                    self.assertEqual(1, int(ent_nbt["PersistenceRequired"].value))
                    if ent_nbt["id"].value == "minecraft:shulker":
                        self.assertEqual(0, int(ent_nbt["AttachFace"].value))
                    self.assertEqual("minecraft:air", blocks.get((ex, ey, ez)), f"{nbt_path.name} entity space {ex, ey, ez}")

            self.assertTrue(spec["loot_tables"].issubset(seen_loot), f"{sid} missing chest loot tables: {seen_loot}")
            adv = json.loads((dsh.CANOPY_DATA / "advancement" / f"{spec['advancement']}.json").read_text())
            self.assertIn(sid, json.dumps(adv))

        self.assertEqual(len(END_SPECS), len(salts))


if __name__ == "__main__":
    unittest.main()
