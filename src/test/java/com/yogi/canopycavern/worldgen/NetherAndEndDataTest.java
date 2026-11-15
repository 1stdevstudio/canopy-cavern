package com.yogi.canopycavern.worldgen;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

class NetherAndEndDataTest {

	private static final List<String> NETHER_STRUCTURES = List.of(
		"cinder_vault_bastion",
		"soul_catacomb_reliquary",
		"basalt_thermal_spire"
	);

	private static final List<String> END_STRUCTURES = List.of(
		"chorus_monastery_citadel",
		"void_beacon_observatory",
		"ender_archive_vault"
	);

	@Test
	void netherStructuresUseNetherCavernJigsawWithinSafeYBand() {
		Set<Integer> salts = new HashSet<>();
		for (String id : NETHER_STRUCTURES) {
			JsonObject def = readJson("data/canopycavern/worldgen/structure/" + id + ".json");
			assertEquals("canopycavern:nether_cavern_jigsaw", def.get("type").getAsString(), id);
			assertEquals("underground_structures", def.get("step").getAsString(), id);
			assertEquals("none", def.get("terrain_adaptation").getAsString(), id);
			JsonObject guard = def.getAsJsonObject("cavern_guard");
			assertNotNull(guard, id + " missing cavern_guard");
			assertTrue(guard.get("min_floor_y").getAsInt() >= 33, id);
			assertTrue(guard.get("max_ceiling_y").getAsInt() <= 118, id);
			assertTrue(guard.get("min_headroom").getAsInt() >= 14, id);
			assertTrue(guard.get("min_rigid_pieces").getAsInt() >= 1, id);

			JsonObject set = readJson("data/canopycavern/worldgen/structure_set/" + id + ".json");
			assertTrue(salts.add(set.getAsJsonObject("placement").get("salt").getAsInt()), "Duplicate salt for " + id);

			JsonObject biomeTag = readJson("data/canopycavern/tags/worldgen/biome/has_structure/" + id + ".json");
			assertTrue(biomeTag.getAsJsonArray("values").size() >= 1, id);
		}
	}

	@Test
	void endStructuresEnforceOuterIslandExclusionAndSolidThickness() {
		Set<Integer> salts = new HashSet<>();
		Set<String> forbiddenEndBiomes = Set.of(
			"minecraft:the_end",
			"minecraft:small_end_islands",
			"minecraft:end_barrens"
		);
		for (String id : END_STRUCTURES) {
			JsonObject def = readJson("data/canopycavern/worldgen/structure/" + id + ".json");
			assertEquals("canopycavern:surface_jigsaw", def.get("type").getAsString(), id);
			assertEquals("surface_structures", def.get("step").getAsString(), id);
			JsonObject guard = def.getAsJsonObject("terrain_guard");
			assertNotNull(guard, id + " missing terrain_guard");
			assertFalse(guard.get("allow_water").getAsBoolean(), id);
			int minThickness = guard.get("min_solid_thickness").getAsInt();
			assertTrue(minThickness >= 6, id + " needs island base thickness check");
			if ("ender_archive_vault".equals(id)) {
				assertTrue(minThickness >= 14, id + " embedded vault must require thick island base");
			}

			JsonObject set = readJson("data/canopycavern/worldgen/structure_set/" + id + ".json");
			assertTrue(salts.add(set.getAsJsonObject("placement").get("salt").getAsInt()), "Duplicate salt for " + id);

			JsonObject biomeTag = readJson("data/canopycavern/tags/worldgen/biome/has_structure/" + id + ".json");
			for (JsonElement value : biomeTag.getAsJsonArray("values")) {
				String biome = value.getAsString();
				assertFalse(forbiddenEndBiomes.contains(biome), id + " must exclude dragon/barren/small islands: " + biome);
				assertTrue(
					biome.equals("minecraft:end_highlands") || biome.equals("minecraft:end_midlands"),
					id + " unexpected End biome: " + biome
				);
			}
		}
	}

	@Test
	void dimensionalLootTablesUseMc263ModifierSyntax() {
		for (String loot : List.of(
			"nether_bastion_vault",
			"nether_bastion_supply",
			"nether_soul_reliquary",
			"nether_thermal_spire",
			"end_monastery_vault",
			"end_observatory_cache",
			"end_archive_vault"
		)) {
			JsonObject table = readJson("data/canopycavern/loot_table/chests/" + loot + ".json");
			String raw = table.toString();
			assertFalse(raw.contains("\"functions\""), loot + " must use 26.3 'modifier' instead of 'functions'");
			assertTrue(raw.contains("\"modifier\""), loot + " expected 26.3 'modifier' field");
		}
	}

	private static JsonObject readJson(String path) {
		try (InputStream in = NetherAndEndDataTest.class.getClassLoader().getResourceAsStream(path)) {
			assertNotNull(in, "Missing resource: " + path);
			return JsonParser.parseString(new String(in.readAllBytes(), StandardCharsets.UTF_8)).getAsJsonObject();
		} catch (IOException ex) {
			throw new AssertionError("Failed reading " + path, ex);
		}
	}
}
