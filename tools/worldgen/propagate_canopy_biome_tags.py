"""Add Canopy stand-ins to every biome tag that lists the vanilla biome they replace.

Covers vanilla tags (structures, spawns, categories) and Canopy's own has_structure tags, so a
structure or spawn rule written against a vanilla biome also fires in the Canopy preset.
Usage: python3 tools/worldgen/propagate_canopy_biome_tags.py <extracted vanilla data/minecraft>
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_canopy_material_rules import biome_map  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "src/main/resources/data"


def entries(path):
    return [v if isinstance(v, str) else v["id"] for v in json.loads(path.read_text()).get("values", [])]


def main():
    vanilla = Path(sys.argv[1])
    mapping = biome_map()
    sources = {}
    for f in (vanilla / "tags/worldgen/biome").rglob("*.json"):
        rel = f.relative_to(vanilla / "tags/worldgen/biome")
        sources[DATA / "minecraft/tags/worldgen/biome" / rel] = entries(f)
    for ns in DATA.iterdir():
        for f in (ns / "tags/worldgen/biome").rglob("*.json") if (ns / "tags/worldgen/biome").exists() else []:
            sources.setdefault(f, []).extend(entries(f))
    changed = 0
    for target, listed in sources.items():
        wanted = [mapping[v] for v in listed if v in mapping]
        if not wanted:
            continue
        data = json.loads(target.read_text()) if target.exists() else {"replace": False, "values": []}
        have = set(entries(target)) if target.exists() else set()
        missing = [w for w in dict.fromkeys(wanted) if w not in have]
        if missing:
            data["values"].extend(missing)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(data, indent=2) + "\n")
            changed += 1
    print(f"updated {changed} tag files")


if __name__ == "__main__":
    main()
