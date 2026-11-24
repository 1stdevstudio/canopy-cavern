"""Build the Canopy preset's noise settings and material (surface) rules.

Vanilla material rules pick surface blocks by biome id (sand for deserts, terracotta for
badlands, mycelium, mud, calcite, powder snow...). The Canopy preset has no vanilla biomes, so
this copies the vanilla overworld rule tree into the canopycavern namespace and adds every
Canopy biome that CanopyBiomeMap maps from a listed vanilla biome. Canopy's own biome rules
(exported by CanopyMaterialRuleExportTest) run before the surface rules, as TerraBlender does.

Usage: python3 tools/worldgen/generate_canopy_material_rules.py <extracted vanilla data/minecraft>
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "src/main/resources/data/canopycavern/worldgen"
MAP_SRC = ROOT / "src/main/java/com/yogi/canopycavern/worldgen/CanopyBiomeMap.java"


def biome_map():
    src = MAP_SRC.read_text()
    consts = dict(re.findall(r'private static final String (\w+) = "([a-z:_]+)";', src))
    out = {}
    for vanilla, target in re.findall(r'Map\.entry\("(minecraft:[a-z_]+)", ("?[A-Za-z:_]+"?)\)', src):
        out[vanilla] = target.strip('"') if target.startswith('"') else consts[target]
    return out


def rewrite(node, mapping):
    if isinstance(node, dict):
        node = {k: rewrite(v, mapping) for k, v in node.items()}
        if node.get("type") == "minecraft:biome":
            ids = node["biome_is"] if isinstance(node["biome_is"], list) else [node["biome_is"]]
            extra = [mapping[i] for i in ids if i in mapping]
            node["biome_is"] = list(dict.fromkeys(ids + extra))
        return node
    if isinstance(node, list):
        return [rewrite(v, mapping) for v in node]
    if isinstance(node, str) and node.startswith("minecraft:overworld"):
        return "canopycavern:" + node[len("minecraft:"):]
    return node


def main():
    vdata = Path(sys.argv[1])
    mapping = biome_map()
    src_root = vdata / "worldgen/material_rule"
    files = [src_root / "overworld.json", *sorted((src_root / "overworld").rglob("*.json"))]
    for f in files:
        rel = f.relative_to(src_root)
        data = rewrite(json.loads(f.read_text()), mapping)
        if rel.as_posix() == "overworld.json":
            seq = data["sequence"]
            seq.insert(seq.index("canopycavern:overworld/iron_ore_vein") + 1, "canopycavern:overworld/canopy_biomes")
        out = RES / "material_rule" / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(data, indent=2) + "\n")
    noise = json.loads((vdata / "worldgen/noise_settings/overworld.json").read_text())
    noise["material_rule"] = "canopycavern:overworld"
    (RES / "noise_settings").mkdir(parents=True, exist_ok=True)
    (RES / "noise_settings/overworld.json").write_text(json.dumps(noise, indent=2) + "\n")


if __name__ == "__main__":
    main()
