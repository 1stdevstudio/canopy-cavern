import gzip
import tempfile
import unittest
from collections import deque
from pathlib import Path
from unittest.mock import patch

from generate_mining_city import ASSET, DISTRICTS, build, v3


class MiningCityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.city = build()

    def test_north_entrance_reaches_every_home_workstation_and_public_facility(self):
        city = self.city
        self.assertEqual((100, 30, 100), (city.sx, city.sy, city.sz))
        start = (50, 0)
        directions = ((0, 1), (0, -1), (1, 0), (-1, 0))

        def cell(x, y, z):
            return city.grid.get((x, y, z), ("minecraft:structure_void", ()))[0]

        def walkable(x, z):
            return city._is_full_face_solid(cell(x, 0, z)) and all(
                cell(x, y, z) == "minecraft:air" or cell(x, y, z).endswith("_door")
                for y in (1, 2)
            )

        self.assertTrue(walkable(*start))
        seen, queue = {start}, deque([start])
        while queue:
            x, z = queue.popleft()
            for dx, dz in directions:
                p = x + dx, z + dz
                if p not in seen and walkable(*p):
                    seen.add(p)
                    queue.append(p)

        residents = [
            e for e in city.entities if e["nbt"]["id"] == "minecraft:villager"
        ]
        self.assertEqual(8, len(residents))
        self.assertEqual(1, sum(
            e["nbt"]["id"] == "canopycavern:village_sentinel" for e in city.entities
        ))
        for resident in residents:
            x, y, z = resident["blockPos"].value
            self.assertEqual(1, y)
            self.assertIn((x, z), seen)
        for district in DISTRICTS:
            self.assertIn((district.x, district.z), seen)
            entry = district.x, district.z - 4
            self.assertEqual("minecraft:air", cell(entry[0], 1, entry[1]))
            self.assertIn(entry, seen)
            self.assertIn((district.x, district.z - 11), seen)
            landmark = {
                "market": "minecraft:hay_block",
                "forge": "minecraft:anvil",
                "garden": "minecraft:brown_mushroom",
                "archive": "minecraft:bookshelf",
            }[district.kind]
            self.assertEqual(landmark, cell(district.x - 4, 1, district.z - 10))
            self.assertIn((district.x - 3, district.z - 10), seen)
            for offset, (_, station) in zip((-4, 4), district.jobs):
                x, z = district.x + offset, district.z + 5
                self.assertEqual(station, cell(x, 1, z))
                self.assertIn((x, z - 1), seen)
        beds = [pos for pos, (kind, props) in city.grid.items()
                if kind.endswith("_bed") and dict(props)["part"] == "head"]
        self.assertEqual(8, len(beds))
        for x, y, z in beds:
            self.assertEqual("head", dict(city.grid[x, y, z][1])["part"])
            self.assertEqual("foot", dict(city.grid[x, y, z + 1][1])["part"])
            self.assertTrue(city._is_full_face_solid(cell(x, y, z - 1)))
            self.assertIn((x + 1, z), seen)
        self.assertEqual("canopycavern:chests/underground_village_treasury",
                         city.block_nbts[55, 1, 55]["LootTable"])

    def test_entry_boulevard_has_evenly_spaced_supported_lighting(self):
        for z in range(4, 40, 6):
            for x in (48, 52):
                self.assertEqual("minecraft:lantern", self.city.grid[x, 3, z][0])
                self.assertTrue(self.city._is_full_face_solid(self.city.grid[x, 2, z][0]))
                self.assertTrue(all(self.city.grid[50, y, z][0] == "minecraft:air" for y in (1, 2)))

    def test_north_portal_is_only_open_seam_and_lamps_are_supported(self):
        city = self.city
        openings = {(x, y, 0) for x in range(49, 52) for y in range(1, 5)}
        city.verify_watertight("Mining City", [(50, 1, 1)], allowed_portals=openings)
        city.validate("Mining City")
        for x, y, z in openings:
            self.assertEqual("minecraft:air", city.grid[x, y, z][0])
            self.assertEqual("minecraft:air", city.grid[x, y, z + 1][0])

    def test_checked_in_template_matches_generator(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(v3, "STRUCT_DIR", Path(directory)):
                self.city.save(ASSET)
            regenerated = gzip.decompress((Path(directory) / ASSET).read_bytes())
        self.assertEqual(regenerated, gzip.decompress((v3.STRUCT_DIR / ASSET).read_bytes()))
