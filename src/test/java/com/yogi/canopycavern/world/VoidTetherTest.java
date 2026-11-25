package com.yogi.canopycavern.world;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class VoidTetherTest {
	@Test
	void rescuesOnlyBelowTheWorldWithAKnownSafeSpot() {
		assertTrue(VoidTether.shouldRescue(-10, 0, true));
		assertFalse(VoidTether.shouldRescue(-5, 0, true), "still inside the margin");
		assertFalse(VoidTether.shouldRescue(-40, 0, false), "no safe spot recorded yet");
	}
}
