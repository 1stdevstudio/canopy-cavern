package com.yogi.canopycavern.worldgen;

import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.datafixers.util.Pair;
import net.minecraft.SharedConstants;
import net.minecraft.server.Bootstrap;
import net.minecraft.world.level.biome.Climate;
import net.minecraft.world.level.biome.OverworldBiomeBuilder;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import java.util.function.Consumer;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Builds the Canopy preset's biome list from vanilla's own climate layout and checks the
 * committed JSON is up to date. Regenerate with: ./gradlew test -Dcanopy.regenPreset=true
 */
class CanopyWorldPresetTest {
	static final Path PRESET = Path.of("src/main/resources/data/canopycavern/worldgen/world_preset/canopy.json");

	@BeforeAll
	static void bootstrap() {
		SharedConstants.tryDetectVersion();
		Bootstrap.bootStrap();
	}

	static List<Pair<Climate.ParameterPoint, String>> vanillaPoints() throws Exception {
		List<Pair<Climate.ParameterPoint, String>> points = new ArrayList<>();
		Method add = OverworldBiomeBuilder.class.getDeclaredMethod("addBiomes", Consumer.class);
		add.setAccessible(true);
		Consumer<Pair<Climate.ParameterPoint, net.minecraft.resources.ResourceKey<?>>> sink =
			pair -> points.add(Pair.of(pair.getFirst(), pair.getSecond().identifier().toString()));
		add.invoke(new OverworldBiomeBuilder(), sink);
		return points;
	}

	static JsonArray range(Climate.Parameter p) {
		JsonArray a = new JsonArray();
		a.add(Climate.unquantizeCoord(p.min()));
		a.add(Climate.unquantizeCoord(p.max()));
		return a;
	}

	static String build() throws Exception {
		JsonArray biomes = new JsonArray();
		List<Pair<Climate.ParameterPoint, String>> points = new ArrayList<>(vanillaPoints());
		// Canopy-only slots with no vanilla counterpart (same points the TerraBlender region uses).
		points.add(Pair.of(CanopyOverworldRegion.LUMINOUS_DEPTHS_POINT, "canopycavern:luminous_depths"));
		for (var pair : points) {
			String target = pair.getSecond().startsWith("canopycavern:") ? pair.getSecond()
				: CanopyBiomeMap.VANILLA_TO_CANOPY.get(pair.getSecond());
			assertNotNull(target, "No Canopy biome mapped for " + pair.getSecond());
			Climate.ParameterPoint p = pair.getFirst();
			JsonObject params = new JsonObject();
			params.add("temperature", range(p.temperature()));
			params.add("humidity", range(p.humidity()));
			params.add("continentalness", range(p.continentalness()));
			params.add("erosion", range(p.erosion()));
			params.add("weirdness", range(p.weirdness()));
			params.add("depth", range(p.depth()));
			params.addProperty("offset", Climate.unquantizeCoord(p.offset()));
			JsonObject entry = new JsonObject();
			entry.addProperty("biome", target);
			entry.add("parameters", params);
			biomes.add(entry);
		}
		String template = """
			{"dimensions":{
			  "minecraft:overworld":{"type":"canopycavern:overworld","generator":{"type":"minecraft:noise","settings":"canopycavern:overworld",
			    "biome_source":{"type":"minecraft:multi_noise","biomes":BIOMES}}},
			  "minecraft:the_nether":{"type":"minecraft:the_nether","generator":{"type":"minecraft:noise","settings":"minecraft:nether",
			    "biome_source":{"type":"minecraft:multi_noise","preset":"minecraft:nether"}}},
			  "minecraft:the_end":{"type":"minecraft:the_end","generator":{"type":"minecraft:noise","settings":"minecraft:end",
			    "biome_source":{"type":"minecraft:the_end"}}}}}""";
		JsonObject root = JsonParser.parseString(template.replace("BIOMES", biomes.toString())).getAsJsonObject();
		return new GsonBuilder().create().toJson(root) + "\n";
	}

