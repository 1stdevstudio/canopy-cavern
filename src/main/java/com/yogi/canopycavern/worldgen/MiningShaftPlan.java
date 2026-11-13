package com.yogi.canopycavern.worldgen;

import java.util.ArrayList;
import java.util.List;

/** Local shaft floor geometry. Y coordinates use the world's vertical reference. */
public final class MiningShaftPlan {
	public static final int BOTTOM_Y = -32;

	public enum Uphill { NORTH, SOUTH, FLAT }

	/** A floor block. On stairs, uphill points toward the higher half of the tread. */
	public record Step(int x, int y, int z, Uphill uphill) {}

	/** The open center of an end landing, one block above its floor. */
	public record Landing(int walkY, int x, int z) {}

	public record Plan(List<Step> steps, List<Landing> landings) {}

	record Guard(int walkY, int minX, int maxX, int z) {}

	static Guard surfaceGuard(Landing top) {
		// Offset the guard inward so all seven blocks of the crossover remain open.
		return top.z() == 0
			? new Guard(top.walkY(), 1, 3, 1)
			: new Guard(top.walkY(), 5, 7, 8);
	}

	private MiningShaftPlan() {}

	public static Plan build(int surfaceY) {
		if (surfaceY < BOTTOM_Y || surfaceY > 320) {
			throw new IllegalArgumentException("Surface Y outside shaft range: " + surfaceY);
		}

		List<Step> steps = new ArrayList<>();
		List<Landing> landings = new ArrayList<>();
		int walkY = BOTTOM_Y;
		boolean south = true;
		addLanding(steps, landings, walkY, 0);

		while (walkY < surfaceY) {
			int lane = south ? 1 : 5;
			int originZ = south ? 0 : 9;
			int direction = south ? 1 : -1;
			int rise = Math.min(8, surfaceY - walkY);
			for (int tread = 1; tread <= 8; tread++) {
				int z = originZ + direction * tread;
				int y = walkY + Math.min(tread, rise) - 1;
				Uphill uphill = tread <= rise ? (south ? Uphill.SOUTH : Uphill.NORTH) : Uphill.FLAT;
				for (int x = lane; x < lane + 3; x++) {
					steps.add(new Step(x, y, z, uphill));
				}
			}
			walkY += rise;
			addLanding(steps, landings, walkY, south ? 9 : 0);
			south = !south;
		}
		return new Plan(List.copyOf(steps), List.copyOf(landings));
	}

	private static void addLanding(List<Step> steps, List<Landing> landings, int walkY, int z) {
		for (int x = 1; x <= 7; x++) {
			steps.add(new Step(x, walkY - 1, z, Uphill.FLAT));
		}
		landings.add(new Landing(walkY, 4, z));
	}
}
