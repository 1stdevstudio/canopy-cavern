package com.yogi.canopycavern.core;

public final class ExpeditionEnchantmentRules {
	private static final int DEEP_FOCUS_DWELL_TICKS = 60;

	private ExpeditionEnchantmentRules() {
	}

	public static boolean canBuildDeepFocus(boolean overworld, boolean spectator, int headY) {
		return overworld && !spectator && headY <= 16;
	}

	public static int caveTicks(int previous, boolean underground) {
		return underground ? Math.min(DEEP_FOCUS_DWELL_TICKS, previous + 1) : 0;
	}

	public static double deepFocusMultiplier(int level, int caveTicks, boolean grottoPickaxe) {
		if (caveTicks < DEEP_FOCUS_DWELL_TICKS) {
			return 1.0;
		}
		return 1.0 + clampTwoLevels(level) * (grottoPickaxe ? 0.05 : 0.10);
	}

	public static double caveGrip(int level, boolean rocky, boolean grounded, boolean wet) {
		return rocky && grounded && !wet ? clampTwoLevels(level) * 0.10 : 0.0;
	}

	public static double ridgeStep(int level, boolean rocky, boolean grounded, boolean wet, double current) {
		return level > 0 && rocky && grounded && !wet ? Math.max(0, 1.0 - current) : 0.0;
	}

	public static double seabedStride(int level, boolean wet, boolean grounded, boolean swimming) {
		return wet && grounded && !swimming ? clampTwoLevels(level) * 0.15 : 0.0;
	}

	static int clampTwoLevels(int level) {
		return Math.max(0, Math.min(level, 2));
	}
}
