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
	public boolean placeRoots(
		WorldGenLevel level,
		BiConsumer<BlockPos, BlockState> blockSetter,
		RandomSource random,
		BlockPos origin,
		BlockPos trunkOrigin,
		TreeFeature feature
	) {
		int count = rootCount.sample(random);
		int collarY = Math.max(origin.getY(), trunkOrigin.getY() - 1);
		double baseAngle = random.nextDouble() * (Math.PI * 2.0);
		BlockPos.MutableBlockPos cursor = new BlockPos.MutableBlockPos();

		for (int i = 0; i < count; i++) {
			double angle = baseAngle + (Math.PI * 2.0 * i) / count + (random.nextDouble() - 0.5) * 0.45;
			int spread = rootSpread.sample(random);
			List<BlockPos> arch = ComplexTreeGeometry.planArchPath(origin, collarY, angle, spread);
			BlockPos tip = origin;
			for (BlockPos step : arch) {
				if (canPlaceRoot(level, step)) {
					placeRoot(level, blockSetter, random, step, feature);
					tryPlaceAboveRoot(level, blockSetter, random, step);
				}
				tip = step;
			}
			// Anchor each root tip downward until hitting sturdy ground.
			for (int drop = 1; drop <= maxDrop; drop++) {
				cursor.set(tip.getX(), tip.getY() - drop, tip.getZ());
				if (!canPlaceRoot(level, cursor)) {
					break;
				}
				placeRoot(level, blockSetter, random, cursor.immutable(), feature);
			}
		}
		return true;
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
