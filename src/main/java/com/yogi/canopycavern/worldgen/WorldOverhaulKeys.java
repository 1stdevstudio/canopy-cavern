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

	public static final ResourceKey<PlacedFeature> DESERT_OASIS_BOULDER = placed("desert_oasis_boulder");
	public static final ResourceKey<PlacedFeature> SAVANNA_ACACIA_BOULDER = placed("savanna_acacia_boulder");
	public static final ResourceKey<PlacedFeature> SWAMP_PEAT_PATCH = placed("swamp_peat_patch");
	public static final ResourceKey<PlacedFeature> BEACH_DRIFT_PEBBLE = placed("beach_drift_pebble");
	public static final ResourceKey<PlacedFeature> CRYSTAL_STEPPE_OUTCROP = placed("crystal_steppe_outcrop");

	public static final ResourceKey<PlacedFeature> STRATIFIED_COPPER_VEIN = placed("stratified_copper_vein");
	public static final ResourceKey<PlacedFeature> STRATIFIED_EMERALD_SEAM = placed("stratified_emerald_seam");
	public static final ResourceKey<PlacedFeature> DEEP_AMETHYST_POCKET = placed("deep_amethyst_pocket");

	public static final ResourceKey<PlacedFeature> NETHER_BASALT_ACCENT = placed("nether_basalt_accent");
	public static final ResourceKey<PlacedFeature> END_CHORUS_OUTCROP = placed("end_chorus_outcrop");

	private WorldOverhaulKeys() {
	}

	private static ResourceKey<PlacedFeature> placed(String path) {
		return ResourceKey.create(Registries.PLACED_FEATURE, CanopyCavernMod.id(path));
	}
}
