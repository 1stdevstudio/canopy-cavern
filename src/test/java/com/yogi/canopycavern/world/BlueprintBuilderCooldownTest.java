package com.yogi.canopycavern.world;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class BlueprintBuilderCooldownTest {

	@Test
	void firstRequestIsAllowed() {
		assertTrue(BlueprintBuilderService.isCooldownElapsed(null, 100L));
	}

	@Test
	void rapidRepeatIsRejected() {
		assertFalse(BlueprintBuilderService.isCooldownElapsed(100L, 100L + BlueprintBuilderService.BUILD_COOLDOWN_TICKS - 1));
	}

	@Test
	void requestAfterCooldownIsAllowed() {
		assertTrue(BlueprintBuilderService.isCooldownElapsed(100L, 100L + BlueprintBuilderService.BUILD_COOLDOWN_TICKS));
	}

	@Test
	void tickCounterResetDoesNotLockPlayerOut() {
		assertTrue(BlueprintBuilderService.isCooldownElapsed(5000L, 10L));
	}
}