	@Test
	void presetMatchesVanillaLayoutWithOnlyCanopyBiomes() throws Exception {
		String expected = build();
		if (Boolean.getBoolean("canopy.regenPreset")) {
			Files.createDirectories(PRESET.getParent());
			Files.writeString(PRESET, expected);
		}
		assertTrue(Files.exists(PRESET), "run ./gradlew test -Dcanopy.regenPreset=true");
		assertEquals(expected, Files.readString(PRESET), "canopy.json is stale; regenerate it");
		assertFalse(expected.contains("\"biome\":\"minecraft:"), "preset must not contain vanilla overworld biomes");
		// TerraBlender injects its regions (including vanilla ones) into every multi_noise source whose
		// dimension type is in #terrablender:overworld_regions, so the preset uses its own type.
		assertTrue(expected.contains("\"type\":\"canopycavern:overworld\""));
	}

	@Test
	void presetIsListedInWorldTypeMenuAndKeepsVanillaDimensionRules() throws Exception {
		String tag = Files.readString(Path.of("src/main/resources/data/minecraft/tags/worldgen/world_preset/normal.json"));
		assertTrue(tag.contains("canopycavern:canopy"));
		var ours = JsonParser.parseString(Files.readString(Path.of("src/main/resources/data/canopycavern/dimension_type/overworld.json")));
		try (var in = CanopyWorldPresetTest.class.getResourceAsStream("/data/minecraft/dimension_type/overworld.json")) {
			assertNotNull(in);
			assertEquals(JsonParser.parseString(new String(in.readAllBytes())), ours, "Canopy overworld type must mirror vanilla");
		}
	}

	@Test
	void everyPresetEntryDecodesWithVanillaClimateCodec() throws Exception {
		var biomes = JsonParser.parseString(Files.readString(PRESET)).getAsJsonObject()
			.getAsJsonObject("dimensions").getAsJsonObject("minecraft:overworld").getAsJsonObject("generator")
			.getAsJsonObject("biome_source").getAsJsonArray("biomes");
		assertEquals(vanillaPoints().size() + 1, biomes.size());
		for (var entry : biomes) {
			var result = Climate.ParameterPoint.CODEC.parse(com.mojang.serialization.JsonOps.INSTANCE,
				entry.getAsJsonObject().get("parameters"));
			assertTrue(result.isSuccess(), () -> "bad climate point: " + entry);
		}
	}

	@Test
	void surfaceRulesCoverEveryCanopyStandInForVanillaBiomes() throws Exception {
		Path dir = Path.of("src/main/resources/data/canopycavern/worldgen/material_rule");
		assertTrue(Files.exists(dir.resolve("overworld.json")), "run tools/worldgen/generate_canopy_material_rules.py");
		String root = Files.readString(dir.resolve("overworld.json"));
		assertTrue(root.contains("canopycavern:overworld/canopy_biomes"), "Canopy biome rules must be wired in");
		assertFalse(root.contains("\"minecraft:overworld/"), "rule tree must stay in the canopycavern namespace");
		try (var files = Files.walk(dir)) {
			for (Path file : files.filter(f -> f.toString().endsWith(".json")).toList()) {
				var text = Files.readString(file);
				var matcher = java.util.regex.Pattern.compile("\"biome_is\": \\[([^\\]]*)\\]").matcher(text);
				while (matcher.find()) {
					String list = matcher.group(1);
					for (var entry : CanopyBiomeMap.VANILLA_TO_CANOPY.entrySet()) {
						if (list.contains("\"" + entry.getKey() + "\"")) {
							assertTrue(list.contains("\"" + entry.getValue() + "\""),
								file.getFileName() + ": " + entry.getKey() + " rule missing " + entry.getValue());
						}
					}
				}
			}
		}
		String noise = Files.readString(Path.of("src/main/resources/data/canopycavern/worldgen/noise_settings/overworld.json"));
		assertTrue(noise.contains("\"material_rule\": \"canopycavern:overworld\""));
	}

	@Test
	void everyCanopyBiomeAppearsInPreset() throws Exception {
		String preset = Files.readString(PRESET);
		for (var key : ModBiomes.ALL_BIOMES) {
			assertTrue(preset.contains(key.identifier().toString()), key + " missing from Canopy preset");
		}
	}
}
