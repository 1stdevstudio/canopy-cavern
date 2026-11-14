package com.yogi.canopycavern.worldgen.tree;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.util.RandomSource;
import net.minecraft.util.valueproviders.IntProvider;
import net.minecraft.util.valueproviders.IntProviders;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.feature.TreeFeature;
import net.minecraft.world.level.levelgen.feature.rootplacers.AboveRootPlacement;
import net.minecraft.world.level.levelgen.feature.rootplacers.RootPlacer;
import net.minecraft.world.level.levelgen.feature.rootplacers.RootPlacerType;
import net.minecraft.world.level.levelgen.feature.stateproviders.BlockStateProvider;

import java.util.List;
import java.util.Optional;
import java.util.function.BiConsumer;

/**
 * Generates arching buttress roots that flare outward from the trunk collar
 * and plunge vertically down into uneven terrain slopes.
 */
public final class ArchingRootPlacer extends RootPlacer {
	public static final MapCodec<ArchingRootPlacer> CODEC = RecordCodecBuilder.mapCodec(instance ->
		rootPlacerParts(instance).and(instance.group(
			IntProviders.codec(2, 6).fieldOf("root_count").forGetter(p -> p.rootCount),
			IntProviders.codec(2, 5).fieldOf("root_spread").forGetter(p -> p.rootSpread),
			Codec.intRange(2, 8).fieldOf("max_drop").forGetter(p -> p.maxDrop)
		)).apply(instance, ArchingRootPlacer::new)
	);

	private final IntProvider rootCount;
	private final IntProvider rootSpread;
	private final int maxDrop;

	public ArchingRootPlacer(
		IntProvider trunkOffsetY,
		Holder<BlockStateProvider> rootProvider,
		Optional<AboveRootPlacement> aboveRootPlacement,
		IntProvider rootCount,
		IntProvider rootSpread,
		int maxDrop
	) {
		super(trunkOffsetY, rootProvider, aboveRootPlacement);
		this.rootCount = rootCount;
		this.rootSpread = rootSpread;
		this.maxDrop = maxDrop;
	}

	@Override
	protected RootPlacerType<?> type() {
		return CanopyTreePlacers.ARCHING_ROOT;
	}

	@Override
	protected boolean canPlaceRoot(net.minecraft.world.level.LevelSimulatedReader level, BlockPos pos) {
		return level.isStateAtPosition(pos, TreeGroundingHelper::isReplaceableForRootOrTrunk);
	}

