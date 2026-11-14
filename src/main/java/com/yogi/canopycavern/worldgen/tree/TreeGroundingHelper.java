package com.yogi.canopycavern.worldgen.tree;

import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.level.LevelSimulatedReader;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

/** Shared terrain-grounding predicates and base offsets for custom stilt and elder trees. */
public final class TreeGroundingHelper {

	private static final List<BlockPos> SINGLE_FOOTPRINT = List.of(BlockPos.ZERO);
	private static final List<BlockPos> DOUBLE_FOOTPRINT = List.of(
		new BlockPos(0, 0, 0),
		new BlockPos(1, 0, 0),
		new BlockPos(0, 0, 1),
		new BlockPos(1, 0, 1)
	);

	private TreeGroundingHelper() {}

	public static List<BlockPos> footprintOffsets(boolean doubleTrunk) {
		return doubleTrunk ? DOUBLE_FOOTPRINT : SINGLE_FOOTPRINT;
	}

	public static boolean isReplaceableForRootOrTrunk(BlockState state) {
		return state.isAir()
			|| state.canBeReplaced()
			|| state.is(BlockTags.LEAVES)
			|| state.is(BlockTags.REPLACEABLE_BY_TREES)
			|| state.is(BlockTags.FLOWERS)
			|| state.is(BlockTags.SAPLINGS)
			|| state.is(Blocks.MOSS_CARPET)
			|| state.is(Blocks.VINE)
			|| state.is(Blocks.CAVE_VINES)
			|| state.is(Blocks.CAVE_VINES_PLANT)
			|| state.is(Blocks.AZALEA)
			|| state.is(Blocks.FLOWERING_AZALEA)
			|| state.is(Blocks.SNOW)
			|| state.is(Blocks.WATER);
	}

	public static boolean isWoodOrRoot(BlockState state) {
		return state.is(BlockTags.LOGS) || state.is(Blocks.MANGROVE_ROOTS);
	}

	public static boolean isNaturalGround(BlockState state) {
		if (isReplaceableForRootOrTrunk(state) || isWoodOrRoot(state)) {
			return false;
		}
		return state.is(BlockTags.DIRT)
			|| state.is(BlockTags.BASE_STONE_OVERWORLD)
			|| state.is(BlockTags.SAND)
			|| state.is(BlockTags.TERRACOTTA)
			|| state.is(Blocks.GRAVEL)
			|| state.is(Blocks.CLAY)
			|| state.is(Blocks.MYCELIUM)
			|| state.is(Blocks.SNOW_BLOCK)
			|| state.is(Blocks.PACKED_ICE)
			|| state.is(Blocks.BLUE_ICE);
	}

	public static boolean isNaturalSoil(BlockState state) {
		return state.is(BlockTags.DIRT) || state.is(Blocks.MOSS_BLOCK);
	}

	public static boolean isNaturalGroundAt(LevelSimulatedReader level, BlockPos pos) {
		return level.isStateAtPosition(pos, TreeGroundingHelper::isNaturalGround);
	}

	public static boolean isWoodOrRootAt(LevelSimulatedReader level, BlockPos pos) {
		return level.isStateAtPosition(pos, TreeGroundingHelper::isWoodOrRoot);
	}
}
