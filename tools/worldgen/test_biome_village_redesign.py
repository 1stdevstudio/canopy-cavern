from collections import deque
import gzip
import unittest
from pathlib import Path


class BiomeVillageRedesignTest(unittest.TestCase):
    def test_themes_have_distinct_roof_geometry_and_accessible_homes(self):
        from generate_biome_villages import THEMES, build_village

        profiles = set()
        for name, theme in THEMES.items():
            with self.subTest(village=name):
                village = build_village(name, theme)
                profiles.add(frozenset((x, y, z) for (x, y, z), (block, _) in village.grid.items()
                                       if y >= 6 and block not in ("minecraft:air", "minecraft:structure_void")))
                self.assertEqual((47, 47), (village.sx, village.sz))
                self.assertLessEqual(village.sy, 48)

                def block(x, y, z):
                    return village.grid.get((x, y, z), ("minecraft:structure_void", ()))[0]

                def passable(x, z):
                    return (block(x, 0, z) != "minecraft:structure_void"
                            and all(block(x, y, z) == "minecraft:air"
                                    or block(x, y, z).endswith("_door") for y in (1, 2)))

                start = (23, 0)
                self.assertTrue(passable(*start))
                seen = {start}
                queue = deque([start])
                while queue:
                    x, z = queue.popleft()
                    for target in ((x - 1, z), (x + 1, z), (x, z - 1), (x, z + 1)):
                        if target not in seen and passable(*target):
                            seen.add(target)
                            queue.append(target)
                for entity in village.entities:
                    x, y, z = entity["blockPos"].value
                    self.assertEqual(1, y)
                    self.assertIn((x, z), seen)
                for (x, y, z), (kind, _) in village.grid.items():
                    if y == 1 and (kind.endswith("_bed") or kind in {
                        "minecraft:composter", "minecraft:lectern", "minecraft:grindstone",
                        "minecraft:cartography_table",
                    }):
                        self.assertTrue(any(pos in seen for pos in (
                            (x - 1, z), (x + 1, z), (x, z - 1), (x, z + 1),
                        )), (kind, x, z))
        self.assertEqual(len(THEMES), len(profiles))

    def test_all_six_templates_are_present_and_distinct_from_legacy(self):
        from generate_biome_villages import THEMES, v3

        for name in THEMES:
            with self.subTest(village=name):
                folder = Path(v3.STRUCT_DIR) / name
                original = gzip.decompress((folder / "center.nbt").read_bytes())
                new = gzip.decompress((folder / "hillside_village.nbt").read_bytes())
                self.assertNotEqual(original, new)
