"""Generate Canopy replacement biomes from their vanilla counterparts.

Each Canopy biome copies the features, carvers and mob spawns of a vanilla "template" biome
(so feature order stays compatible and every survival resource is kept), applies the
Canopy palette, and inherits every vanilla biome tag the template is listed in directly
(structures, spawn rules, ocean/river/beach categories...).

Usage: python3 tools/worldgen/generate_canopy_biomes.py <path to extracted vanilla data/minecraft>
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "src/main/resources"

# id: (vanilla template, palette, en name, id name, humidity %)
BIOMES = {
    # Phase 1: water and coast
    "sunlit_shallows":   ("warm_ocean",     dict(water="#2fbf9f", fog="#1f8f7a", sky="#7fc9b0"), "Sunlit Shallows", "Perairan Terang", 82),
    "coral_drift":       ("lukewarm_ocean", dict(water="#2ba88f", fog="#1c7c6a", sky="#7cbfa8"), "Coral Drift", "Arus Karang", 80),
    "temperate_sound":   ("ocean",          dict(water="#25897a", fog="#16645a", sky="#7fb5a0"), "Temperate Sound", "Selat Sedang", 78),
    "abyssal_trench":    ("deep_ocean",     dict(water="#1d6b60", fog="#0f4740", sky="#6fa592"), "Abyssal Trench", "Palung Abisal", 78),
    "kelpwood_sea":      ("cold_ocean",     dict(water="#2a7a68", fog="#18564a", sky="#86b0a0"), "Kelpwood Sea", "Laut Rimba Kelp", 74),
    "floe_sea":          ("frozen_ocean",   dict(water="#4f8f82", fog="#2f6b60", sky="#a9c9bc"), "Floe Sea", "Laut Bongkahan Es", 66),
    "meandering_river":  ("river",          dict(water="#2e8f74", fog="#1e6b56", sky="#82b9a0"), "Meandering River", "Sungai Berkelok", 72),
    "frostbound_river":  ("frozen_river",   dict(water="#5a9686", fog="#3a7064", sky="#b0ccc0"), "Frostbound River", "Sungai Membeku", 60),
    "golden_strand":     ("beach",          dict(water="#2fb29a", fog="#1f8a76", sky="#9cc8a6"), "Golden Strand", "Pantai Keemasan", 64),
    "frostline_shore":   ("snowy_beach",    dict(water="#4f8f82", fog="#2f6b60", sky="#b4cfc2"), "Frostline Shore", "Pesisir Garis Beku", 56),
    # Phase 2: lowlands, forests, wetlands, drylands
    "wildgrass_plains":   ("plains",                   dict(water="#2e9a78", fog="#1e7058", sky="#8fc4a0"), "Wildgrass Plains", "Padang Rumput Liar", 50),
    "sunbaked_savanna":   ("savanna",                  dict(water="#3a9a72", fog="#2a7052", sky="#b8c88c"), "Sunbaked Savanna", "Sabana Terik", 30),
    "dune_expanse":       ("desert",                   dict(water="#3aa07c", fog="#2a7a5c", sky="#d4c890"), "Dune Expanse", "Hamparan Bukit Pasir", 12),
    "rustrock_badlands":  ("badlands",                 dict(water="#4a9a76", fog="#3a7054", sky="#d8b48a"), "Rustrock Badlands", "Tanah Tandus Karat", 10),
    "oakhollow_woods":    ("forest",                   dict(water="#2a8a6e", fog="#1c6650", sky="#86b896"), "Oakhollow Woods", "Hutan Oak Rongga", 70),
    "bloomveil_forest":   ("flower_forest",            dict(water="#2a8f74", fog="#1c6a56", sky="#9ac2a0"), "Bloomveil Forest", "Hutan Tirai Bunga", 72),
    "silverbirch_glade":  ("birch_forest",             dict(water="#2c8c72", fog="#1d6854", sky="#94c0a2"), "Silverbirch Glade", "Lembah Birch Perak", 66),
    "blossom_terrace":    ("cherry_grove",             dict(water="#3a9e86", fog="#2a7a66", sky="#c8b8a8"), "Blossom Terrace", "Teras Sakura", 64),
    "dapplelight_wood":   ("dappled_forest",           dict(water="#2c8a6c", fog="#1d6650", sky="#8eb898"), "Dapplelight Wood", "Hutan Cahaya Belang", 68),
    "ashen_garden":       ("pale_garden",              dict(water="#6a8a7e", fog="#4c6a60", sky="#b4bcb4"), "Ashen Garden", "Taman Kelabu", 62),
    "spruce_hollow":      ("taiga",                    dict(water="#287a68", fog="#1a584a", sky="#8ab2a0"), "Spruce Hollow", "Lembah Cemara", 74),
    "giant_spruce_reach": ("old_growth_spruce_taiga",  dict(water="#26766a", fog="#18544a", sky="#84ac9a"), "Giant Spruce Reach", "Bentang Cemara Raksasa", 78),
    "tanglewild_jungle":  ("jungle",                   dict(water="#2a9a76", fog="#1c7456", sky="#86c094"), "Tanglewild Jungle", "Rimba Kusut", 92),
    "bamboo_thicket":     ("bamboo_jungle",            dict(water="#2a9a78", fog="#1c7458", sky="#8ec49a"), "Bamboo Thicket", "Belukar Bambu", 90),
    "bogwater_fen":       ("swamp",                    dict(water="#4a7a52", fog="#36583c", sky="#8aa286"), "Bogwater Fen", "Rawa Air Gambut", 94),
    "mangrove_tangle":    ("mangrove_swamp",           dict(water="#3e7a5a", fog="#2c5842", sky="#88a690"), "Mangrove Tangle", "Belantara Bakau", 96),
}


def vanilla_tags(vdata: Path):
    tags = {}
    base = vdata / "tags/worldgen/biome"
    for f in base.rglob("*.json"):
        values = json.loads(f.read_text()).get("values", [])
        tags[f.relative_to(base).with_suffix("").as_posix()] = [v if isinstance(v, str) else v["id"] for v in values]
    return tags


def main():
    vdata = Path(sys.argv[1])
    tags = vanilla_tags(vdata)
    tag_dir = RES / "data/minecraft/tags/worldgen/biome"
    langs = {"en_us": {}, "id_id": {}}
    for bid, (template, pal, en, idn, _hum) in BIOMES.items():
        biome = json.loads((vdata / f"worldgen/biome/{template}.json").read_text())
        attrs = biome.setdefault("attributes", {})
        attrs["minecraft:visual/sky_color"] = pal["sky"]
        attrs["minecraft:visual/water_fog_color"] = pal["fog"]
        biome.setdefault("effects", {})["water_color"] = pal["water"]
        out = RES / f"data/canopycavern/worldgen/biome/{bid}.json"
        out.write_text(json.dumps(biome, indent=2) + "\n")
        for tag, values in tags.items():
            if f"minecraft:{template}" in values:
                p = tag_dir / f"{tag}.json"
                data = json.loads(p.read_text()) if p.exists() else {"replace": False, "values": []}
                entry = f"canopycavern:{bid}"
                if entry not in data["values"]:
                    data["values"].append(entry)
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps(data, indent=2) + "\n")
        langs["en_us"][f"biome.canopycavern.{bid}"] = en
        langs["id_id"][f"biome.canopycavern.{bid}"] = idn
    for lang, entries in langs.items():
        p = RES / f"assets/canopycavern/lang/{lang}.json"
        data = json.loads(p.read_text())
        data.update(entries)
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
