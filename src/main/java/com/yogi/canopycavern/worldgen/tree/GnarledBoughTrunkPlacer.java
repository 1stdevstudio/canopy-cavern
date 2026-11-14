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

	public boolean isDoubleTrunk() {
		return doubleTrunk;
	}

	private void placeBaseSoil(
		WorldGenLevel level,
		BiConsumer<BlockPos, BlockState> blockSetter,
		RandomSource random,
		BlockPos origin,
		TreeFeature feature
	) {
		BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();
		for (BlockPos offset : TreeGroundingHelper.footprintOffsets(doubleTrunk)) {
			BlockPos columnStart = origin.offset(offset.getX(), 0, offset.getZ());
			// Anchor only if the block right below the trunk column isn't already supported by terrain or a stilt root.
			BlockPos immediatelyBelow = columnStart.below();
			boolean supportedByRoot = TreeGroundingHelper.isWoodOrRootAt(level, immediatelyBelow);
			boolean hitGround = false;
			for (int drop = 1; drop <= 10; drop++) {
				cursor.set(columnStart.getX(), columnStart.getY() - drop, columnStart.getZ());
				if (TreeGroundingHelper.isNaturalGroundAt(level, cursor)) {
					if (level.isStateAtPosition(cursor, TreeGroundingHelper::isNaturalSoil)) {
						placeBelowTrunkBlock(level, blockSetter, random, cursor.immutable(), feature);
					}
					hitGround = true;
					break;
				}
				if (supportedByRoot && TreeGroundingHelper.isWoodOrRootAt(level, cursor)) {
					continue;
				}
				if (!supportedByRoot && level.isStateAtPosition(cursor, TreeGroundingHelper::isReplaceableForRootOrTrunk)) {
					BlockState trunkState = feature.trunkProvider().value().getState(level, random, cursor);
					blockSetter.accept(cursor.immutable(), trunkState);
					continue;
				}
				break;
			}
			// If a stilt root wasn't present right below the column, ensure it connects cleanly all the way down.
			if (!hitGround && !supportedByRoot) {
				for (int drop = 1; drop <= 6; drop++) {
					cursor.set(columnStart.getX(), columnStart.getY() - drop, columnStart.getZ());
					if (TreeGroundingHelper.isNaturalGroundAt(level, cursor)) {
						break;
					}
					if (level.isStateAtPosition(cursor, TreeGroundingHelper::isReplaceableForRootOrTrunk)) {
						blockSetter.accept(cursor.immutable(), feature.trunkProvider().value().getState(level, random, cursor));
					}
				}
			}
		}
	}

	private static BlockState orientAxis(BlockState state, Direction.Axis axis) {
		return state.hasProperty(RotatedPillarBlock.AXIS) ? state.setValue(RotatedPillarBlock.AXIS, axis) : state;
	}
}
