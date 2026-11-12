package com.yogi.canopycavern.worldgen;

import com.mojang.datafixers.util.Pair;
import net.minecraft.core.Registry;
import net.minecraft.resources.Identifier;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.biome.Biomes;
import net.minecraft.world.level.biome.Climate;
import terrablender.api.Region;
import terrablender.api.RegionType;

import java.util.function.Consumer;

/**
 * Overworld TerraBlender region injecting Canopy Cavern's custom surface and
 * subterranean cavern biomes without leaving gaps in vanilla climate noise space.
 */
public final class CanopyOverworldRegion extends Region {
	public CanopyOverworldRegion(Identifier name, int weight) {
		super(name, RegionType.OVERWORLD, weight);
	}

	@Override
	public void addBiomes(
		Registry<Biome> registry,
		Consumer<Pair<Climate.ParameterPoint, ResourceKey<Biome>>> mapper
	) {
		this.addModifiedVanillaOverworldBiomes(mapper, builder -> {
			builder.replaceBiome(Biomes.MEADOW, ModBiomes.WHISPERING_PEAKS);
			builder.replaceBiome(Biomes.STONY_PEAKS, ModBiomes.WHISPERING_PEAKS);
			builder.replaceBiome(Biomes.WINDSWEPT_HILLS, ModBiomes.WHISPERING_PEAKS);

			builder.replaceBiome(Biomes.OLD_GROWTH_PINE_TAIGA, ModBiomes.MOSSY_CANOPY);
			builder.replaceBiome(Biomes.DARK_FOREST, ModBiomes.MOSSY_CANOPY);

			builder.replaceBiome(Biomes.SUNFLOWER_PLAINS, ModBiomes.CRYSTAL_STEPPE);
			builder.replaceBiome(Biomes.SAVANNA_PLATEAU, ModBiomes.CRYSTAL_STEPPE);

			builder.replaceBiome(Biomes.LUSH_CAVES, ModBiomes.VERDANT_GROTTO);
			builder.replaceBiome(Biomes.DRIPSTONE_CAVES, ModBiomes.AMBER_CAVERNS);
		});
	}
}
