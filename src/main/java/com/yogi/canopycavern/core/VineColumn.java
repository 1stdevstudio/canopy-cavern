package com.yogi.canopycavern.core;

import net.minecraft.core.BlockPos;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Predicate;

/** Plans the vine column a Climbing Vine Coil hangs: straight down while the cell is empty and backed by a wall. */
public final class VineColumn {
	private VineColumn() {
	}

	public static List<BlockPos> plan(BlockPos start, int maxLength, Predicate<BlockPos> isEmpty, Predicate<BlockPos> hasWall) {
		List<BlockPos> out = new ArrayList<>();
		BlockPos pos = start;
		while (out.size() < maxLength && isEmpty.test(pos) && hasWall.test(pos)) {
			out.add(pos);
			pos = pos.below();
		}
		return out;
	}
}
