package com.yogi.canopycavern.world;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/** Short-lived climate protection granted by the Ember Canteen, keyed by player and game time. */
public final class ClimateShield {
	public static final long DURATION_TICKS = 2400L;
	private static final Map<UUID, Long> EXPIRES_AT = new ConcurrentHashMap<>();

	private ClimateShield() {
	}

	public static void grant(UUID player, long gameTime) {
		EXPIRES_AT.put(player, gameTime + DURATION_TICKS);
	}

	public static boolean isActive(UUID player, long gameTime) {
		Long expiry = EXPIRES_AT.get(player);
		if (expiry == null) {
			return false;
		}
		if (gameTime >= expiry || expiry - gameTime > DURATION_TICKS) {
			EXPIRES_AT.remove(player);
			return false;
		}
		return true;
	}

	public static void forget(UUID player) {
		EXPIRES_AT.remove(player);
	}

	public static void clear() {
		EXPIRES_AT.clear();
	}
}
