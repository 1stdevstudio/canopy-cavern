package com.yogi.canopycavern.worldgen;

import com.yogi.canopycavern.CanopyCavernMod;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.biome.Biome;

import java.util.List;

/**
 * Resource keys for Canopy Cavern's custom Overworld and subterranean biomes.
 */
public final class ModBiomes {
	public static final ResourceKey<Biome> WHISPERING_PEAKS = key("whispering_peaks");
	public static final ResourceKey<Biome> MOSSY_CANOPY = key("mossy_canopy");
	public static final ResourceKey<Biome> VERDANT_GROTTO = key("verdant_grotto");
	public static final ResourceKey<Biome> CRYSTAL_STEPPE = key("crystal_steppe");
	public static final ResourceKey<Biome> AMBER_CAVERNS = key("amber_caverns");

	public static final List<ResourceKey<Biome>> ALL_BIOMES = List.of(
		WHISPERING_PEAKS,
		MOSSY_CANOPY,
		VERDANT_GROTTO,
		CRYSTAL_STEPPE,
		AMBER_CAVERNS
	);

	private ModBiomes() {
	}

	private static ResourceKey<Biome> key(String path) {
		return ResourceKey.create(Registries.BIOME, CanopyCavernMod.id(path));
	}
}
