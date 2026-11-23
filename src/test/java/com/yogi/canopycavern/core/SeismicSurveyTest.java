package com.yogi.canopycavern.core;

import com.yogi.canopycavern.world.ClimateShield;
import net.minecraft.core.BlockPos;
import org.junit.jupiter.api.Test;

import java.util.Set;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

class SeismicSurveyTest {
	@Test
	void findsClosestOreAndIgnoresOutOfRange() {
		BlockPos origin = new BlockPos(0, 0, 0);
		Set<BlockPos> ores = Set.of(new BlockPos(5, 0, 0), new BlockPos(2, 1, 0), new BlockPos(20, 0, 0));
		assertEquals(new BlockPos(2, 1, 0), SeismicSurvey.nearest(origin, 8, ores::contains));
		assertNull(SeismicSurvey.nearest(origin, 8, pos -> pos.equals(new BlockPos(20, 0, 0))));
	}

	@Test
	void closerOreRingsHigher() {
		assertTrue(SeismicSurvey.pitchForDistance(1, 8) > SeismicSurvey.pitchForDistance(7, 8));
		assertEquals(2.0, SeismicSurvey.pitchForDistance(0, 8), 1e-9);
	}

	@Test
	void climateShieldExpiresAfterTwoMinutes() {
		UUID id = UUID.randomUUID();
		ClimateShield.grant(id, 1000L);
		assertTrue(ClimateShield.isActive(id, 1000L + ClimateShield.DURATION_TICKS - 1));
		assertFalse(ClimateShield.isActive(id, 1000L + ClimateShield.DURATION_TICKS));
	}
}
