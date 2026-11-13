import unittest
from pathlib import Path
from zipfile import ZipFile

from generate_vanilla_template_architecture import DEFAULT_JAR, PREFIX, decode, normalized, template_cells, template_palettes

ASSETS = Path(__file__).resolve().parents[2] / "src/main/resources/data/minecraft/structure"


class AncientCityArchitectureTest(unittest.TestCase):
    def test_all_city_templates_keep_mechanics_and_change_block_shapes(self):
        with ZipFile(DEFAULT_JAR) as jar:
            names = [name for name in jar.namelist()
                     if name.startswith(PREFIX + "ancient_city/") and name.endswith(".nbt")]
            self.assertEqual(58, len(names))
            for name in names:
                with self.subTest(template=name[len(PREFIX):]):
                    before = decode(jar.read(name))
                    after = decode((ASSETS / name[len(PREFIX):]).read_bytes())
                    self.assertEqual(before["size"], after["size"])
                    self.assertEqual(before["entities"], after["entities"])
                    a, b = template_cells(before), template_cells(after)
                    first, last = template_palettes(before)[0], template_palettes(after)[0]

                    def states(cells, palette):
                        return {pos: normalized(palette[cell["state"].value])["id"]
                                for pos, cell in cells.items()}

                    old, new = states(a, first), states(b, last)
                    self.assertEqual({p: c["nbt"] for p, c in a.items() if "nbt" in c},
                                     {p: c["nbt"] for p, c in b.items() if "nbt" in c})
                    for pos, block in old.items():
                        if any(kind in block for kind in ("sculk", "wool", "reinforced_deepslate",
                                                          "redstone", "ladder")):
                            self.assertEqual(a[pos], b[pos])
                    shape_changes = [p for p in new if old.get(p) != new[p] and
                                     new[p].endswith(("_stairs", "_wall", "_slab"))]
                    self.assertGreaterEqual(len(shape_changes), 2)
