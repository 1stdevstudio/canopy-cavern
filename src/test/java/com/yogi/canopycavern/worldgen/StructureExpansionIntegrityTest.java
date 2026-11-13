package com.yogi.canopycavern.worldgen;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.io.DataInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Stream;
import java.util.zip.GZIPInputStream;

import static org.junit.jupiter.api.Assertions.*;

class StructureExpansionIntegrityTest {
    private static final Path ROOT = Path.of("src/main/resources/data");
    private static final List<String> NEW_VILLAGES = List.of(
        "jungle_canopy_hamlet", "mangrove_marsh_village", "badlands_pueblo",
        "cherry_grove_hamlet", "mushroom_island_outpost", "frozen_ridge_village",
        "underground_hollow_village"
    );
    private static final String ABANDONED = "abandoned_mega_village";

    @Test
    void newVillagesHaveValidGenerationDefinitionsAndMatchingBiomes() throws Exception {
        for (String id : allNewStructures()) {
            JsonObject structure = json(ROOT.resolve("canopycavern/worldgen/structure/" + id + ".json"));
            JsonObject structureSet = json(ROOT.resolve("canopycavern/worldgen/structure_set/" + id + ".json"));
            JsonObject tag = json(ROOT.resolve("canopycavern/tags/worldgen/biome/has_structure/" + id + ".json"));
            JsonObject pool = json(ROOT.resolve("canopycavern/worldgen/template_pool/" + id + "/start.json"));
            assertEquals("minecraft:jigsaw", structure.get("type").getAsString(), id);
            assertEquals("#canopycavern:has_structure/" + id, structure.get("biomes").getAsString(), id);
            assertEquals("canopycavern:" + id + "/start", structure.get("start_pool").getAsString(), id);
            assertEquals(1, structure.get("size").getAsInt(), id + " must not rely on nonexistent jigsaw attachments");
            assertTrue(tag.getAsJsonArray("values").size() >= 1, id);
            assertEquals("minecraft:random_spread", structureSet.getAsJsonObject("placement").get("type").getAsString(), id);
            JsonObject placement = structureSet.getAsJsonObject("placement");
            assertTrue(placement.get("spacing").getAsInt() > placement.get("separation").getAsInt(), id);
            assertTrue(placement.get("separation").getAsInt() > 0, id);
            assertEquals("canopycavern:" + id,
                structureSet.getAsJsonArray("structures").get(0).getAsJsonObject().get("structure").getAsString(), id);
            JsonArray elements = pool.getAsJsonArray("elements");
            assertEquals(1, elements.size(), id);
            assertEquals("canopycavern:" + id + "/center",
                elements.get(0).getAsJsonObject().getAsJsonObject("element").get("location").getAsString(), id);
            if (id.equals("underground_hollow_village")) {
                assertEquals("underground_structures", structure.get("step").getAsString());
                assertEquals("encapsulate", structure.get("terrain_adaptation").getAsString());
            } else {
                assertEquals("surface_structures", structure.get("step").getAsString());
            }
        }
    }

    @Test
    void allNewTemplatesAreWellFormedAndVillagersAndLootMatchPurpose() throws Exception {
        for (String id : allNewStructures()) {
            Path path = ROOT.resolve("canopycavern/structure/" + id + "/center.nbt");
            Map<String,Object> nbt = readNbt(path);
            assertEquals(5023, nbt.get("DataVersion"), id);
            List<?> size = list(nbt, "size");
            int width = (int) size.get(0), height = (int) size.get(1), depth = (int) size.get(2);
            assertTrue(width <= 48 && height <= 48 && depth <= 48, id + " exceeds structure block limit");

            List<?> palette = list(nbt, "palette");
            List<?> blocks = list(nbt, "blocks");
            List<?> entities = list(nbt, "entities");
            assertFalse(blocks.isEmpty(), id);
            assertFalse(palette.isEmpty(), id);
            Set<String> uniquePositions = new HashSet<>();
            int chestCount = 0;
            int beds = 0;
            for (Object blockObject : blocks) {
                Map<String,Object> block = map(blockObject);
                List<?> pos = list(block, "pos");
                int x = (int) pos.get(0), y = (int) pos.get(1), z = (int) pos.get(2);
                assertTrue(x >= 0 && y >= 0 && z >= 0 && x < width && y < height && z < depth, id + ": " + pos);
                assertTrue(uniquePositions.add(x + ":" + y + ":" + z), id + " duplicate block at " + pos);
                int state = (int) block.get("state");
                assertTrue(state >= 0 && state < palette.size(), id + ": invalid palette state " + state);
                String blockId = String.valueOf(map(palette.get(state)).get("id"));
                if (blockId.equals("minecraft:chest")) {
                    chestCount++;
                    assertEquals(id.equals(ABANDONED) ? "canopycavern:chests/abandoned_mega_village" : "canopycavern:chests/village_supply",
                        map(block.get("nbt")).get("LootTable"), id);
                }
                if (blockId.endsWith("_bed")) beds++;
            }
            long villagers = entities.stream().filter(e ->
                "minecraft:villager".equals(map(map(e).get("nbt")).get("id"))).count();
            long guardians = entities.stream().filter(e ->
                "canopycavern:village_sentinel".equals(map(map(e).get("nbt")).get("id"))
                || "minecraft:iron_golem".equals(map(map(e).get("nbt")).get("id"))).count();
            if (id.equals(ABANDONED)) {
                assertEquals(0, villagers, "Abandoned village must not spawn living villagers");
                assertTrue(chestCount >= 2, "Abandoned village needs its exploration reward");
                assertTrue(entities.size() >= 2, "Abandoned village needs some threat");
            } else {
                assertTrue(villagers >= 4, id + " needs inhabitants");
                assertTrue(guardians >= 1, id + " needs protection");
                assertTrue(beds >= villagers * 2, id + " needs a complete 2-block bed for each villager");
            }
        }
    }

