package com.yogi.canopycavern.worldgen;

import org.junit.jupiter.api.Test;

import java.util.ArrayDeque;
import java.util.HashSet;
import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

class MiningShaftPlanTest {
	private record Cell(int x, int y, int z) {}

	@Test
	void switchbacksReachAllStationsAndTheSurfaceAcrossUnevenHeights() {
		for (int surfaceY : new int[] {-31, -16, 0, 63, 64, 72, 137, 256, 319}) {
			var plan = MiningShaftPlan.build(surfaceY);
			Set<Cell> floor = new HashSet<>();
			for (var step : plan.steps()) {
				assertTrue(step.x() >= 1 && step.x() <= 7 && step.z() >= 0 && step.z() <= 9);
				assertTrue(floor.add(new Cell(step.x(), step.y(), step.z())));
			}
			assertEquals(new MiningShaftPlan.Landing(-32, 4, 0), plan.landings().getFirst());
			var surface = plan.landings().getLast();
			assertEquals(surfaceY, surface.walkY());
			assertTrue(surface.z() == 0 || surface.z() == 9);

			for (int station : new int[] {-16, 0}) {
				if (station <= surfaceY) {
					assertTrue(plan.landings().contains(new MiningShaftPlan.Landing(station, 4, 0)));
				}
			}
			// All floor cells have clear volume above. Adjacent walking surfaces differ by at most one.
			for (var cell : floor) {
				assertFalse(floor.contains(new Cell(cell.x(), cell.y() + 1, cell.z())));
				assertFalse(floor.contains(new Cell(cell.x(), cell.y() + 2, cell.z())));
			}
			var bottom = new Cell(4, -33, 0);
			var open = new ArrayDeque<Cell>();
			var reached = new HashSet<Cell>();
			open.add(bottom);
			reached.add(bottom);
			while (!open.isEmpty()) {
				var current = open.remove();
				for (int[] axis : new int[][] {{1, 0}, {-1, 0}, {0, 1}, {0, -1}}) {
					for (int dy = -1; dy <= 1; dy++) {
						var next = new Cell(current.x() + axis[0], current.y() + dy, current.z() + axis[1]);
						if (floor.contains(next) && reached.add(next)) open.add(next);
					}
				}
			}
			assertEquals(floor, reached, "Unreachable floor at surface Y=" + surfaceY);
		}
	}

	@Test
	void surfaceGuardProtectsInactiveLaneWithoutBlockingTheCrossing() {
		for (int surfaceY : new int[] {64, 65, 71, 72, 79, 80}) {
			var plan = MiningShaftPlan.build(surfaceY);
			var top = plan.landings().getLast();
			var guard = MiningShaftPlan.surfaceGuard(top);
			assertEquals(surfaceY, guard.walkY());
			assertEquals(top.z() == 0 ? 1 : 8, guard.z());
			assertEquals(top.z() == 0 ? 1 : 5, guard.minX());
			assertEquals(3, guard.maxX() - guard.minX() + 1);
			for (int x = guard.minX(); x <= guard.maxX(); x++) {
				int guardX = x;
				assertTrue(plan.steps().stream().noneMatch(step -> step.x() == guardX
					&& step.z() == guard.z() && step.y() >= surfaceY - 4));
			}
		}
	}

	@Test
	void terrainChecksCoverFullYardOnBothSurfaceLandings() {
		for (int surfaceY : new int[] {64, 72}) {
			var top = MiningShaftPlan.build(surfaceY).landings().getLast();
			var yard = MiningSurfacePlan.origin(top);
			var probes = MiningSurfacePlan.terrainProbes(top);
			for (int x : new int[] {yard.x(), yard.x() + 88}) {
				for (int z : new int[] {yard.z(), yard.z() + 32}) {
					assertTrue(probes.contains(new MiningSurfacePlan.Column(x, z)));
				}
			}
			assertTrue(probes.contains(new MiningSurfacePlan.Column(8, top.z())));
			assertTrue(MiningSurfacePlan.hasFoundation(0, 12));
			assertTrue(MiningSurfacePlan.hasFoundation(68, 31));
			assertTrue(MiningSurfacePlan.hasFoundation(88, 16));
			assertFalse(MiningSurfacePlan.hasFoundation(88, 32));
		}
	}

	@Test
	void eachAscendingTreadHasThreeLanesAndTheCorrectUphillDirection() {
		var plan = MiningShaftPlan.build(81);
		for (int y = -32; y < 81; y++) {
			int progress = y + 32;
			int flight = progress / 8;
			int stride = progress % 8 + 1;
			boolean south = flight % 2 == 0;
			int z = south ? stride : 9 - stride;
			int x = south ? 1 : 5;
			for (int lane = x; lane < x + 3; lane++) {
				assertTrue(plan.steps().contains(new MiningShaftPlan.Step(lane, y, z,
					south ? MiningShaftPlan.Uphill.SOUTH : MiningShaftPlan.Uphill.NORTH)));
			}
		}
		assertThrows(IllegalArgumentException.class, () -> MiningShaftPlan.build(-33));
	}
}
