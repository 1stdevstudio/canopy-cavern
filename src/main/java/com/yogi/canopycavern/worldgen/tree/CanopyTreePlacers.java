package com.yogi.canopycavern.worldgen.tree;

import com.yogi.canopycavern.CanopyCavernMod;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.level.levelgen.feature.foliageplacers.FoliagePlacerType;
import net.minecraft.world.level.levelgen.feature.rootplacers.RootPlacerType;
import net.minecraft.world.level.levelgen.feature.trunkplacers.TrunkPlacerType;

/**
 * Registers Canopy Cavern's custom complex-tree trunk, foliage, and root placers.
 */
public final class CanopyTreePlacers {
	public static final TrunkPlacerType<GnarledBoughTrunkPlacer> GNARLED_BOUGH =
		new TrunkPlacerType<>(GnarledBoughTrunkPlacer.CODEC);
	public static final FoliagePlacerType<LayeredUmbrellaFoliagePlacer> LAYERED_UMBRELLA =
		new FoliagePlacerType<>(LayeredUmbrellaFoliagePlacer.CODEC);
	public static final RootPlacerType<ArchingRootPlacer> ARCHING_ROOT =
		new RootPlacerType<>(ArchingRootPlacer.CODEC);

	private CanopyTreePlacers() {
	}

	public static void register() {
		Registry.register(BuiltInRegistries.TRUNK_PLACER_TYPE, CanopyCavernMod.id("gnarled_bough"), GNARLED_BOUGH);
		Registry.register(BuiltInRegistries.FOLIAGE_PLACER_TYPE, CanopyCavernMod.id("layered_umbrella"), LAYERED_UMBRELLA);
		Registry.register(BuiltInRegistries.ROOT_PLACER_TYPE, CanopyCavernMod.id("arching_root"), ARCHING_ROOT);
	}
}
