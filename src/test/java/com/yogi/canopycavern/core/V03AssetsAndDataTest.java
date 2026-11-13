package com.yogi.canopycavern.core;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

class V03AssetsAndDataTest {

	private static final List<String> ALL_ITEMS = List.of(
		"thermal_hood",
		"thermal_parka",
		"thermal_leggings",
		"thermal_boots",
		"mossweave_cap",
		"mossweave_tunic",
		"mossweave_trousers",
		"mossweave_boots",
		"grotto_crystal_pickaxe",
		"alpine_climbing_pick",
		"flare_torch",
		"glow_lantern",
		"grotto_relic_compass",
		"canopy_field_guide",
		"abyssal_tide_compass",
		"sea_glass_charm"
	);

	private static final List<String> ALL_ADVANCEMENTS = List.of(
		"root",
		"enter_peaks",
		"find_crystal_steppe",
		"craft_thermal_set",
		"build_shelter",
		"find_watchtower",
		"conquer_shrine",
		"conquer_mineshaft",
		"attune_compass",
		"visit_village_sentinel",
		"craft_tide_compass",
		"explore_reef_lighthouse",
		"dive_thermal_observatory",
		"plunder_sunken_citadel",
		"discover_abyssal_monument"
	);

	@Test
	void allItemsHaveDefinitionsModelsTexturesAndRecipes() throws IOException {
		for (String item : ALL_ITEMS) {
			JsonObject itemDef = readJson("assets/canopycavern/items/" + item + ".json");
			assertTrue(itemDef.has("model"), item + " missing model definition");

			JsonObject recipe = readJson("data/canopycavern/recipe/" + item + ".json");
			assertTrue(recipe.has("type"), item + " recipe missing type");
			assertTrue(recipe.getAsJsonObject("result").get("id").getAsString().equals("canopycavern:" + item));

			if (item.equals("grotto_relic_compass") || item.equals("abyssal_tide_compass")) {
				for (int i = 0; i < 32; i++) {
					String frame = String.format("%s_%02d", item, i);
					JsonObject m = readJson("assets/canopycavern/models/item/" + frame + ".json");
					assertTrue(m.has("textures"));
					assertPngHeader("assets/canopycavern/textures/item/" + frame + ".png");
				}
			} else {
				JsonObject model = readJson("assets/canopycavern/models/item/" + item + ".json");
				assertTrue(model.has("textures"));
				assertPngHeader("assets/canopycavern/textures/item/" + item + ".png");
			}
		}
	}

	@Test
	void equipmentAndSentinelTexturesAndTagsAreValid() throws IOException {
		for (String eq : List.of("peak_thermal", "mossweave")) {
			JsonObject def = readJson("assets/canopycavern/equipment/" + eq + ".json");
			assertTrue(def.has("layers"));
			assertPngHeader("assets/canopycavern/textures/entity/equipment/humanoid/" + eq + ".png");
			assertPngHeader("assets/canopycavern/textures/entity/equipment/humanoid_leggings/" + eq + ".png");
		}
		assertPngHeader("assets/canopycavern/textures/entity/village_sentinel.png");

		for (String tag : List.of(
			"tags/item/repairs_thermal_armor.json",
			"tags/item/repairs_mossweave_armor.json",
			"tags/item/repairs_crystal_tools.json",
			"tags/worldgen/structure/relic_compass_targets.json",
			"tags/worldgen/structure/tide_compass_targets.json",
			"tags/worldgen/structure/villages.json"
		)) {
			JsonObject t = readJson("data/canopycavern/" + tag);
			assertTrue(t.getAsJsonArray("values").size() >= 2, tag + " should not be empty");
		}
	}

	@Test
	void localizationKeysetsMatchAcrossEnglishAndIndonesian() {
		JsonObject en = readJson("assets/canopycavern/lang/en_us.json");
		JsonObject id = readJson("assets/canopycavern/lang/id_id.json");
		Set<String> enKeys = en.keySet();
		Set<String> idKeys = id.keySet();
		assertEquals(enKeys, idKeys, "English and Indonesian translation keys must match exactly");
		assertTrue(enKeys.size() >= 90, "Expected complete v0.4.0 localization catalog");
	}


	@Test
	void everyCanopyItemHasTwoLocalizedTooltipLines() {
		for (String locale : List.of("en_us", "id_id")) {
			JsonObject lang = readJson("assets/canopycavern/lang/" + locale + ".json");
			for (String item : ALL_ITEMS) {
				for (String suffix : List.of(".tooltip", ".tooltip.detail")) {
					String key = "item.canopycavern." + item + suffix;
					assertTrue(lang.has(key), locale + " missing " + key);
					assertTrue(!lang.get(key).getAsString().isBlank(), locale + " blank " + key);
				}
			}
		}
	}

	@Test
	void allAdvancementsParseCleanlyAndMatchTranslations() {
		JsonObject en = readJson("assets/canopycavern/lang/en_us.json");
		for (String adv : ALL_ADVANCEMENTS) {
			JsonObject obj = readJson("data/canopycavern/advancement/" + adv + ".json");
			assertTrue(obj.has("display"));
			assertTrue(obj.has("criteria"));
			assertTrue(en.has("advancements.canopycavern." + adv + ".title"), "Missing title lang key for " + adv);
			assertTrue(en.has("advancements.canopycavern." + adv + ".description"), "Missing desc lang key for " + adv);
		}
	}

	private static void assertPngHeader(String path) throws IOException {
		try (InputStream in = V03AssetsAndDataTest.class.getClassLoader().getResourceAsStream(path)) {
			assertNotNull(in, "Missing PNG resource: " + path);
			byte[] header = in.readNBytes(8);
			assertEquals(8, header.length);
			assertEquals((byte) 0x89, header[0]);
			assertEquals((byte) 'P', header[1]);
			assertEquals((byte) 'N', header[2]);
			assertEquals((byte) 'G', header[3]);
		}
	}

	private static JsonObject readJson(String path) {
		try (InputStream in = V03AssetsAndDataTest.class.getClassLoader().getResourceAsStream(path)) {
			assertNotNull(in, "Missing resource: " + path);
			return JsonParser.parseString(new String(in.readAllBytes(), StandardCharsets.UTF_8)).getAsJsonObject();
		} catch (IOException ex) {
			throw new AssertionError("Failed reading " + path, ex);
		}
	}
}
