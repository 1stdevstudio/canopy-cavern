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
	void exposesFiveCohesiveCustomBiomes() {
		assertEquals(5, ModBiomes.ALL_BIOMES.size());
		List<String> expected = List.of(
			"whispering_peaks",
			"mossy_canopy",
			"verdant_grotto",
			"crystal_steppe",
			"amber_caverns"
		);
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
		assertTrue(raw.contains("canopycavern:crystal_steppe"));
		assertTrue(raw.contains("canopycavern:amber_caverns"));

		JsonObject mountainTag = readJson("data/minecraft/tags/worldgen/biome/is_mountain.json");
		assertTrue(mountainTag.getAsJsonArray("values").toString().contains("canopycavern:whispering_peaks"));

		JsonObject forestTag = readJson("data/minecraft/tags/worldgen/biome/is_forest.json");
		assertTrue(forestTag.getAsJsonArray("values").toString().contains("canopycavern:mossy_canopy"));
	}

	@Test
	void configuresOceanMegaStructuresGrandMonumentAndLootTables() throws IOException {
		assertMultiPieceStructure(
			"sunken_citadel_vault",
			"sunken_citadel_vaults",
			"sunken_citadel_vault/central_vault",
			"canopycavern:chests/sunken_citadel"
		);
		assertMultiPieceStructure(
			"abyssal_thermal_observatory",
			"abyssal_thermal_observatories",
			"abyssal_thermal_observatory/main_dome",
			"canopycavern:chests/thermal_observatory"
		);
		assertMultiPieceStructure(
			"reef_lighthouse_keep",
			"reef_lighthouse_keeps",
			"reef_lighthouse_keep/island_keep_anchored",
			"canopycavern:chests/armada_treasure"
		);
		assertMultiPieceStructure(
			"abyssal_sanctum_monument",
			"abyssal_sanctum_monument",
			"abyssal_sanctum_monument/grand_rotunda",
			"canopycavern:chests/abyssal_monument"
		);

		JsonObject tideTag = readJson("data/canopycavern/tags/worldgen/structure/tide_compass_targets.json");
		String tideValues = tideTag.getAsJsonArray("values").toString();
		assertTrue(tideValues.contains("canopycavern:sunken_citadel_vault"));
		assertTrue(tideValues.contains("canopycavern:abyssal_thermal_observatory"));
		assertTrue(tideValues.contains("canopycavern:reef_lighthouse_keep"));

		JsonObject relicTag = readJson("data/canopycavern/tags/worldgen/structure/relic_compass_targets.json");
		assertTrue(relicTag.getAsJsonArray("values").toString().contains("canopycavern:abyssal_sanctum_monument"));
	}

	@Test
	void configuresRevampedVanillaVillagesWithGroundOutdoorSentinelsAndValidOrientations() throws Exception {
		for (String theme : List.of("plains", "desert", "savanna", "snowy", "taiga")) {
			JsonObject tcPool = readJson("data/minecraft/worldgen/template_pool/village/" + theme + "/town_centers.json");
			assertTrue(tcPool.getAsJsonArray("elements").toString().contains("canopycavern:vanilla_revamp/" + theme + "/grand_town_center"));
			assertPoolWeightsValid(tcPool, theme + "/town_centers.json");
			JsonObject housesPool = readJson("data/minecraft/worldgen/template_pool/village/" + theme + "/houses.json");
			assertPoolWeightsValid(housesPool, theme + "/houses.json");
			String housesRaw = housesPool.getAsJsonArray("elements").toString();
			assertTrue(housesRaw.contains("canopycavern:vanilla_revamp/" + theme + "/grand_manor"));
			assertTrue(housesRaw.contains("canopycavern:vanilla_revamp/" + theme + "/bastion_gatehouse"));

			assertRevampNbtIntegrity(theme, "grand_town_center", 9, 5, 2);
			assertRevampNbtIntegrity(theme, "bastion_gatehouse", 4, 2, 1);
			assertRevampNbtIntegrity(theme, "guild_smithy", 3, 2, 0);
			assertRevampNbtIntegrity(theme, "market_pavilion", 3, 3, 0);
			assertRevampNbtIntegrity(theme, "grand_manor", 2, 3, 0);
			assertRevampNbtIntegrity(theme, "sanctuary_library", 2, 3, 0);
		}
	}

	private static void assertPoolWeightsValid(JsonObject pool, String label) {
		for (var el : pool.getAsJsonArray("elements")) {
			int w = el.getAsJsonObject().get("weight").getAsInt();
			assertTrue(w >= 1 && w <= 150, label + " weight " + w + " outside vanilla [1..150] range");
		}
	}

	private static void assertMultiPieceStructure(
		String structureId,
		String setId,
		String mainNbtRel,
		String expectedLootTable
	) throws IOException {
		JsonObject def = readJson("data/canopycavern/worldgen/structure/" + structureId + ".json");
		assertEquals("minecraft:jigsaw", def.get("type").getAsString());
		JsonObject set = readJson("data/canopycavern/worldgen/structure_set/" + setId + ".json");
		assertTrue(set.getAsJsonArray("structures").toString().contains("canopycavern:" + structureId));

		String nbtPath = "data/canopycavern/structure/" + mainNbtRel + ".nbt";
		String ascii = decompressNbtLatin1(nbtPath);
		assertTrue(ascii.contains("DataVersion"), nbtPath + " missing DataVersion");
		assertTrue(ascii.contains("minecraft:chest"), nbtPath + " missing chest");
		assertTrue(ascii.contains(expectedLootTable), nbtPath + " missing loot " + expectedLootTable);

		String lootRel = expectedLootTable.replace("canopycavern:", "data/canopycavern/loot_table/") + ".json";
		JsonObject lootTable = readJson(lootRel);
		assertEquals("minecraft:chest", lootTable.get("type").getAsString());
		assertTrue(lootTable.getAsJsonArray("pools").size() >= 2, lootRel + " should have >= 2 pools");
		assertEquals(expectedLootTable, lootTable.get("random_sequence").getAsString());
	}

	private static void assertRevampNbtIntegrity(
		String theme,
		String piece,
		int minSentinels,
		int minVillagers,
		int minGolems
	) throws IOException {
		String nbtPath = "data/canopycavern/structure/vanilla_revamp/" + theme + "/" + piece + ".nbt";
		String ascii = decompressNbtLatin1(nbtPath);
		assertTrue(ascii.contains("DataVersion"), nbtPath + " missing DataVersion");
		assertEquals(true, countOccurrences(ascii, "canopycavern:village_sentinel") >= minSentinels,
			nbtPath + " expected >= " + minSentinels + " sentinels");
		assertEquals(true, countOccurrences(ascii, "minecraft:villager") >= minVillagers,
			nbtPath + " expected >= " + minVillagers + " villagers");
		if (minGolems > 0) {
			assertEquals(true, countOccurrences(ascii, "minecraft:iron_golem") >= minGolems,
				nbtPath + " expected >= " + minGolems + " iron golems");
		}
	}

	private static String decompressNbtLatin1(String resourcePath) throws IOException {
		try (GZIPInputStream gzip = new GZIPInputStream(new ByteArrayInputStream(readBytes(resourcePath)))) {
			return new String(gzip.readAllBytes(), StandardCharsets.ISO_8859_1);
		}
	}

	private static int countOccurrences(String haystack, String needle) {
		int count = 0;
		int idx = 0;
		while ((idx = haystack.indexOf(needle, idx)) >= 0) {
			count++;
			idx += needle.length();
		}
		return count;
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
		assertStructureBundle(
			"canopy_treetop_bastion",
			"canopy_treetop_bastions",
			"surface_structures",
			"canopycavern:chests/canopy_bastion"
		);
		assertStructureBundle(
			"echoing_mineshaft_hub",
			"echoing_mineshaft_hubs",
			"underground_structures",
			"canopycavern:chests/echoing_mineshaft"
		);
	}

	@Test
	void configuresFourThemedVillagerCivilizationsAndSentinels() throws IOException {
		// Each village now gets its own random-spread placement. Combining mutually
		// exclusive biome targets into one weighted set suppressed valid generations.
		for (String villageId : List.of("crystal_citadel", "peak_citadel", "canopy_village", "grotto_outpost_town")) {
			JsonObject villageSet = readJson("data/canopycavern/worldgen/structure_set/" + villageId + ".json");
			assertTrue(villageSet.getAsJsonArray("structures").toString().contains("canopycavern:" + villageId));
			JsonObject structure = readJson("data/canopycavern/worldgen/structure/" + villageId + ".json");
			assertEquals("minecraft:jigsaw", structure.get("type").getAsString());
			assertEquals("canopycavern:" + villageId + "/start", structure.get("start_pool").getAsString());

			String centerPath = "data/canopycavern/structure/" + villageId + "/town_center.nbt";
			byte[] rawCenter;
			try (GZIPInputStream gzip = new GZIPInputStream(new ByteArrayInputStream(readBytes(centerPath)))) {
				rawCenter = gzip.readAllBytes();
			}
			String centerAscii = new String(rawCenter, StandardCharsets.ISO_8859_1);
			assertTrue(centerAscii.contains("canopycavern:common/village_sentinel"), centerPath + " must summon Village Sentinels");

			String guardPath = "data/canopycavern/structure/" + villageId + "/guardhouse.nbt";
			byte[] rawGuard;
			try (GZIPInputStream gzip = new GZIPInputStream(new ByteArrayInputStream(readBytes(guardPath)))) {
				rawGuard = gzip.readAllBytes();
			}
			String guardAscii = new String(rawGuard, StandardCharsets.ISO_8859_1);
			assertTrue(guardAscii.contains("canopycavern:chests/village_supply"), guardPath + " missing supply chest loot");
		}

		byte[] rawSentinel;
		try (GZIPInputStream gzip = new GZIPInputStream(new ByteArrayInputStream(readBytes("data/canopycavern/structure/common/village_sentinel.nbt")))) {
			rawSentinel = gzip.readAllBytes();
		}
		assertTrue(new String(rawSentinel, StandardCharsets.ISO_8859_1).contains("canopycavern:village_sentinel"));
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
		String template = switch (structureName) {
			case "cavern_shrine" -> "cavern_shrine/vaulted_nave";
		case "echoing_mineshaft_hub" -> "echoing_mineshaft_hub/ore_exchange";

			default -> structureName;
		};
		assertEquals(
			"canopycavern:" + template,
			pool.getAsJsonArray("elements")
				.get(0).getAsJsonObject()
				.getAsJsonObject("element")
				.get("location").getAsString()
		);

		String nbtPath = "data/canopycavern/structure/" + template + ".nbt";
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
