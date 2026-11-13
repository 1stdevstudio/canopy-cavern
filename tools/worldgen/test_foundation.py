import unittest

import generate_v04_ocean_and_villages as generator


class FoundationTest(unittest.TestCase):
    def test_foundation_moves_chest_and_jigsaw_metadata_with_blocks(self):
        builder = generator.V4StructureBuilder(7, 8, 7)
        builder.chest(3, 2, 3, "north", "canopycavern:chests/test")
        builder.jigsaw(3, 2, 5, "south_up", "canopycavern:test",
                       "canopycavern:test", "minecraft:empty", "minecraft:stone")
        original = dict(builder.block_nbts)
        builder.extend_seabed_foundation(6)
        self.assertEqual({(x, y + 6, z): value for (x, y, z), value in original.items()},
                         builder.block_nbts)

    def test_foundation_moves_entity_using_valid_nbt_lists(self):
        builder = generator.V4StructureBuilder(7, 8, 7)
        builder.add_entity(3.5, 2.0, 3.5, "minecraft:guardian")
        builder.extend_seabed_foundation(6)
        entity = builder.entities[0]
        self.assertEqual([3.5, 8.0, 3.5], entity["pos"].value)
        self.assertEqual(9, entity["blockPos"].tag_type)
        self.assertEqual(3, entity["blockPos"].elem_type)
        self.assertEqual([3, 8, 3], entity["blockPos"].value)
        encoded = bytearray()
        generator.v3.encode_nbt_payload(encoded, generator.v3.TAG_COMPOUND, entity)
        self.assertTrue(encoded)


if __name__ == "__main__":
    unittest.main()
