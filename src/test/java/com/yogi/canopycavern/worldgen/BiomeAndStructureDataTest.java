package com.yogi.canopycavern.worldgen;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.zip.GZIPInputStream;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

class BiomeAndStructureDataTest {
	@Test
	void exposesThreeCohesiveCustomBiomes() {
		assertEquals(3, ModBiomes.ALL_BIOMES.size());
		List<String> expected = List.of("whispering_peaks", "mossy_canopy", "verdant_grotto");
		List<String> actual = ModBiomes.ALL_BIOMES.stream().map(k -> k.identifier().getPath()).toList();
		assertEquals(expected, actual);

		for (String biome : expected) {
			JsonObject root = readJson("data/canopycavern/worldgen/biome/" + biome + ".json");
			assertTrue(root.has("attributes"), biome + " should define 26.3 attributes");
			assertTrue(root.has("effects"), biome + " should define effects");
			JsonArray features = root.getAsJsonArray("features");
			assertEquals(11, features.size(), biome + " must define all 11 feature steps");
		}
	}

	@Test
	void registersBiomesInOverworldAndCategoryTags() {
		JsonObject overworldTag = readJson("data/minecraft/tags/worldgen/biome/is_overworld.json");
		assertEquals(false, overworldTag.get("replace").getAsBoolean());
		String raw = overworldTag.getAsJsonArray("values").toString();
		assertTrue(raw.contains("canopycavern:whispering_peaks"));
		assertTrue(raw.contains("canopycavern:mossy_canopy"));
		assertTrue(raw.contains("canopycavern:verdant_grotto"));

		JsonObject mountainTag = readJson("data/minecraft/tags/worldgen/biome/is_mountain.json");
		assertTrue(mountainTag.getAsJsonArray("values").toString().contains("canopycavern:whispering_peaks"));

		JsonObject forestTag = readJson("data/minecraft/tags/worldgen/biome/is_forest.json");
		assertTrue(forestTag.getAsJsonArray("values").toString().contains("canopycavern:mossy_canopy"));
	}

	@Test
	void configuresValidJigsawStructuresTemplatesSetsNbtAndLootTables() throws IOException {
		assertStructureBundle(
			"peak_watchtower_ruin",
			"peak_watchtower_ruins",
			"surface_structures",
			"canopycavern:chests/peak_watchtower"
		);
		assertStructureBundle(
			"cavern_shrine",
			"cavern_shrines",
			"underground_structures",
			"canopycavern:chests/cavern_shrine"
		);
	}

	private static void assertStructureBundle(
		String structureName,
		String structureSetName,
		String expectedStep,
		String expectedLootTable
	) throws IOException {
		JsonObject structure = readJson("data/canopycavern/worldgen/structure/" + structureName + ".json");
		assertEquals("minecraft:jigsaw", structure.get("type").getAsString());
		assertEquals(expectedStep, structure.get("step").getAsString());
		assertEquals("canopycavern:" + structureName + "/start", structure.get("start_pool").getAsString());

		JsonObject structureSet = readJson("data/canopycavern/worldgen/structure_set/" + structureSetName + ".json");
		assertTrue(structureSet.getAsJsonArray("structures").toString().contains("canopycavern:" + structureName));

		JsonObject pool = readJson("data/canopycavern/worldgen/template_pool/" + structureName + "/start.json");
		assertEquals(
			"canopycavern:" + structureName,
			pool.getAsJsonArray("elements")
				.get(0).getAsJsonObject()
				.getAsJsonObject("element")
				.get("location").getAsString()
		);

		String nbtPath = "data/canopycavern/structure/" + structureName + ".nbt";
		byte[] compressed = readBytes(nbtPath);
		byte[] uncompressed;
		try (GZIPInputStream gzip = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
			uncompressed = gzip.readAllBytes();
		}
		String nbtAscii = new String(uncompressed, StandardCharsets.ISO_8859_1);
		assertTrue(nbtAscii.contains("DataVersion"), nbtPath + " missing DataVersion");
		assertTrue(nbtAscii.contains("minecraft:chest"), nbtPath + " missing loot chest block");
		assertTrue(nbtAscii.contains(expectedLootTable), nbtPath + " missing loot table " + expectedLootTable);

		String lootRel = expectedLootTable.replace("canopycavern:", "data/canopycavern/loot_table/") + ".json";
		JsonObject lootTable = readJson(lootRel);
		assertEquals("minecraft:chest", lootTable.get("type").getAsString());
		assertTrue(lootTable.getAsJsonArray("pools").size() >= 2);
		assertEquals(expectedLootTable, lootTable.get("random_sequence").getAsString());
	}

	private static JsonObject readJson(String resourcePath) {
		try {
			String text = new String(readBytes(resourcePath), StandardCharsets.UTF_8);
			return JsonParser.parseString(text).getAsJsonObject();
		} catch (IOException ex) {
			throw new AssertionError("Failed to read " + resourcePath, ex);
		}
	}

	private static byte[] readBytes(String resourcePath) throws IOException {
		try (InputStream in = BiomeAndStructureDataTest.class.getClassLoader().getResourceAsStream(resourcePath)) {
			assertNotNull(in, "Missing classpath resource: " + resourcePath);
			return in.readAllBytes();
		}
	}
}
