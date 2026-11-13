package com.yogi.canopycavern.world;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

final class ClimateUpdates<T> {
	private record Update<T>(Object player, T payload, long tick) {}

	private final long refreshTicks;
	private final Map<UUID, Update<T>> sent = new HashMap<>();

	ClimateUpdates(long refreshTicks) {
		this.refreshTicks = refreshTicks;
	}

	boolean shouldSend(UUID id, Object player, T payload, long tick) {
		Update<T> previous = sent.get(id);
		if (previous != null && previous.player() == player && payload.equals(previous.payload())
				&& tick >= previous.tick() && tick - previous.tick() < refreshTicks) {
			return false;
		}
		sent.put(id, new Update<>(player, payload, tick));
		return true;
	}

	void forget(UUID id, Object player) {
		Update<T> previous = sent.get(id);
		if (previous != null && previous.player() == player) {
			sent.remove(id);
		}
	}

	void clear() {
		sent.clear();
	}
}
