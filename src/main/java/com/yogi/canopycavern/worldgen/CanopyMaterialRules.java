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
	private static final MaterialRule ROOTED_DIRT = stateRule(Blocks.ROOTED_DIRT);
	private static final MaterialRule MOSS_BLOCK = stateRule(Blocks.MOSS_BLOCK);
	private static final MaterialRule GRANITE = stateRule(Blocks.GRANITE);
	private static final MaterialRule TUFF = stateRule(Blocks.TUFF);
	private static final MaterialRule CALCITE = stateRule(Blocks.CALCITE);
	private static final MaterialRule SMOOTH_BASALT = stateRule(Blocks.SMOOTH_BASALT);
	private static final MaterialRule TERRACOTTA = stateRule(Blocks.TERRACOTTA);
	private static final MaterialRule DRIPSTONE_BLOCK = stateRule(Blocks.DRIPSTONE_BLOCK);
	private static final MaterialRule SNOW_BLOCK = stateRule(Blocks.SNOW_BLOCK);
	private static final MaterialRule PACKED_ICE = stateRule(Blocks.PACKED_ICE);
	private static final MaterialRule DEEPSLATE = stateRule(Blocks.DEEPSLATE);
	private static final MaterialRule ANDESITE = stateRule(Blocks.ANDESITE);
	private static final MaterialRule GRAVEL = stateRule(Blocks.GRAVEL);

	private CanopyMaterialRules() {
	}

	/** Builds Overworld surface/cavern material rules scoped to Canopy Cavern biomes. */
	public static MaterialRule makeRules(RegistryAccess registryAccess) {
		return makeRules(registryAccess.lookupOrThrow(Registries.BIOME));
	}

	/** Same rules from any biome lookup; also used to export them as data for the Canopy preset. */
	public static MaterialRule makeRules(HolderGetter<Biome> biomes) {

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

		MaterialRule elderBoughSurface = MaterialRules.sequence(
			MaterialRules.ifTrue(
				MaterialRules.stoneDepthCheck(0, false, CaveSurface.FLOOR),
				MaterialRules.ifTrue(
					MaterialRules.waterBlockCheck(-1, 0),
					MaterialRules.sequence(
						MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE_SECONDARY, 0.15D, 1.8D), MOSS_BLOCK),
						MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE, -0.35D, 0.25D), PODZOL),
						MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE_SECONDARY, -0.55D, -0.25D), ROOTED_DIRT),
						GRASS_BLOCK
					)
				)
			),
			MaterialRules.ifTrue(
				MaterialRules.stoneDepthCheck(0, true, CaveSurface.FLOOR),
				MaterialRules.sequence(
					MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE, -0.35D, 0.25D), ROOTED_DIRT),
					MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE_SECONDARY, -0.45D, 0.1D), COARSE_DIRT),
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
						MaterialRules.ifTrue(MaterialRules.isBiome(biomes, ModBiomes.ELDER_BOUGH_GROVE), elderBoughSurface),
						MaterialRules.ifTrue(MaterialRules.isBiome(biomes, ModBiomes.CRYSTAL_STEPPE), crystalSteppeSurface),
						MaterialRules.ifTrue(MaterialRules.isBiome(biomes, ModBiomes.FROSTSPIRE_CRAGS), buildFrostspireCragsSurface()),
						MaterialRules.ifTrue(MaterialRules.isBiome(biomes, ModBiomes.WINDCARVED_CLIFFS), buildWindcarvedCliffsSurface())
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

	private static MaterialRule buildFrostspireCragsSurface() {
		MaterialRule steepRock = MaterialRules.sequence(
			MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE, 0.15D, 1.8D), TUFF),
			DEEPSLATE
		);
		return MaterialRules.sequence(
			MaterialRules.ifTrue(
				MaterialRules.stoneDepthCheck(0, false, CaveSurface.FLOOR),
				MaterialRules.sequence(
					MaterialRules.ifTrue(MaterialRules.steep(), steepRock),
					MaterialRules.ifTrue(
						MaterialRules.yBlockCheck(VerticalAnchor.absolute(165), 0),
						MaterialRules.sequence(
							MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE_SECONDARY, 0.28D, 1.8D), PACKED_ICE),
							SNOW_BLOCK
						)
					),
					MaterialRules.ifTrue(
						MaterialRules.waterBlockCheck(-1, 0),
						MaterialRules.sequence(
							MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE, 0.26D, 1.8D), CALCITE),
							MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE_SECONDARY, -0.55D, -0.15D), TUFF),
							SNOW_BLOCK
						)
					)
				)
			),
			MaterialRules.ifTrue(
				MaterialRules.stoneDepthCheck(0, true, CaveSurface.FLOOR),
				MaterialRules.sequence(
					MaterialRules.ifTrue(MaterialRules.steep(), DEEPSLATE),
					MaterialRules.ifTrue(MaterialRules.yBlockCheck(VerticalAnchor.absolute(165), 0), PACKED_ICE),
					TUFF
				)
			)
		);
	}

	private static MaterialRule buildWindcarvedCliffsSurface() {
		MaterialRule stratifiedSteepWall = MaterialRules.sequence(
			MaterialRules.ifTrue(
				MaterialRules.yBlockCheck(VerticalAnchor.absolute(115), 0),
				MaterialRules.sequence(
					MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE, 0.10D, 1.8D), TERRACOTTA),
					GRANITE
				)
			),
			MaterialRules.ifTrue(
				MaterialRules.yBlockCheck(VerticalAnchor.absolute(88), 0),
				MaterialRules.sequence(
					MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE_SECONDARY, 0.05D, 1.8D), ANDESITE),
					TUFF
				)
			),
			MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE, 0.15D, 1.8D), DEEPSLATE),
			SMOOTH_BASALT
		);
		return MaterialRules.sequence(
			MaterialRules.ifTrue(
				MaterialRules.stoneDepthCheck(0, false, CaveSurface.FLOOR),
				MaterialRules.sequence(
					MaterialRules.ifTrue(MaterialRules.steep(), stratifiedSteepWall),
					MaterialRules.ifTrue(
						MaterialRules.waterBlockCheck(-1, 0),
						MaterialRules.sequence(
							MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE_SECONDARY, 0.35D, 1.8D), SMOOTH_BASALT),
							MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE, 0.08D, 1.8D), TUFF),
							MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE, -0.60D, -0.35D), GRAVEL),
							MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE_SECONDARY, -0.60D, -0.30D), MOSS_BLOCK),
							MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE, -0.25D, -0.05D), COARSE_DIRT),
							GRASS_BLOCK
						)
					),
					TUFF
				)
			),
			MaterialRules.ifTrue(
				MaterialRules.stoneDepthCheck(0, true, CaveSurface.FLOOR),
				MaterialRules.sequence(
					MaterialRules.ifTrue(MaterialRules.steep(), TUFF),
					MaterialRules.ifTrue(
						MaterialRules.waterBlockCheck(-1, 0),
						MaterialRules.sequence(
							MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE, 0.08D, 1.8D), TUFF),
							MaterialRules.ifTrue(MaterialRules.noiseCondition2d(Noises.SURFACE, -0.55D, -0.25D), COARSE_DIRT),
							DIRT
						)
					),
					SMOOTH_BASALT
				)
			)
		);
	}

	private static MaterialRule stateRule(Block block) {
		return MaterialRules.state(block.defaultBlockState());
	}
}
