import gzip
import json
import os
import subprocess
import sys
import tempfile
import unittest
from collections import deque
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
DATA = TOOLS.parents[1] / "src/main/resources/data/canopycavern"
ID = "grotto_outpost_town"
PIECES = {
    "start": {"lantern_market"},
    "streets": {"mining_arcade"},
    "terminators": {"survey_exit"},
    "buildings": {"miners_quarters", "deep_forge", "survey_library", "watch_room"},
}


def cell(piece, x, y, z):
    return piece.grid.get((x, y, z), ("minecraft:structure_void", ()))[0]


def routes(piece, start, height):
    def passable(x, z):
        return (
            0 <= x < piece.sx and 0 <= z < piece.sz
            and piece._is_full_face_solid(cell(piece, x, 0, z))
            and all(cell(piece, x, y, z) in ("minecraft:air", "minecraft:jigsaw")
                    for y in range(1, height + 1))
        )

    queue = deque([start])
    seen = {start}
    while queue:
        x, z = queue.popleft()
        for pos in ((x - 1, z), (x + 1, z), (x, z - 1), (x, z + 1)):
            if pos not in seen and passable(*pos):
                queue.append(pos)
                seen.add(pos)
    return seen


class GrottoOutpostTest(unittest.TestCase):
    def test_generation_uses_redesigned_pieces(self):
        for name, pieces in PIECES.items():
            pool = json.loads((DATA / f"worldgen/template_pool/{ID}/{name}.json").read_text())
            self.assertEqual(
                {f"canopycavern:{ID}/{piece}" for piece in pieces},
                {entry["element"]["location"] for entry in pool["elements"]},
            )

    def test_market_and_arcade_have_open_three_block_routes(self):
        from generate_grotto_outpost import build_arcade, build_market

        for piece, expected in ((build_market(), 4), (build_arcade(), 4)):
            sockets = [pos for pos, tag in piece.block_nbts.items() if tag.get("id") == "minecraft:jigsaw"]
            self.assertEqual(expected, len(sockets))
            x, y, z = sockets[0]
            self.assertEqual(1, y)
            accessible = routes(piece, (x, z), 3)
            for x, y, z in sockets:
                self.assertEqual(1, y)
                self.assertIn((x, z), accessible)
                self.assertEqual("minecraft:air", piece.block_nbts[x, y, z]["final_state"])
            for entity in piece.entities:
                x, y, z = entity["blockPos"].value
                self.assertEqual(1, y)
                self.assertIn((x, z), accessible)

    def test_ceiling_lights_are_supported_by_the_vault(self):
        from generate_grotto_outpost import build_arcade, build_market, build_room, build_survey_exit

        for piece in (build_market(), build_arcade(), build_room("survey_library"), build_survey_exit()):
            for (x, y, z), (block, props) in piece.grid.items():
                if block == "minecraft:lantern" and dict(props)["hanging"] == "true":
                    for offset in (1, 2):
                        self.assertTrue(piece._is_full_face_solid(cell(piece, x, y + offset, z)),
                                        (piece.sx, piece.sy, x, y, z))

    def test_exit_has_clear_route_to_the_cave_boundary(self):
        from generate_grotto_outpost import build_survey_exit

        self.assertIn((3, 6), routes(build_survey_exit(), (3, 0), 3))

    def test_role_rooms_have_reachable_furniture_and_supported_lights(self):
        from generate_grotto_outpost import build_room

        for role, station in (
            ("miners_quarters", "crafting_table"), ("deep_forge", "smithing_table"),
            ("survey_library", "lectern"), ("watch_room", "fletching_table"),
        ):
            with self.subTest(role=role):
                room = build_room(role)
                accessible = routes(room, (4, 0), 2)
                for (x, y, z), (block, props) in room.grid.items():
                    if block in (f"minecraft:{station}", "minecraft:chest", "minecraft:green_bed"):
                        self.assertTrue(any(pos in accessible for pos in
                                            ((x - 1, z), (x + 1, z), (x, z - 1), (x, z + 1))))
                    if block == "minecraft:lantern":
                        offset = 1 if dict(props)["hanging"] == "true" else -1
                        self.assertTrue(room._is_full_face_solid(cell(room, x, y + offset, z)))
                self.assertIn(f"minecraft:{station}", {block for block, _ in room.grid.values()})
                for entity in room.entities:
                    x, y, z = entity["blockPos"].value
                    self.assertEqual(1, y)
                    self.assertIn((x, z), accessible)

    def test_checked_in_templates_match_deterministic_generator(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                [sys.executable, str(TOOLS / "generate_grotto_outpost.py"), tmp],
                check=True, env={**os.environ, "PYTHONHASHSEED": "47"},
            )
            for piece in set.union(*PIECES.values()):
                relative = Path(f"{ID}/{piece}.nbt")
                actual = gzip.decompress((Path(tmp) / relative).read_bytes())
                self.assertEqual(gzip.decompress((DATA / "structure" / relative).read_bytes()), actual)
