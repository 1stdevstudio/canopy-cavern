import json
import unittest
from pathlib import Path

from generate_biome_villages import BIOME_CITIES
from generate_v04_ocean_and_villages import THEMES as VANILLA_THEMES
from generate_vanilla_template_architecture import decode

DATA = Path(__file__).resolve().parents[2] / "src/main/resources/data/canopycavern"
V03_CITIES = ("crystal_citadel", "peak_citadel", "canopy_village")
NON_BOXY_BUILDINGS = (
    "villa_l_wing",
    "rotunda_observatory",
    "market_t_hall",
    "foundry_bastion",
    "cruciform_guildhall",
)
EXPECTED_STREETS = (
    "street_boulevard_dual",
    "street_boulevard_single",
    "street_turn_left",
    "street_turn_right",
    "street_t_junction",
    "street_crossroad_plaza",
    "street_diagonal_zig",
)


def nbt_blocks(nbt: dict) -> dict[tuple[int, int, int], tuple[str, dict[str, str], dict | None]]:
    palette = []
    for raw_entry in nbt["palette"].value:
        entry = raw_entry.value
        name_tag = entry.get("Name") or entry.get("id")
        props = {}
        props_tag = entry.get("Properties") or entry.get("properties")
        if props_tag is not None:
            props = {k: v.value for k, v in props_tag.value.items()}
        palette.append((name_tag.value, props))
    grid = {}
    for raw_cell in nbt["blocks"].value:
        cell = raw_cell.value
        pos = tuple(int(c.value) for c in cell["pos"].value)
        name, props = palette[int(cell["state"].value)]
        be = cell.get("nbt")
        grid[pos] = (name, props, {k: v.value for k, v in be.value.items()} if be is not None else None)
    return grid


def nbt_entities(nbt: dict) -> list[dict]:
    out = []
    for raw_ent in nbt["entities"].value:
        ent = raw_ent.value
        ent_nbt = ent["nbt"].value
        out.append({
            "id": ent_nbt["id"].value,
            "blockPos": [int(v.value) for v in ent["blockPos"].value],
        })
    return out


class BiomeVillageRedesignTest(unittest.TestCase):
    def test_all_nine_surface_cities_are_sprawling_and_non_boxy(self):
        all_cities = [(spec.palette.city_id, spec.palette.stilt_height) for spec in BIOME_CITIES] + [
            (cid, 0) for cid in V03_CITIES
        ]
        for city_id, stilt_height in all_cities:
            with self.subTest(city=city_id):
                struct = json.loads((DATA / f"worldgen/structure/{city_id}.json").read_text())
                self.assertEqual("canopycavern:surface_jigsaw", struct["type"])
                self.assertEqual(7, struct["size"])
                self.assertGreaterEqual(struct["max_distance_from_center"], 112)
                self.assertIn("terrain_guard", struct)

                streets_pool = json.loads((DATA / f"worldgen/template_pool/{city_id}/streets.json").read_text())
                street_locs = {e["element"]["location"] for e in streets_pool["elements"]}
                for street_name in EXPECTED_STREETS:
                    self.assertIn(f"canopycavern:{city_id}/{street_name}", street_locs)

                buildings_pool = json.loads((DATA / f"worldgen/template_pool/{city_id}/buildings.json").read_text())
                bldg_locs = {e["element"]["location"] for e in buildings_pool["elements"]}
                for bldg_name in NON_BOXY_BUILDINGS + ("side_garden",):
                    self.assertIn(f"canopycavern:{city_id}/{bldg_name}", bldg_locs)

                struct_dir = DATA / "structure" / city_id
                for obsolete in (
                    "house_farmer.nbt",
                    "street_farmer.nbt",
                    "house.nbt",
                    "forge.nbt",
                    "street_avenue.nbt",
                    "terminator.nbt",
                ):
                    self.assertFalse((struct_dir / obsolete).exists(), f"stale boxy file remains: {obsolete}")

                # Check every center & non-boxy civic building has chamfered/wing voids, valid lanterns, and beds
                for piece_name in ("town_center",) + NON_BOXY_BUILDINGS:
                    nbt = decode((struct_dir / f"{piece_name}.nbt").read_bytes())
                    sx, _, sz = [int(v.value) for v in nbt["size"].value]
                    blocks = nbt_blocks(nbt)
                    corners = [(0, stilt_height, 0), (sx - 1, stilt_height, 0), (0, stilt_height, sz - 1), (sx - 1, stilt_height, sz - 1)]
                    void_corners = sum(
                        1 for pos in corners if blocks.get(pos, ("minecraft:structure_void", {}, None))[0] == "minecraft:structure_void"
                    )
                    self.assertGreaterEqual(void_corners, 3, f"{city_id}/{piece_name} should not have a solid square base corners={corners}")

                    for (lx, ly, lz), (bid, props, _) in blocks.items():
                        if bid == "minecraft:lantern":
                            sup = (lx, ly + 1, lz) if props.get("hanging") == "true" else (lx, ly - 1, lz)
                            sup_id = blocks.get(sup, ("minecraft:structure_void", {}, None))[0]
                            self.assertNotIn(sup_id, ("minecraft:air", "minecraft:structure_void"), f"{city_id}/{piece_name} floating lantern at {(lx, ly, lz)}")

                    if piece_name != "town_center":
                        bed_heads = sum(
                            1 for bid, props, _ in blocks.values()
                            if bid.endswith("_bed") and props.get("part") == "head"
                        )
                        self.assertGreaterEqual(bed_heads, 2, f"{city_id}/{piece_name} needs >= 2 beds")

    def test_mangrove_marsh_keeps_water_stilt_guard_and_rigid_docks(self):
        struct = json.loads((DATA / "worldgen/structure/mangrove_marsh_village.json").read_text())
        guard = struct["terrain_guard"]
        self.assertTrue(guard["allow_water"])
        self.assertEqual(2, guard["max_water_depth"])
        self.assertEqual(0, guard["min_piece_y_above_sea"])
        self.assertEqual("none", struct["terrain_adaptation"])
        streets_pool = json.loads((DATA / "worldgen/template_pool/mangrove_marsh_village/streets.json").read_text())
        for elem in streets_pool["elements"]:
            self.assertEqual("rigid", elem["element"]["projection"])

    def test_vanilla_revamp_halls_are_non_boxy_across_all_five_themes(self):
        for theme in VANILLA_THEMES:
            for role in ("grand_manor", "guild_smithy", "sanctuary_library"):
                with self.subTest(theme=theme, role=role):
                    nbt = decode((DATA / f"structure/vanilla_revamp/{theme}/{role}.nbt").read_bytes())
                    sx, _, sz = [int(v.value) for v in nbt["size"].value]
                    blocks = nbt_blocks(nbt)
                    corners = [(0, 0, 0), (sx - 1, 0, 0), (0, 0, sz - 1), (sx - 1, 0, sz - 1)]
                    self.assertTrue(
                        all(blocks.get(c, ("minecraft:structure_void", {}, None))[0] == "minecraft:structure_void" for c in corners),
                        f"{theme}/{role} still has solid bounding-box base corners",
                    )
                    jigsaws = [b for b in blocks.values() if b[0] == "minecraft:jigsaw"]
                    self.assertEqual(1, len(jigsaws))
                    self.assertEqual("minecraft:building_entrance", jigsaws[0][2]["name"])
                    ents = [e["id"] for e in nbt_entities(nbt)]
                    self.assertGreaterEqual(ents.count("canopycavern:village_sentinel"), 2)
                    self.assertGreaterEqual(ents.count("minecraft:villager"), 2)


if __name__ == "__main__":
    unittest.main()
