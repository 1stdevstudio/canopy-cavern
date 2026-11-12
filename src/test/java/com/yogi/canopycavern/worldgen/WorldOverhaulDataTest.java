package com.yogi.canopycavern.worldgen;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

class WorldOverhaulDataTest {

	private static final List<String> REQUIRED_PLACED_FEATURES = List.of(
		"river_boulder",
		"mountain_outcrop",
		"plains_fieldstone",
		"forest_fallen_oak",
		"taiga_fallen_spruce",
		"cave_moss_floor",
		"cave_moss_ceiling",
		"cave_boulder_cluster",
		"cave_glow_lichen_accent",
		"cave_dripstone_accent"
	);

	private static final List<String> REQUIRED_CUSTOM_FEATURES = List.of(
		"river_boulder",
		"mountain_outcrop",
		"plains_fieldstone",
		"forest_fallen_oak",
		"taiga_fallen_spruce",
		"cave_moss_floor",
		"cave_moss_ceiling",
		"cave_boulder_cluster",
		"cave_glow_lichen_accent"
	);

	@Test
	void allPlacedAndConfiguredFeaturesExistAndParseAsJsonObjects() throws Exception {
		for (String name : REQUIRED_PLACED_FEATURES) {
			JsonObject obj = loadJson("data/canopycavern/worldgen/placed_feature/" + name + ".json");
			assertTrue(obj.has("feature"), "Missing feature in placed_feature: " + name);
			assertTrue(obj.has("placement"), "Missing placement in placed_feature: " + name);
		}
		for (String name : REQUIRED_CUSTOM_FEATURES) {
			JsonObject obj = loadJson("data/canopycavern/worldgen/feature/" + name + ".json");
			assertTrue(obj.has("type"), "Missing type in feature: " + name);
		}
	}

	@Test
	void carversStaySmoothAcrossDimensions() throws Exception {
		JsonObject cave = loadJson("data/minecraft/worldgen/carver/cave.json");
		assertFalse(cave.get("weird_thickness_bias").getAsBoolean());
		assertTrue(cave.getAsJsonObject("y").getAsJsonObject("max_inclusive").get("absolute").getAsInt() <= 120);

		JsonObject deepCave = loadJson("data/minecraft/worldgen/carver/cave_extra_underground.json");
		assertFalse(deepCave.get("weird_thickness_bias").getAsBoolean());

		JsonObject canyon = loadJson("data/minecraft/worldgen/carver/canyon.json");
		assertTrue(canyon.get("probability").getAsDouble() <= 0.005);
		assertTrue(canyon.getAsJsonObject("y").getAsJsonObject("max_inclusive").get("absolute").getAsInt() <= 48);

		JsonObject netherCave = loadJson("data/minecraft/worldgen/carver/nether_cave.json");
		assertFalse(netherCave.get("weird_thickness_bias").getAsBoolean());
		assertTrue(netherCave.get("probability").getAsDouble() <= 0.16);
	}

	@Test
	void densityFunctionsCalibratedAcrossOverworldNetherAndEnd() throws Exception {
		JsonObject baseNoise = loadJson("data/minecraft/worldgen/density_function/overworld/base_3d_noise.json");
		assertTrue(baseNoise.get("y_scale").getAsDouble() <= 0.02);

		JsonObject slopedCheese = loadJson("data/minecraft/worldgen/density_function/overworld/sloped_cheese.json");
		JsonObject scaledNoise = slopedCheese.getAsJsonObject("input").getAsJsonObject("right");
		assertEquals("minecraft:mul", scaledNoise.get("type").getAsString());
		assertTrue(scaledNoise.get("right").getAsDouble() <= 0.1);

		JsonObject noodle = loadJson("data/minecraft/worldgen/density_function/overworld/caves/noodle.json");
		assertFalse(noodle.toString().contains("321.0"), "Noodle caves must stay capped below surface peaks");

		assertTrue(loadJson("data/minecraft/worldgen/density_function/overworld/caves/entrances.json").has("input"));
		assertTrue(loadJson("data/minecraft/worldgen/density_function/overworld/caves/spaghetti_roughness_function.json").has("input"));
		assertTrue(loadJson("data/minecraft/worldgen/density_function/overworld/final_density.json").has("left"));

		JsonObject netherNoise = loadJson("data/minecraft/worldgen/density_function/nether/base_3d_noise.json");
		assertTrue(netherNoise.get("y_scale").getAsDouble() <= 0.16);

		JsonObject endNoise = loadJson("data/minecraft/worldgen/density_function/end/base_3d_noise.json");
		assertTrue(endNoise.get("y_scale").getAsDouble() <= 0.1);

		JsonObject endCheese = loadJson("data/minecraft/worldgen/density_function/end/sloped_cheese.json");
		assertEquals("minecraft:end/islands", endCheese.get("left").getAsString());
		assertTrue(endCheese.getAsJsonObject("right").get("right").getAsDouble() <= 0.4);
	}

	private static JsonObject loadJson(String resourcePath) throws Exception {
		try (InputStream stream = WorldOverhaulDataTest.class.getClassLoader().getResourceAsStream(resourcePath)) {
			assertNotNull(stream, "Missing classpath resource: " + resourcePath);
			try (InputStreamReader reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
				JsonElement parsed = JsonParser.parseReader(reader);
				assertTrue(parsed.isJsonObject(), "Expected JSON object in " + resourcePath);
				return parsed.getAsJsonObject();
			}
		}
	}
}
