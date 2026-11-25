package com.yogi.canopycavern.worldgen;

import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.mojang.serialization.JsonOps;
import net.minecraft.SharedConstants;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderGetter;
import net.minecraft.core.HolderSet;
import net.minecraft.core.registries.Registries;
import net.minecraft.data.registries.VanillaRegistries;
import net.minecraft.resources.RegistryOps;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.Bootstrap;
import net.minecraft.tags.TagKey;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.levelgen.material.rule.MaterialRule;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;

/**
 * TerraBlender only applies CanopyMaterialRules to the Default world type. The Canopy preset gets the
 * same rules as data: this test encodes them to material_rule/overworld/canopy_biomes.json and checks the
 * committed copy is current. Regenerate with ./gradlew test -Dcanopy.regenPreset=true
 */
class CanopyMaterialRuleExportTest {
	static final Path OUT = Path.of("src/main/resources/data/canopycavern/worldgen/material_rule/overworld/canopy_biomes.json");

	@BeforeAll
	static void bootstrap() {
		SharedConstants.tryDetectVersion();
		Bootstrap.bootStrap();
	}

	static String export() {
		var provider = VanillaRegistries.createWorldLookup();
		RegistryOps<JsonElement> ops = RegistryOps.create(JsonOps.INSTANCE, provider);
		// Mod biomes are not in the vanilla lookup, so each one is encoded through a unique vanilla
		// stand-in (a valid reference in this registry set) and renamed back afterwards.
		var biomeLookup = provider.lookupOrThrow(Registries.BIOME);
		java.util.List<ResourceKey<Biome>> standIns = biomeLookup.listElementIds()
			.sorted(java.util.Comparator.comparing(k -> k.identifier().toString())).toList();
		java.util.Map<String, String> renames = new java.util.LinkedHashMap<>();
		HolderGetter<Biome> anyBiome = new HolderGetter<>() {
			@Override
			public Optional<Holder.Reference<Biome>> get(ResourceKey<Biome> key) {
				if (!key.identifier().getNamespace().equals("canopycavern")) {
					throw new IllegalStateException("material rules must only reference Canopy biomes: " + key);
				}
				String id = key.identifier().toString();
				int index = new java.util.ArrayList<>(renames.values()).indexOf(id);
				if (index < 0) {
					index = renames.size();
					renames.put(standIns.get(index).identifier().toString(), id);
				}
				return Optional.of(biomeLookup.getOrThrow(standIns.get(index)));
			}

			@Override
			public Optional<HolderSet.Named<Biome>> get(TagKey<Biome> tag) {
				return Optional.empty();
			}
		};
		MaterialRule rule = CanopyMaterialRules.makeRules(anyBiome);
		JsonElement json = MaterialRule.DIRECT_CODEC.encodeStart(ops, rule).getOrThrow();
		String out = new GsonBuilder().setPrettyPrinting().create().toJson(json) + "\n";
		for (var rename : renames.entrySet()) {
			out = out.replace("\"" + rename.getKey() + "\"", "\"" + rename.getValue() + "\"");
		}
		assertFalse(out.contains("\"minecraft:" ) && out.contains("biome_is\": \"minecraft:"), "stand-in biome leaked");
		return out;
	}

	@Test
	void canopyBiomeRulesAreExportedForThePreset() throws Exception {
		String expected = export();
		if (Boolean.getBoolean("canopy.regenPreset")) {
			Files.createDirectories(OUT.getParent());
			Files.writeString(OUT, expected);
		}
		assertEquals(expected, Files.readString(OUT), "canopy_biomes.json is stale; regenerate it");
		assertTrue(expected.contains("canopycavern:mossy_canopy"));
	}
}
