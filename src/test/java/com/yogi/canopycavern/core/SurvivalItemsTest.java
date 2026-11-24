package com.yogi.canopycavern.core;

import net.minecraft.core.BlockPos;
import org.junit.jupiter.api.Test;

import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

class SurvivalItemsTest {
	@Test
	void vineStopsAtFloorWallGapAndMaxLength() {
		BlockPos start = new BlockPos(0, 10, 0);
		assertEquals(4, VineColumn.plan(start, 16, p -> p.getY() > 6, p -> true).size(), "stops at the floor");
		assertEquals(2, VineColumn.plan(start, 16, p -> true, p -> p.getY() > 8).size(), "stops where the wall ends");
		assertEquals(16, VineColumn.plan(start, 16, p -> true, p -> true).size(), "capped at 16");
		assertTrue(VineColumn.plan(start, 16, p -> false, p -> true).isEmpty());
		assertEquals(Set.of(start, start.below()), Set.copyOf(VineColumn.plan(start, 2, p -> true, p -> true)));
	}
}
