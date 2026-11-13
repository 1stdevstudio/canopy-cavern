import os
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

DATA = Path(__file__).resolve().parents[2] / "src/main/resources/data/minecraft/structure"
JAR = Path(os.environ.get(
    "MINECRAFT_JAR",
    Path.home() / ".gradle/caches/fabric-loom/26.3/minecraft-common.jar",
))
FAMILIES = {
    "end_city": 20, "igloo": 3, "nether_fossils": 14, "ruined_portal": 13,
    "shipwreck": 20, "underwater_ruin": 48, "woodland_mansion": 73,
}


class VanillaTemplateArchitectureTest(unittest.TestCase):
    def test_all_template_families_have_geometry_overrides(self):
        for family, count in FAMILIES.items():
            with self.subTest(family=family):
                self.assertEqual(count, len(list((DATA / family).glob("*.nbt"))))

    @unittest.skipUnless(JAR.is_file(), "Minecraft 26.3 game JAR required for source comparison")
    def test_geometry_and_gameplay_data_survive_across_all_variants(self):
        from generate_vanilla_template_architecture import (
            decode, generate, normalized, template_cells, template_palettes,
        )

        with ZipFile(JAR) as vanilla, tempfile.TemporaryDirectory() as temp:
            generated = Path(temp)
            self.assertEqual(FAMILIES, generate(vanilla, generated))
            for family in FAMILIES:
                shapes_changed = 0
                for target in sorted((generated / family).glob("*.nbt")):
                    relative = target.relative_to(generated)
                    with self.subTest(template=str(relative)):
                        original = decode(vanilla.read(f"data/minecraft/structure/{relative.as_posix()}"))
                        revised = decode(target.read_bytes())
                        self.assertEqual(normalized(original["size"]), normalized(revised["size"]))
                        self.assertEqual(original["entities"], revised["entities"])
                        self.assertEqual(len(template_palettes(original)), len(template_palettes(revised)))
                        old_cells, new_cells = template_cells(original), template_cells(revised)
                        old_palettes, new_palettes = template_palettes(original), template_palettes(revised)
                        old_sensitive = {pos: cell["nbt"] for pos, cell in old_cells.items() if "nbt" in cell}
                        new_sensitive = {pos: cell["nbt"] for pos, cell in new_cells.items() if "nbt" in cell}
                        self.assertEqual(old_sensitive, new_sensitive)
                        for pos in old_sensitive:
                            for old_palette, new_palette in zip(old_palettes, new_palettes):
                                old_state = old_palette[normalized(old_cells[pos]["state"])]
                                new_state = new_palette[normalized(new_cells[pos]["state"])]
                                self.assertEqual(normalized(old_state), normalized(new_state))
                        def shape_at(cells, palette, pos):
                            cell = cells.get(pos)
                            kind = palette[cell["state"].value]["id"].value if cell else "minecraft:air"
                            if kind == "minecraft:air":
                                return "air"
                            return next((shape for shape in ("_stairs", "_slab", "_wall") if kind.endswith(shape)), "block")

                        changed_outline = any(
                            shape_at(old_cells, old_palettes[0], pos) != shape_at(new_cells, new_palettes[0], pos)
                            for pos in old_cells.keys() | new_cells.keys()
                        )
                        shapes_changed += changed_outline
                        self.assertNotEqual(normalized(original["blocks"]), normalized(revised["blocks"]))
                        self.assertEqual(target.read_bytes(), (DATA / relative).read_bytes())
                self.assertGreater(shapes_changed, 0, family)
