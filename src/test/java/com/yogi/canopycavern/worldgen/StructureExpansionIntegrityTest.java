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
