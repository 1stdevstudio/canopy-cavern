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

		return MaterialRules.ifTrue(
			MaterialRules.yBlockCheck(VerticalAnchor.aboveBottom(8), 0),
			MaterialRules.sequence(
				MaterialRules.ifTrue(
					MaterialRules.abovePreliminarySurface(),
					MaterialRules.sequence(
						MaterialRules.ifTrue(MaterialRules.isBiome(biomes, ModBiomes.WHISPERING_PEAKS), peaksFloorSurface),
						MaterialRules.ifTrue(MaterialRules.isBiome(biomes, ModBiomes.MOSSY_CANOPY), mossyCanopyFloorSurface)
					)
				),
				MaterialRules.ifTrue(
					MaterialRules.isBiome(biomes, ModBiomes.VERDANT_GROTTO),
					verdantGrottoSurface
				)
			)
		);
	}

	private static MaterialRule stateRule(Block block) {
		return MaterialRules.state(block.defaultBlockState());
	}
}