    @Test
    void everyCustomJigsawPoolPointsToPresentNbtAndHasValidFallback() throws Exception {
        Path poolRoot = ROOT.resolve("canopycavern/worldgen/template_pool");
        try (Stream<Path> files = Files.walk(poolRoot)) {
            for (Path file : files.filter(p -> p.toString().endsWith(".json")).toList()) {
                JsonObject root = json(file);
                assertTrue(root.has("fallback"), file.toString());
                String fallback = root.get("fallback").getAsString();
                if (fallback.startsWith("canopycavern:")) {
                    String relative = fallback.substring("canopycavern:".length());
                    assertTrue(Files.exists(poolRoot.resolve(relative + ".json")), file + " missing fallback " + fallback);
                }
                for (var entry : root.getAsJsonArray("elements")) {
                    JsonObject element = entry.getAsJsonObject().getAsJsonObject("element");
                    String kind = element.get("element_type").getAsString();
                    if (kind.equals("minecraft:single_pool_element") || kind.equals("minecraft:legacy_single_pool_element")) {
                        String loc = element.get("location").getAsString();
                        if (loc.startsWith("canopycavern:")) {
                            Path nbtPath = ROOT.resolve("canopycavern/structure/" +
                                loc.substring("canopycavern:".length()) + ".nbt");
                            assertTrue(Files.exists(nbtPath), file + " references missing " + nbtPath);
                        }
                    }
                    assertTrue(entry.getAsJsonObject().get("weight").getAsInt() >= 1, file.toString());
                }
            }
        }
    }

