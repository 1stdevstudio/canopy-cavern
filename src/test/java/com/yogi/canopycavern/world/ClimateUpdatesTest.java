package com.yogi.canopycavern.world;

import org.junit.jupiter.api.Test;

import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ClimateUpdatesTest {
	private static final UUID PLAYER = new UUID(0, 1);
	private static final UUID OTHER_PLAYER = new UUID(0, 2);

	@Test
	void suppressesIdenticalSnapshotsUntilTheRefreshDeadline() {
		var updates = new ClimateUpdates<String>(100);
		Object player = new Object();

		assertTrue(updates.shouldSend(PLAYER, player, "comfortable", 20));
		assertFalse(updates.shouldSend(PLAYER, player, "comfortable", 30));
		assertFalse(updates.shouldSend(PLAYER, player, "comfortable", 119));
		assertTrue(updates.shouldSend(PLAYER, player, "comfortable", 120));
		assertFalse(updates.shouldSend(PLAYER, player, "comfortable", 130));
	}

	@Test
	void sendsChangesImmediatelyAndRestartsTheRefreshWindow() {
		var updates = new ClimateUpdates<String>(100);
		Object player = new Object();

		assertTrue(updates.shouldSend(PLAYER, player, "comfortable", 0));
		assertTrue(updates.shouldSend(PLAYER, player, "freezing", 10));
		assertTrue(updates.shouldSend(PLAYER, player, "comfortable", 20));
		assertFalse(updates.shouldSend(PLAYER, player, "comfortable", 100));
		assertTrue(updates.shouldSend(PLAYER, player, "comfortable", 120));
	}

	@Test
	void treatsAReplacementPlayerAsFreshAndDoesNotForgetItOnStaleDisconnect() {
		var updates = new ClimateUpdates<String>(100);
		Object firstPlayer = new Object();
		Object replacement = new Object();

		assertTrue(updates.shouldSend(PLAYER, firstPlayer, "comfortable", 0));
		assertTrue(updates.shouldSend(PLAYER, replacement, "comfortable", 10));
		updates.forget(PLAYER, firstPlayer);
		assertFalse(updates.shouldSend(PLAYER, replacement, "comfortable", 20));
		updates.forget(PLAYER, replacement);
		assertTrue(updates.shouldSend(PLAYER, replacement, "comfortable", 30));
	}

	@Test
	void keepsPlayersIndependentAndClearsStateAtServerStop() {
		var updates = new ClimateUpdates<String>(100);
		Object player = new Object();
		Object otherPlayer = new Object();

		assertTrue(updates.shouldSend(PLAYER, player, "comfortable", 0));
		assertTrue(updates.shouldSend(OTHER_PLAYER, otherPlayer, "comfortable", 0));
		assertTrue(updates.shouldSend(PLAYER, player, "freezing", 10));
		assertFalse(updates.shouldSend(OTHER_PLAYER, otherPlayer, "comfortable", 10));
		updates.clear();
		assertTrue(updates.shouldSend(PLAYER, player, "freezing", 20));
		assertTrue(updates.shouldSend(OTHER_PLAYER, otherPlayer, "comfortable", 20));
	}
}
