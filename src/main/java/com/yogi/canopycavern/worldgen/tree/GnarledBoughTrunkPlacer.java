package com.yogi.canopycavern.worldgen.tree;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.RandomSource;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.util.valueproviders.IntProviders;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.RotatedPillarBlock;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.feature.TreeFeature;
import net.minecraft.world.level.levelgen.feature.foliageplacers.FoliagePlacer.FoliageAttachment;
import net.minecraft.world.level.levelgen.feature.trunkplacers.TrunkPlacer;
import net.minecraft.world.level.levelgen.feature.trunkplacers.TrunkPlacerType;

import com.yogi.canopycavern.worldgen.tree.ComplexTreeGeometry.BoughSegment;
import com.yogi.canopycavern.worldgen.tree.ComplexTreeGeometry.SkeletonPlan;
import java.util.List;
import java.util.function.BiConsumer;

/**
 * Generates tall, slightly twisted trunks (1x1 or 2x2) with spiraling radial boughs
 * and secondary foliage forks for complex multi-layered forest canopies.
 */
public final class GnarledBoughTrunkPlacer extends TrunkPlacer {
	public static final MapCodec<GnarledBoughTrunkPlacer> CODEC = RecordCodecBuilder.mapCodec(instance ->
		trunkPlacerParts(instance).and(instance.group(
			IntProviders.codec(2, 6).fieldOf("bough_count").forGetter(p -> p.boughCount),
			IntProviders.codec(2, 6).fieldOf("bough_length").forGetter(p -> p.boughLength),
			Codec.BOOL.fieldOf("double_trunk").forGetter(p -> p.doubleTrunk)
		)).apply(instance, GnarledBoughTrunkPlacer::new)
	);

	private final IntProvider boughCount;
	private final IntProvider boughLength;
	private final boolean doubleTrunk;

	public GnarledBoughTrunkPlacer(
		int baseHeight,
		int heightRandA,
		int heightRandB,
		IntProvider boughCount,
		IntProvider boughLength,
		boolean doubleTrunk
	) {
		super(baseHeight, heightRandA, heightRandB);
		this.boughCount = boughCount;
		this.boughLength = boughLength;
		this.doubleTrunk = doubleTrunk;
	}

	@Override
	protected TrunkPlacerType<?> type() {
		return CanopyTreePlacers.GNARLED_BOUGH;
	}

	@Override
	public List<FoliageAttachment> placeTrunk(
		WorldGenLevel level,
		BiConsumer<BlockPos, BlockState> blockSetter,
		RandomSource random,
		int freeTreeHeight,
		BlockPos origin,
		TreeFeature feature
	) {
		placeBaseSoil(level, blockSetter, random, origin, feature);
		SkeletonPlan plan = ComplexTreeGeometry.planSkeleton(
			origin,
			freeTreeHeight,
			boughCount.sample(random),
			() -> boughLength.sample(random),
			doubleTrunk,
			random
		);

		for (BlockPos col : plan.trunkBlocks()) {
			placeLog(level, blockSetter, random, col, feature);
		}
		for (BoughSegment seg : plan.boughSegments()) {
			Direction.Axis axis = seg.axis();
			placeLog(level, blockSetter, random, seg.pos(), feature, state -> orientAxis(state, axis));
		}
		return plan.attachments().stream()
			.map(anchor -> new FoliageAttachment(anchor.pos(), anchor.radiusOffsetXZ(), anchor.doubleTrunk()))
			.toList();
	}

	private void placeBaseSoil(
		WorldGenLevel level,
		BiConsumer<BlockPos, BlockState> blockSetter,
		RandomSource random,
		BlockPos origin,
		TreeFeature feature
	) {
		placeBelowTrunkBlock(level, blockSetter, random, origin.below(), feature);
		if (!doubleTrunk) {
			return;
		}
		placeBelowTrunkBlock(level, blockSetter, random, origin.below().east(), feature);
		placeBelowTrunkBlock(level, blockSetter, random, origin.below().south(), feature);
		placeBelowTrunkBlock(level, blockSetter, random, origin.below().east().south(), feature);
	}

	private static BlockState orientAxis(BlockState state, Direction.Axis axis) {
		return state.hasProperty(RotatedPillarBlock.AXIS) ? state.setValue(RotatedPillarBlock.AXIS, axis) : state;
	}
}
