package com.yogi.canopycavern.worldgen;

import net.minecraft.core.HolderGetter;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Noises;
import net.minecraft.world.level.levelgen.VerticalAnchor;
import net.minecraft.world.level.levelgen.material.MaterialRules;
import net.minecraft.world.level.levelgen.material.rule.MaterialRule;
import net.minecraft.world.level.levelgen.placement.CaveSurface;

/**
 * TerraBlender surface and subterranean material rules for Canopy Cavern's custom biomes.
 */
public final class CanopyMaterialRules {
	private static final MaterialRule GRASS_BLOCK = stateRule(Blocks.GRASS_BLOCK);
	private static final MaterialRule DIRT = stateRule(Blocks.DIRT);
	private static final MaterialRule COARSE_DIRT = stateRule(Blocks.COARSE_DIRT);
	private static final MaterialRule PODZOL = stateRule(Blocks.PODZOL);
	private static final MaterialRule MOSS_BLOCK = stateRule(Blocks.MOSS_BLOCK);
	private static final MaterialRule GRANITE = stateRule(Blocks.GRANITE);
	private static final MaterialRule TUFF = stateRule(Blocks.TUFF);
	private static final MaterialRule CALCITE = stateRule(Blocks.CALCITE);
	private static final MaterialRule SMOOTH_BASALT = stateRule(Blocks.SMOOTH_BASALT);
	private static final MaterialRule TERRACOTTA = stateRule(Blocks.TERRACOTTA);
	private static final MaterialRule DRIPSTONE_BLOCK = stateRule(Blocks.DRIPSTONE_BLOCK);

	private CanopyMaterialRules() {
	}

	/** Builds Overworld surface/cavern material rules scoped to Canopy Cavern biomes. */
	public static MaterialRule makeRules(RegistryAccess registryAccess) {
		HolderGetter<Biome> biomes = registryAccess.lookupOrThrow(Registries.BIOME);

		MaterialRule peaksFloorSurface = MaterialRules.sequence(
			MaterialRules.ifTrue(
				MaterialRules.stoneDepthCheck(0, false, CaveSurface.FLOOR),
				MaterialRules.sequence(
					MaterialRules.ifTrue(MaterialRules.steep(), TUFF),
					MaterialRules.ifTrue(
						MaterialRules.waterBlockCheck(-1, 0),
						MaterialRules.sequence(
							MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE, 0.22D, 1.8D), GRANITE),
							MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE_SECONDARY, 0.35D, 1.8D), MOSS_BLOCK),
							GRASS_BLOCK
						)
					)
				)
			),
			MaterialRules.ifTrue(
				MaterialRules.stoneDepthCheck(0, true, CaveSurface.FLOOR),
				MaterialRules.sequence(
					MaterialRules.ifTrue(MaterialRules.steep(), TUFF),
					MaterialRules.ifTrue(MaterialRules.waterBlockCheck(-1, 0), DIRT)
				)
			)
		);

		MaterialRule mossyCanopyFloorSurface = MaterialRules.sequence(
			MaterialRules.ifTrue(
				MaterialRules.stoneDepthCheck(0, false, CaveSurface.FLOOR),
				MaterialRules.ifTrue(
					MaterialRules.waterBlockCheck(-1, 0),
					MaterialRules.sequence(
						MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE_SECONDARY, 0.2D, 1.8D), MOSS_BLOCK),
						MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE, -0.45D, 0.3D), PODZOL),
						GRASS_BLOCK
					)
				)
			),
			MaterialRules.ifTrue(
				MaterialRules.stoneDepthCheck(0, true, CaveSurface.FLOOR),
				MaterialRules.sequence(
					MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE, -0.45D, 0.3D), COARSE_DIRT),
					DIRT
				)
			)
		);

		MaterialRule verdantGrottoSurface = MaterialRules.sequence(
			MaterialRules.ifTrue(
				MaterialRules.stoneDepthCheck(0, false, CaveSurface.FLOOR),
				MaterialRules.ifTrue(
					MaterialRules.waterBlockCheck(0, 0),
					MaterialRules.sequence(
						MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE, -0.2D, 1.8D), MOSS_BLOCK),
						TUFF
					)
				)
			),
			MaterialRules.ifTrue(
				MaterialRules.stoneDepthCheck(0, false, CaveSurface.CEILING),
				MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE_SECONDARY, 0.05D, 1.8D), TUFF)
			)
		);

		MaterialRule crystalSteppeSurface = MaterialRules.sequence(
			MaterialRules.ifTrue(
				MaterialRules.stoneDepthCheck(0, false, CaveSurface.FLOOR),
				MaterialRules.sequence(
					MaterialRules.ifTrue(MaterialRules.steep(), CALCITE),
					MaterialRules.ifTrue(
						MaterialRules.waterBlockCheck(-1, 0),
						MaterialRules.sequence(
							MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE, 0.42D, 1.8D), CALCITE),
							MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE_SECONDARY, 0.28D, 1.8D), MOSS_BLOCK),
							GRASS_BLOCK
						)
					)
				)
			),
			MaterialRules.ifTrue(
				MaterialRules.stoneDepthCheck(0, true, CaveSurface.FLOOR),
				MaterialRules.sequence(
					MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE, 0.42D, 1.8D), SMOOTH_BASALT),
					DIRT
				)
			)
		);

		MaterialRule amberCavernsSurface = MaterialRules.sequence(
			MaterialRules.ifTrue(
				MaterialRules.stoneDepthCheck(0, false, CaveSurface.FLOOR),
				MaterialRules.ifTrue(
					MaterialRules.waterBlockCheck(0, 0),
					MaterialRules.sequence(
						MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE, 0.25D, 1.8D), TERRACOTTA),
						MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE_SECONDARY, -0.25D, 0.35D), DRIPSTONE_BLOCK),
						TUFF
					)
				)
			),
			MaterialRules.ifTrue(
				MaterialRules.stoneDepthCheck(0, false, CaveSurface.CEILING),
				MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE, -0.1D, 1.8D), DRIPSTONE_BLOCK)
			)
		);

		return MaterialRules.ifTrue(
			MaterialRules.yBlockCheck(VerticalAnchor.aboveBottom(8), 0),
			MaterialRules.sequence(
				MaterialRules.ifTrue(
					MaterialRules.abovePreliminarySurface(),
					MaterialRules.sequence(
						MaterialRules.ifTrue(MaterialRules.isBiome(biomes, ModBiomes.WHISPERING_PEAKS), peaksFloorSurface),
						MaterialRules.ifTrue(MaterialRules.isBiome(biomes, ModBiomes.MOSSY_CANOPY), mossyCanopyFloorSurface),
						MaterialRules.ifTrue(MaterialRules.isBiome(biomes, ModBiomes.CRYSTAL_STEPPE), crystalSteppeSurface)
					)
				),
				MaterialRules.ifTrue(
					MaterialRules.isBiome(biomes, ModBiomes.VERDANT_GROTTO),
					verdantGrottoSurface
				),
				MaterialRules.ifTrue(
					MaterialRules.isBiome(biomes, ModBiomes.AMBER_CAVERNS),
					amberCavernsSurface
				)
			)
		);
	}

	private static MaterialRule stateRule(Block block) {
		return MaterialRules.state(block.defaultBlockState());
	}
}
