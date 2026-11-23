package com.yogi.canopycavern.core;

import net.minecraft.core.BlockPos;

import java.util.function.Predicate;

/** Pure helpers for the Seismic Rod: nearest matching block and a distance-coded chime pitch. */
public final class SeismicSurvey {
	private SeismicSurvey() {
	}

	/** Returns the closest position within a cube of {@code radius} matching {@code isOre}, or null. */
	public static BlockPos nearest(BlockPos origin, int radius, Predicate<BlockPos> isOre) {
		BlockPos best = null;
		double bestDist = Double.MAX_VALUE;
		for (BlockPos pos : BlockPos.betweenClosed(origin.offset(-radius, -radius, -radius), origin.offset(radius, radius, radius))) {
			double dist = pos.distSqr(origin);
			if (dist < bestDist && isOre.test(pos)) {
				bestDist = dist;
				best = pos.immutable();
			}
		}
		return best;
	}

	/** Closer ore rings higher: 2.0 at the player, 0.5 at the edge of the radius. */
	public static double pitchForDistance(double distance, int radius) {
		double t = Math.max(0.0, Math.min(1.0, distance / (radius * Math.sqrt(3.0))));
		return 2.0 - 1.5 * t;
	}
}