    @Test
    void villageGeometryDoesNotBreakBedsDoorsLightsOrSpawnPoints() throws Exception {
        for (String id : allNewStructures()) {
            Map<String,Object> data = readNbt(ROOT.resolve("canopycavern/structure/" + id + "/center.nbt"));
            List<?> palette = list(data, "palette");
            Map<String,String> blocks = new HashMap<>();
            Map<String,Map<String,Object>> properties = new HashMap<>();
            for (Object obj : list(data, "blocks")) {
                Map<String,Object> b = map(obj);
                List<?> p = list(b, "pos");
                String at = p.get(0) + ":" + p.get(1) + ":" + p.get(2);
                Map<String,Object> entry = map(palette.get((int)b.get("state")));
                blocks.put(at, String.valueOf(entry.get("id")));
                properties.put(at, entry.containsKey("properties") ? map(entry.get("properties")) : Map.of());
            }
            for (Object obj : list(data, "blocks")) {
                Map<String,Object> block = map(obj);
                List<?> pos = list(block, "pos");
                int x = (int)pos.get(0), y = (int)pos.get(1), z = (int)pos.get(2);
                String at = x + ":" + y + ":" + z;
                String blockId = blocks.get(at);
                Map<String,Object> props = properties.get(at);
                if (blockId.endsWith("_door")) {
                    String otherPos = x + ":" + (y + ("lower".equals(props.get("half")) ? 1 : -1)) + ":" + z;
                    assertEquals(blockId, blocks.get(otherPos), id + " has half of a broken two-block door at " + at);
                    assertEquals("lower".equals(props.get("half")) ? "upper" : "lower",
                        properties.getOrDefault(otherPos, Map.of()).get("half"), id + " has invalid door half " + at);
                }
                if (blockId.endsWith("_bed")) {
                    assertTrue(props.containsKey("part"), id + " bed missing part at " + at);
                    String facing = String.valueOf(props.get("facing"));
                    int offsetX = "east".equals(facing) ? 1 : "west".equals(facing) ? -1 : 0;
                    int offsetZ = "south".equals(facing) ? 1 : "north".equals(facing) ? -1 : 0;
                    int sign = "foot".equals(props.get("part")) ? 1 : -1;
                    String otherPos = (x + sign * offsetX) + ":" + y + ":" + (z + sign * offsetZ);
                    assertEquals(blockId, blocks.get(otherPos), id + " half of the bed missing at " + at);
                    assertEquals("foot".equals(props.get("part")) ? "head" : "foot",
                        properties.getOrDefault(otherPos, Map.of()).get("part"), id + " bed pairing invalid at " + at);
                }
                if (blockId.equals("minecraft:lantern") && "true".equals(props.get("hanging"))) {
                    String above = blocks.get(x + ":" + (y+1) + ":" + z);
                    assertNotNull(above, id + " hanging lantern has no roof at " + at);
                    assertFalse(above.equals("minecraft:air"), id + " hanging lantern falls without solid support at " + at);
                }
                if (blockId.equals("minecraft:bell") && "floor".equals(props.get("attachment"))) {
                    String below = blocks.get(x + ":" + (y-1) + ":" + z);
                    assertNotNull(below, id + " bell has no floor support");
                    assertFalse(below.equals("minecraft:air") || below.equals("minecraft:water")
                        || below.equals("minecraft:lava"), id + " bell is supported by liquid/air");
                }
            }
            for (Object obj : list(data, "entities")) {
                Map<String,Object> e = map(obj);
                List<?> blockPos = list(e, "blockPos");
                int x = (int)blockPos.get(0), y = (int)blockPos.get(1), z = (int)blockPos.get(2);
                String idAt = blocks.get(x + ":" + y + ":" + z);
                assertFalse("minecraft:stone_bricks".equals(idAt) || "minecraft:deepslate_bricks".equals(idAt),
                    id + " spawned an entity intersecting solid walls at " + blockPos);
            }
        }
    }


    @Test
    void frontierPillagerOutpostHasFunctionalTemplateAndDoesNotReplaceVanillaOutpost() throws Exception {
        String id = "frontier_pillager_outpost";
        JsonObject def = json(ROOT.resolve("canopycavern/worldgen/structure/" + id + ".json"));
        JsonObject set = json(ROOT.resolve("canopycavern/worldgen/structure_set/" + id + ".json"));
        JsonObject tag = json(ROOT.resolve("canopycavern/tags/worldgen/biome/has_structure/" + id + ".json"));
        JsonObject pool = json(ROOT.resolve("canopycavern/worldgen/template_pool/" + id + "/start.json"));
        assertEquals("minecraft:jigsaw", def.get("type").getAsString());
        assertEquals("surface_structures", def.get("step").getAsString());
        assertEquals("canopycavern:" + id + "/start", def.get("start_pool").getAsString());
        assertTrue(set.getAsJsonArray("structures").toString().contains("canopycavern:" + id));
        assertEquals("canopycavern:" + id + "/center",
            pool.getAsJsonArray("elements").get(0).getAsJsonObject()
                .getAsJsonObject("element").get("location").getAsString());
        assertTrue(tag.getAsJsonArray("values").size() >= 4);
        assertFalse(Files.exists(ROOT.resolve("minecraft/worldgen/structure/pillager_outpost.json")),
            "Do not overwrite vanilla Pillager Outpost's structure definition");

        Map<String,Object> nbt = readNbt(ROOT.resolve("canopycavern/structure/" + id + "/center.nbt"));
        assertEquals(5023, nbt.get("DataVersion"));
        List<?> palette = list(nbt, "palette"), blocks = list(nbt, "blocks"), entities = list(nbt, "entities");
        assertFalse(blocks.isEmpty());
        Set<String> locations = new HashSet<>();
        int ladders = 0, ironBars = 0, lootChests = 0;
        for (Object o : blocks) {
            Map<String,Object> block = map(o);
            List<?> p = list(block, "pos");
            assertTrue(locations.add(p.get(0) + ":" + p.get(1) + ":" + p.get(2)), "duplicate outpost coordinate");
            int state = (int)block.get("state");
            assertTrue(state >= 0 && state < palette.size());
            String blockId = String.valueOf(map(palette.get(state)).get("id"));
            if (blockId.equals("minecraft:ladder")) ladders++;
            if (blockId.equals("minecraft:iron_bars")) ironBars++;
            if (blockId.equals("minecraft:chest")) {
                lootChests++;
                assertEquals("canopycavern:chests/frontier_pillager_outpost",
                    map(block.get("nbt")).get("LootTable"));
            }
        }
        assertTrue(ladders >= 8, "Watchtower needs climbable access");
        assertTrue(ironBars >= 10, "Golem cage should be physically present");
        assertTrue(lootChests >= 1);
        long pillagers = entities.stream().filter(o ->
            "minecraft:pillager".equals(map(map(o).get("nbt")).get("id"))).count();
        long golems = entities.stream().filter(o ->
            "minecraft:iron_golem".equals(map(map(o).get("nbt")).get("id"))).count();
        long villagers = entities.stream().filter(o ->
            "minecraft:villager".equals(map(map(o).get("nbt")).get("id"))).count();
        assertTrue(pillagers >= 3);
        assertTrue(golems >= 1);
        assertEquals(0, villagers, "This is a hostile Pillager outpost, not a village");
        JsonObject loot = json(ROOT.resolve("canopycavern/loot_table/chests/" + id + ".json"));
        assertEquals("minecraft:chest", loot.get("type").getAsString());
    }

