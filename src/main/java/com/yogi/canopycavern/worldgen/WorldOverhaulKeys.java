package com.yogi.canopycavern.worldgen;

import com.yogi.canopycavern.CanopyCavernMod;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.level.levelgen.placement.PlacedFeature;

/**
 * Registry keys for Canopy Cavern surface and subterranean placed features.
 */
public final class WorldOverhaulKeys {
	public static final ResourceKey<PlacedFeature> RIVER_BOULDER = placed("river_boulder");
	public static final ResourceKey<PlacedFeature> MOUNTAIN_OUTCROP = placed("mountain_outcrop");
	public static final ResourceKey<PlacedFeature> FOREST_FALLEN_OAK = placed("forest_fallen_oak");
	public static final ResourceKey<PlacedFeature> TAIGA_FALLEN_SPRUCE = placed("taiga_fallen_spruce");
	public static final ResourceKey<PlacedFeature> PLAINS_FIELDSTONE = placed("plains_fieldstone");

	public static final ResourceKey<PlacedFeature> CAVE_MOSS_FLOOR = placed("cave_moss_floor");
	public static final ResourceKey<PlacedFeature> CAVE_MOSS_CEILING = placed("cave_moss_ceiling");
	public static final ResourceKey<PlacedFeature> CAVE_BOULDER_CLUSTER = placed("cave_boulder_cluster");
	public static final ResourceKey<PlacedFeature> CAVE_GLOW_LICHEN_ACCENT = placed("cave_glow_lichen_accent");
	public static final ResourceKey<PlacedFeature> CAVE_DRIPSTONE_ACCENT = placed("cave_dripstone_accent");

	private WorldOverhaulKeys() {
	}

	private static ResourceKey<PlacedFeature> placed(String path) {
		return ResourceKey.create(Registries.PLACED_FEATURE, CanopyCavernMod.id(path));
	}
}
