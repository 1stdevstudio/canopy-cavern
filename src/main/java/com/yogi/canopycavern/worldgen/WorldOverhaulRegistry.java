package com.yogi.canopycavern.worldgen;

import com.yogi.canopycavern.CanopyCavernMod;
import com.yogi.canopycavern.config.CanopyCavernConfig;
import net.fabricmc.fabric.api.biome.v1.BiomeModifications;
import net.fabricmc.fabric.api.biome.v1.BiomeSelectors;
import net.fabricmc.fabric.api.biome.v1.ModificationPhase;
import net.minecraft.data.worldgen.placement.MiscOverworldPlacements;
import net.minecraft.tags.BiomeTags;
import net.minecraft.world.level.biome.Biomes;
import net.minecraft.world.level.levelgen.GenerationStep;

/**
 * Registers surface and subterranean world overhaul biome modifications based on active config.
 */
public final class WorldOverhaulRegistry {
	private WorldOverhaulRegistry() {
	}

	/** Applies configured Overworld surface cleanup, surface details, and cave overhaul features. */
	public static void register(CanopyCavernConfig config) {
		if (config.removeAbstractSurfaceLava()) {
			BiomeModifications.create(CanopyCavernMod.id("surface_lava_cleanup"))
				.add(ModificationPhase.REMOVALS, BiomeSelectors.foundInOverworld(), context -> {
					var gen = context.getGenerationSettings();
					gen.removeFeature(GenerationStep.Decoration.LAKES, MiscOverworldPlacements.LAKE_LAVA_SURFACE);
					gen.removeFeature(GenerationStep.Decoration.FLUID_SPRINGS, MiscOverworldPlacements.SPRING_LAVA);
					gen.removeFeature(GenerationStep.Decoration.FLUID_SPRINGS, MiscOverworldPlacements.SPRING_LAVA_FROZEN);
				});
		}

		if (config.surfaceOverhaulEnabled()) {
			BiomeModifications.addFeature(
				BiomeSelectors.tag(BiomeTags.IS_RIVER),
				GenerationStep.Decoration.LOCAL_MODIFICATIONS,
				WorldOverhaulKeys.RIVER_BOULDER
			);
			BiomeModifications.addFeature(
				BiomeSelectors.tag(BiomeTags.IS_MOUNTAIN),
				GenerationStep.Decoration.LOCAL_MODIFICATIONS,
				WorldOverhaulKeys.MOUNTAIN_OUTCROP
			);
			BiomeModifications.addFeature(
				BiomeSelectors.includeByKey(Biomes.PLAINS, Biomes.SUNFLOWER_PLAINS, Biomes.MEADOW),
				GenerationStep.Decoration.LOCAL_MODIFICATIONS,
				WorldOverhaulKeys.PLAINS_FIELDSTONE
			);
			BiomeModifications.addFeature(
				BiomeSelectors.tag(BiomeTags.IS_FOREST),
				GenerationStep.Decoration.VEGETAL_DECORATION,
				WorldOverhaulKeys.FOREST_FALLEN_OAK
			);
			BiomeModifications.addFeature(
				BiomeSelectors.tag(BiomeTags.IS_TAIGA),
				GenerationStep.Decoration.VEGETAL_DECORATION,
				WorldOverhaulKeys.TAIGA_FALLEN_SPRUCE
			);
		}

		if (config.caveOverhaulEnabled()) {
			BiomeModifications.addFeature(
				BiomeSelectors.foundInOverworld(),
				GenerationStep.Decoration.UNDERGROUND_DECORATION,
				WorldOverhaulKeys.CAVE_BOULDER_CLUSTER
			);
			BiomeModifications.addFeature(
				BiomeSelectors.foundInOverworld(),
				GenerationStep.Decoration.UNDERGROUND_DECORATION,
				WorldOverhaulKeys.CAVE_MOSS_FLOOR
			);
			BiomeModifications.addFeature(
				BiomeSelectors.foundInOverworld(),
				GenerationStep.Decoration.UNDERGROUND_DECORATION,
				WorldOverhaulKeys.CAVE_MOSS_CEILING
			);
			BiomeModifications.addFeature(
				BiomeSelectors.foundInOverworld(),
				GenerationStep.Decoration.UNDERGROUND_DECORATION,
				WorldOverhaulKeys.CAVE_GLOW_LICHEN_ACCENT
			);
			BiomeModifications.addFeature(
				BiomeSelectors.foundInOverworld(),
				GenerationStep.Decoration.UNDERGROUND_DECORATION,
				WorldOverhaulKeys.CAVE_DRIPSTONE_ACCENT
			);
		}
	}
}
