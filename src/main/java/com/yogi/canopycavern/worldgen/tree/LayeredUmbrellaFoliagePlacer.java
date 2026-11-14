package com.yogi.canopycavern.worldgen.tree;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.util.RandomSource;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.util.valueproviders.IntProviders;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.levelgen.feature.TreeFeature;
import net.minecraft.world.level.levelgen.feature.foliageplacers.FoliagePlacer;
import net.minecraft.world.level.levelgen.feature.foliageplacers.FoliagePlacerType;

/**
 * Generates broad, flat-bottomed asymmetric canopy umbrellas with serrated edges
 * and trailing leaf drapes for dappled woodland lighting.
 */
public final class LayeredUmbrellaFoliagePlacer extends FoliagePlacer {
	public static final MapCodec<LayeredUmbrellaFoliagePlacer> CODEC = RecordCodecBuilder.mapCodec(instance ->
		foliagePlacerParts(instance).and(instance.group(
			IntProviders.codec(2, 5).fieldOf("height").forGetter(p -> p.height),
			Codec.floatRange(0.0F, 1.0F).fieldOf("skirt_hole_chance").forGetter(p -> p.skirtHoleChance),
			Codec.floatRange(0.0F, 1.0F).fieldOf("hanging_chance").forGetter(p -> p.hangingChance)
		)).apply(instance, LayeredUmbrellaFoliagePlacer::new)
	);

	private final IntProvider height;
	private final float skirtHoleChance;
	private final float hangingChance;

	public LayeredUmbrellaFoliagePlacer(
		IntProvider radius,
		IntProvider offset,
		IntProvider height,
		float skirtHoleChance,
		float hangingChance
	) {
		super(radius, offset);
		this.height = height;
		this.skirtHoleChance = skirtHoleChance;
		this.hangingChance = hangingChance;
	}

	@Override
	protected FoliagePlacerType<?> type() {
		return CanopyTreePlacers.LAYERED_UMBRELLA;
	}

	@Override
	protected void createFoliage(
		WorldGenLevel level,
		FoliageSetter blockSetter,
		RandomSource random,
		TreeFeature feature,
		int maxFreeTreeHeight,
		FoliageAttachment attachment,
		int foliageHeight,
		int foliageRadius,
		int offset
	) {
		boolean doubleTrunk = attachment.doubleTrunk();
		BlockPos center = attachment.pos().above(offset);
		int effectiveRadius = foliageRadius + attachment.radiusOffsetXZ();

		// Build stepped umbrella discs from top dome down to hanging bottom skirt.
		placeLeavesRow(level, blockSetter, random, feature, center, Math.max(1, effectiveRadius - 2), 1, doubleTrunk);
		placeLeavesRow(level, blockSetter, random, feature, center, Math.max(1, effectiveRadius - 1), 0, doubleTrunk);
		placeLeavesRow(level, blockSetter, random, feature, center, effectiveRadius, -1, doubleTrunk);
		if (foliageHeight >= 3) {
			placeLeavesRowWithHangingLeavesBelow(
				level,
				blockSetter,
				random,
				feature,
				center,
				effectiveRadius,
				-2,
				doubleTrunk,
				hangingChance,
				hangingChance * 0.6F
			);
		}
	}

	@Override
	public int foliageHeight(RandomSource random, int treeHeight, TreeFeature feature) {
		return height.sample(random);
	}

	@Override
	protected boolean shouldSkipLocation(
		RandomSource random,
		int localX,
		int localY,
		int localZ,
		int range,
		boolean large
	) {
		if (range <= 1) {
			return localX == range && localZ == range && random.nextFloat() < 0.5F;
		}
		int distSq = localX * localX + localZ * localZ;
		int maxSq = range * range;
		// Carve circular silhouette plus serrated pockets on outer umbrella edge.
		if (distSq > maxSq + 1) {
			return true;
		}
		if (distSq >= maxSq - 1 && localY <= -1 && random.nextFloat() < skirtHoleChance) {
			return true;
		}
		return localX == range && localZ == range;
	}
}
