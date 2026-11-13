import unittest
from generate_cavern_city import build

class CityTest(unittest.TestCase):
    def test_districts_connected_to_crossroads(self):
        city = build()
        self.assertEqual((75, 30, 75), (city.sx, city.sy, city.sz))
        start = (37, 37)
        seen = {start}
        queue = [start]
        for x, z in queue:
            for dx, dz in ((0,1),(0,-1),(1,0),(-1,0)):
                point = (x+dx,z+dz)
                a,b = point
                if point in seen or not (0 <= a < 75 and 0 <= b < 75):
                    continue
                if all(city.grid[a,y,b][0] == "minecraft:air" or city.grid[a,y,b][0].endswith("_door") for y in (1,2)) and city.grid[a,0,b][0] not in ("minecraft:air","minecraft:structure_void"):
                    seen.add(point)
                    queue.append(point)
        for point in ((0,37),(74,37),(37,0),(37,74),(17,17),(57,17),(17,57),(57,57)):
            self.assertIn(point, seen)
        self.assertEqual(8, sum(e["nbt"]["id"] == "minecraft:villager" for e in city.entities))
