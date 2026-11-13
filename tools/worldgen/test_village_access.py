import unittest

from generate_v04_ocean_and_villages import THEMES, draw_revamp_house


class VillageAccessTest(unittest.TestCase):
    def test_gatehouse_ladders_reach_guarded_walkable_roof(self):
        for theme, palette in THEMES.items():
            with self.subTest(theme=theme):
                house = draw_revamp_house(theme, palette, "bastion_gatehouse")
                for shaft_x, landing_x in ((1, 2), (11, 10)):
                    for y in range(1, 12):
                        self.assertEqual("minecraft:ladder", house.grid[shaft_x, y, 5][0])
                    self.assertEqual(palette["plinth"], house.grid[landing_x, 11, 5][0])
                    for y in (12, 13):
                        for x in (shaft_x, landing_x):
                            self.assertEqual("minecraft:air", house.grid[x, y, 5][0])
                for left, right in ((0, 4), (8, 12)):
                    for x in range(left, right + 1):
                        for z in range(4, 12):
                            if x in (left, right) or z in (4, 11):
                                self.assertEqual(palette["fence"], house.grid[x, 12, z][0])

    def test_market_loft_ladder_has_clear_exit_and_guarded_sides(self):
        for theme, palette in THEMES.items():
            with self.subTest(theme=theme):
                house = draw_revamp_house(theme, palette, "market_pavilion")
                for y in (6, 7):
                    for z in (8, 9):
                        self.assertEqual("minecraft:air", house.grid[7, y, z][0])
                self.assertEqual(palette["floor"], house.grid[7, 5, 8][0])
                for x in (6, 8):
                    self.assertEqual(palette["fence"], house.grid[x, 6, 9][0])

    def test_gatehouse_bed_stays_inside_window_wall(self):
        for theme, palette in THEMES.items():
            with self.subTest(theme=theme):
                house = draw_revamp_house(theme, palette, "bastion_gatehouse")
                self.assertEqual(palette["bed"], house.grid[2, 7, 10][0])
                self.assertEqual(palette["bed"], house.grid[2, 7, 9][0])
                self.assertEqual("head", dict(house.grid[2, 7, 10][1])["part"])
                self.assertEqual("south", dict(house.grid[2, 7, 9][1])["facing"])

                self.assertEqual(palette["plinth"], house.grid[2, 7, 11][0])
                self.assertEqual(palette["pane"], house.grid[2, 8, 11][0])