    private static List<String> allNewStructures() {
        List<String> all = new ArrayList<>(NEW_VILLAGES);
        all.add(ABANDONED);
        return all;
    }

    private static JsonObject json(Path file) throws IOException {
        return JsonParser.parseString(Files.readString(file, StandardCharsets.UTF_8)).getAsJsonObject();
    }

    @SuppressWarnings("unchecked")
    private static Map<String,Object> map(Object value) {
        assertInstanceOf(Map.class, value);
        return (Map<String,Object>) value;
    }

    private static List<?> list(Map<String,Object> obj, String key) {
        assertInstanceOf(List.class, obj.get(key), key);
        return (List<?>) obj.get(key);
    }

    private static Map<String,Object> readNbt(Path file) throws IOException {
        try (InputStream raw = Files.newInputStream(file);
             GZIPInputStream gzip = new GZIPInputStream(raw);
             DataInputStream in = new DataInputStream(gzip)) {
            assertEquals(10, in.readUnsignedByte(), file + " must contain a root TAG_Compound");
            assertEquals("", in.readUTF(), file + " should use unnamed root");
            Map<String,Object> root = map(readPayload(in, 10));
            assertEquals(-1, in.read(), file + " trailing compressed NBT data");
            return root;
        }
    }

    private static Object readPayload(DataInputStream in, int type) throws IOException {
        return switch (type) {
            case 1 -> in.readByte();
            case 2 -> in.readShort();
            case 3 -> in.readInt();
            case 4 -> in.readLong();
            case 5 -> in.readFloat();
            case 6 -> in.readDouble();
            case 7 -> {
                int count = checkedSize(in.readInt());
                byte[] bytes = new byte[count];
                in.readFully(bytes);
                yield bytes;
            }
            case 8 -> in.readUTF();
            case 9 -> {
                int elementType = in.readUnsignedByte(), count = checkedSize(in.readInt());
                List<Object> values = new ArrayList<>(count);
                for (int i = 0; i < count; i++) values.add(readPayload(in, elementType));
                yield values;
            }
            case 10 -> {
                Map<String,Object> values = new HashMap<>();
                int next;
                while ((next = in.readUnsignedByte()) != 0) {
                    values.put(in.readUTF(), readPayload(in, next));
                }
                yield values;
            }
            case 11 -> {
                int count = checkedSize(in.readInt());
                List<Integer> values = new ArrayList<>(count);
                for (int i = 0; i < count; i++) values.add(in.readInt());
                yield values;
            }
            case 12 -> {
                int count = checkedSize(in.readInt());
                List<Long> values = new ArrayList<>(count);
                for (int i = 0; i < count; i++) values.add(in.readLong());
                yield values;
            }
            default -> throw new IOException("Unsupported NBT type " + type);
        };
    }

    private static int checkedSize(int count) throws IOException {
        if (count < 0 || count > 1_000_000) throw new IOException("Invalid NBT length " + count);
        return count;
    }
}