	@Override
	public boolean placeRoots(
		WorldGenLevel level,
		BiConsumer<BlockPos, BlockState> blockSetter,
		RandomSource random,
		BlockPos origin,
		BlockPos trunkOrigin,
		TreeFeature feature
	) {
		boolean doubleTrunk = feature.trunkPlacer() instanceof GnarledBoughTrunkPlacer gnarled
			&& gnarled.isDoubleTrunk();
		List<BlockPos> footprint = TreeGroundingHelper.footprintOffsets(doubleTrunk);
		int count = Math.max(rootCount.sample(random), footprint.size());
		int collarY = Math.max(origin.getY(), trunkOrigin.getY() - 1);
		double baseAngle = random.nextDouble() * (Math.PI * 2.0);
		BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();

		// Anchor every base column under the trunk so no bottom log face hovers over air.
		for (BlockPos offset : footprint) {
			BlockPos collarPos = new BlockPos(origin.getX() + offset.getX(), collarY, origin.getZ() + offset.getZ());
			if (canPlaceRoot(level, collarPos) && !TreeGroundingHelper.isWoodOrRootAt(level, collarPos)) {
				placeRootUnchecked(level, blockSetter, random, collarPos, feature);
			}
		}

		// Drop a sturdy inner taproot beneath the primary column down to true natural terrain.
		int taprootDropLimit = Math.max(maxDrop + 4, (collarY - origin.getY()) + 6);
		for (int dy = 1; dy <= taprootDropLimit; dy++) {
			cursor.set(origin.getX(), collarY - dy, origin.getZ());
			if (TreeGroundingHelper.isNaturalGroundAt(level, cursor)) {
				break;
			}
			placeRootIfAllowed(level, blockSetter, random, cursor.immutable(), feature);
		}

		for (int i = 0; i < count; i++) {
			BlockPos cornerOffset = footprint.get(i % footprint.size());
			BlockPos archAnchor = new BlockPos(
				origin.getX() + cornerOffset.getX(),
				origin.getY(),
				origin.getZ() + cornerOffset.getZ()
			);
			double angle = doubleTrunk && i < 4
				? Math.atan2(cornerOffset.getZ() == 0 ? -1.0 : 1.0, cornerOffset.getX() == 0 ? -1.0 : 1.0)
					+ (random.nextDouble() - 0.5) * 0.45
				: baseAngle + (Math.PI * 2.0 * i) / count + (random.nextDouble() - 0.5) * 0.45;
			int spread = rootSpread.sample(random);
			List<BlockPos> arch = ComplexTreeGeometry.planArchPath(archAnchor, collarY, angle, spread);
			BlockPos prev = new BlockPos(archAnchor.getX(), collarY, archAnchor.getZ());
			BlockPos tip = prev;
			for (BlockPos step : arch) {
				// Bridge diagonal X/Z + Y steps with a face-adjacent elbow so root arches stay connected.
				if (step.getY() < prev.getY() && (step.getX() != prev.getX() || step.getZ() != prev.getZ())) {
					placeRootIfAllowed(
						level,
						blockSetter,
						random,
						new BlockPos(step.getX(), prev.getY(), step.getZ()),
						feature
					);
				}
				if (TreeGroundingHelper.isNaturalGroundAt(level, step)) {
					break;
				}
				boolean insideCollar = step.getY() >= collarY
					&& step.getX() >= origin.getX()
					&& step.getX() <= origin.getX() + (doubleTrunk ? 1 : 0)
					&& step.getZ() >= origin.getZ()
					&& step.getZ() <= origin.getZ() + (doubleTrunk ? 1 : 0);
				if (insideCollar) {
					if (canPlaceRoot(level, step) && !TreeGroundingHelper.isWoodOrRootAt(level, step)) {
						placeRootUnchecked(level, blockSetter, random, step, feature);
					}
				} else {
					placeRootIfAllowed(level, blockSetter, random, step, feature);
				}
				prev = step;
				tip = step;
			}
			// Extend each arch tip downward through foliage/air until hitting sturdy terrain ground.
			int verticalLimit = maxDrop + 4;
			for (int drop = 1; drop <= verticalLimit; drop++) {
				cursor.set(tip.getX(), tip.getY() - drop, tip.getZ());
				if (TreeGroundingHelper.isNaturalGroundAt(level, cursor)) {
					if (level.isStateAtPosition(cursor, TreeGroundingHelper::isNaturalSoil)) {
						placeRootUnchecked(level, blockSetter, random, cursor.immutable(), feature);
					}
					break;
				}
				if (!canPlaceRoot(level, cursor) && !TreeGroundingHelper.isWoodOrRootAt(level, cursor)) {
					break;
				}
				placeRootIfAllowed(level, blockSetter, random, cursor.immutable(), feature);
			}
		}
		return true;
	}

	private void placeRootIfAllowed(
		WorldGenLevel level,
		BiConsumer<BlockPos, BlockState> blockSetter,
		RandomSource random,
		BlockPos pos,
		TreeFeature feature
	) {
		if (canPlaceRoot(level, pos) && !TreeGroundingHelper.isWoodOrRootAt(level, pos)) {
			placeRoot(level, blockSetter, random, pos, feature);
		}
	}

	private void placeRootUnchecked(
		WorldGenLevel level,
		BiConsumer<BlockPos, BlockState> blockSetter,
		RandomSource random,
		BlockPos pos,
		TreeFeature feature
	) {
		BlockState state = rootProvider.value().getState(level, random, pos);
		blockSetter.accept(pos, getPotentiallyWaterloggedState(level, pos, state));
	}

	private void tryPlaceAboveRoot(
		WorldGenLevel level,
		BiConsumer<BlockPos, BlockState> blockSetter,
		RandomSource random,
		BlockPos rootPos
	) {
		if (aboveRootPlacement.isEmpty()) {
			return;
		}
		AboveRootPlacement above = aboveRootPlacement.get();
		if (random.nextFloat() >= above.aboveRootPlacementChance()) {
			return;
		}
		BlockPos abovePos = rootPos.above();
		if (level.isEmptyBlock(abovePos)) {
			blockSetter.accept(abovePos, above.aboveRootProvider().value().getState(level, random, abovePos));
		}
	}
}
