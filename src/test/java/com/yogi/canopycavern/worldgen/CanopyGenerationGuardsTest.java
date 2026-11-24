package com.yogi.canopycavern.worldgen;

import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.net.URI;
import java.nio.file.FileSystem;
import java.nio.file.FileSystems;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

/** Guards for the generated parts of the Canopy preset (tags, advancement, survival resources). */
class CanopyGenerationGuardsTest {
	static final Path DATA = Path.of("src/main/resources/data");

	static Set<String> entries(String json) {
		Set<String> out = new HashSet<>();
		for (var v : JsonParser.parseString(json).getAsJsonObject().getAsJsonArray("values")) {
			out.add(v.isJsonPrimitive() ? v.getAsString() : v.getAsJsonObject().get("id").getAsString());
		}
		return out;
	}

	/** Every tag (vanilla or Canopy's own) that lists a replaced vanilla biome also lists its stand-in. */
	@Test
	void biomeTagsIncludeCanopyStandIns() throws Exception {
		List<String> problems = new ArrayList<>();
		URI uri = getClass().getResource("/data/minecraft/tags/worldgen/biome/is_ocean.json").toURI();
		try (FileSystem fs = "jar".equals(uri.getScheme()) ? FileSystems.newFileSystem(uri, Map.of()) : null) {
			Path vanilla = fs != null ? fs.getPath("/data/minecraft/tags/worldgen/biome") : Path.of(uri).getParent();
			try (var files = Files.walk(vanilla)) {
				for (Path f : files.filter(p -> p.toString().endsWith(".json")).toList()) {
					Path ours = DATA.resolve("minecraft/tags/worldgen/biome").resolve(vanilla.relativize(f).toString());
					check(entries(Files.readString(f)), ours, problems);
				}
			}
		}
		try (var files = Files.walk(DATA.resolve("canopycavern/tags/worldgen/biome"))) {
			for (Path f : files.filter(p -> p.toString().endsWith(".json")).toList()) {
				check(entries(Files.readString(f)), f, problems);
			}
		}
		assertTrue(problems.isEmpty(), "run tools/worldgen/propagate_canopy_biome_tags.py: " + problems);
	}

	private static void check(Set<String> listed, Path ours, List<String> problems) throws Exception {
		Set<String> have = Files.exists(ours) ? entries(Files.readString(ours)) : Set.of();
		for (String v : listed) {
			String standIn = CanopyBiomeMap.VANILLA_TO_CANOPY.get(v);
			if (standIn != null && !have.contains(standIn)) problems.add(ours.getFileName() + ":" + standIn);
		}
	}

	/** "Adventuring Time" cannot be finished in the Canopy preset, so Canopy Cartographer replaces it. */
	@Test
	void canopyCartographerListsEveryCanopyBiome() throws Exception {
		Path file = DATA.resolve("canopycavern/advancement/canopy_cartographer.json");
		JsonObject criteria = new JsonObject();
		JsonArray requirements = new JsonArray();
		for (var key : ModBiomes.ALL_BIOMES) {
			String id = key.identifier().toString();
			JsonObject location = new JsonObject();
			location.addProperty("biomes", id);
			JsonObject predicate = new JsonObject();
			predicate.add("minecraft:location", location);
			JsonObject player = new JsonObject();
			player.addProperty("type", "minecraft:entity_properties");
			player.addProperty("entity", "this");
			player.add("predicate", predicate);
			JsonObject conditions = new JsonObject();
			conditions.add("player", player);
			JsonObject criterion = new JsonObject();
			criterion.addProperty("trigger", "minecraft:location");
			criterion.add("conditions", conditions);
			criteria.add(id, criterion);
			JsonArray req = new JsonArray();
			req.add(id);
			requirements.add(req);
		}
		JsonObject root = JsonParser.parseString("""
			{"parent":"canopycavern:root","display":{"icon":{"id":"minecraft:filled_map"},
			"title":{"translate":"advancements.canopycavern.canopy_cartographer.title"},
			"description":{"translate":"advancements.canopycavern.canopy_cartographer.description"},
			"frame":"challenge"},"rewards":{"experience":500},"sends_telemetry_event":false}""").getAsJsonObject();
		root.add("criteria", criteria);
		root.add("requirements", requirements);
		String expected = new GsonBuilder().setPrettyPrinting().create().toJson(root) + "\n";
		if (Boolean.getBoolean("canopy.regenPreset")) Files.writeString(file, expected);
		assertEquals(expected, Files.readString(file), "canopy_cartographer.json is stale; regenerate it");
	}

	/** Every survival resource that vanilla ties to a specific biome is still reachable in the preset. */
	@Test
	void survivalResourcesStayReachable() throws Exception {
		StringBuilder all = new StringBuilder();
		for (var key : ModBiomes.ALL_BIOMES) {
			all.append(Files.readString(DATA.resolve("canopycavern/worldgen/biome/" + key.identifier().getPath() + ".json")));
		}
		try (var files = Files.walk(DATA.resolve("canopycavern/worldgen/material_rule"))) {
			for (Path f : files.filter(p -> p.toString().endsWith(".json")).toList()) all.append(Files.readString(f));
		}
		String text = all.toString();
		Map<String, String> needs = new LinkedHashMap<>();
		needs.put("cactus", "minecraft:patch_cactus_desert");
		needs.put("sugar cane", "minecraft:patch_sugar_cane");
		needs.put("bamboo", "minecraft:bamboo");
		needs.put("cocoa / jungle wood", "minecraft:trees_jungle");
		needs.put("melon", "minecraft:patch_melon");
		needs.put("cherry wood", "minecraft:trees_cherry");
		needs.put("mangrove wood", "minecraft:trees_mangrove");
		needs.put("pale oak + creaking", "minecraft:pale_garden_vegetation");
		needs.put("dark oak", "minecraft:dark_forest_vegetation");
		needs.put("acacia", "minecraft:trees_savanna");
		needs.put("ice spikes", "minecraft:ice_spike");
		needs.put("amethyst geodes", "minecraft:amethyst_geode");
		needs.put("sculk", "minecraft:sculk_patch_deep_dark");
		needs.put("coral", "minecraft:warm_ocean_vegetation");
		needs.put("kelp", "minecraft:kelp_cold");
		needs.put("pandas", "minecraft:panda");
		needs.put("mooshrooms", "minecraft:mooshroom");
		needs.put("axolotls", "minecraft:axolotl");
		needs.put("frogs", "minecraft:frog");
		needs.put("parrots", "minecraft:parrot");
		needs.put("polar bears", "minecraft:polar_bear");
		needs.put("sand surface", "minecraft:sand");
		needs.put("terracotta bands", "minecraft:bandlands");
		needs.put("mycelium", "minecraft:mycelium");
		needs.put("mud", "minecraft:mud");
		needs.put("powder snow", "minecraft:powder_snow");
		List<String> missing = new ArrayList<>();
		needs.forEach((what, id) -> { if (!text.contains("\"" + id + "\"")) missing.add(what + " (" + id + ")"); });
		assertTrue(missing.isEmpty(), "missing in Canopy preset: " + missing);
	}
}
