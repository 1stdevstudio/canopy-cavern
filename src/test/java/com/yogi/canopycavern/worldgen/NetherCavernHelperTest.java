package com.yogi.canopycavern.worldgen;

import com.yogi.canopycavern.worldgen.NetherCavernHelper.CavernFootprint;
import org.junit.jupiter.api.Test;

import java.util.OptionalInt;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class NetherCavernHelperTest {

	@Test
	void findCavernFloorSkipsBedrockLavaAndFindsDryShelfBelowCeiling() {
		// Simulate column: bedrock 0..4, lava 5..31, netherrack floor 38..40, open cavern 41..90, ceiling 91..127
		OptionalInt floor = NetherCavernHelper.findCavernFloorY(
			y -> (y >= 0 && y <= 4) || (y >= 38 && y <= 40) || y >= 91,
			y -> y > 40 && y < 91,
			y -> y >= 5 && y <= 31,
			34,
			96,
			16,
			118
		);
		assertTrue(floor.isPresent());
		assertEquals(41, floor.getAsInt());
	}

	@Test
	void findCavernFloorRejectsCrampedCavernWithoutRequiredHeadroom() {
		// Only 10 blocks of headroom (41..50), ceiling starts at 51
		OptionalInt floor = NetherCavernHelper.findCavernFloorY(
			y -> (y >= 38 && y <= 40) || y >= 51,
			y -> y >= 41 && y <= 50,
			y -> false,
			34,
			96,
			16,
			118
		);
		assertTrue(floor.isEmpty());
	}

	@Test
	void findCavernFloorNeverPlacesNearLavaSeaOrRoof() {
		// Floor at 105 only leaves 12 blocks below 118 ceiling limit
		OptionalInt nearRoof = NetherCavernHelper.findCavernFloorY(
			y -> y >= 102 && y <= 104,
			y -> y >= 105 && y < 120,
			y -> false,
			34,
			110,
			16,
			118
		);
		assertTrue(nearRoof.isEmpty());

		// Matching search rejects dipping into lava lake or lava waterfalls
		OptionalInt blockedByLava = NetherCavernHelper.findMatchingFloorNear(
			y -> y >= 32 && y <= 35,
			y -> y >= 36 && y <= 70,
			y -> y == 45, // lava fall intersecting room volume!
			36,
			4,
			4,
			34,
			118,
			16
		);
		assertTrue(blockedByLava.isEmpty());
	}

	@Test
	void fitsPiecePlacementRejectsExcessiveReliefLavaAndCeilingClipping() {
		CavernFootprint soundShelf = new CavernFootprint(50, 54, 52, 48, false, true);
		assertTrue(NetherCavernHelper.fitsPiecePlacement(soundShelf, 51, 68, 7, 4, 14, 34, 118));

		CavernFootprint lavaExposed = new CavernFootprint(50, 54, 52, 48, true, true);
		assertFalse(NetherCavernHelper.fitsPiecePlacement(lavaExposed, 51, 68, 7, 4, 14, 34, 118));

		CavernFootprint ceilingClip = new CavernFootprint(102, 104, 103, 102, false, true);
		assertFalse(NetherCavernHelper.fitsPiecePlacement(ceilingClip, 103, 121, 7, 4, 14, 34, 118));

		CavernFootprint buriedInWall = new CavernFootprint(50, 62, 56, 50, false, true);
		assertFalse(NetherCavernHelper.fitsPiecePlacement(buriedInWall, 52, 68, 15, 4, 14, 34, 118));
	}

	@Test
	void endIslandMinimumSolidThicknessPreventsVoidPunchthrough() {
		// Thick 18-block island beneath surface Y=60 passes 14-block thickness check
		assertTrue(NetherCavernHelper.hasMinimumSolidThickness(y -> y >= 42 && y < 60, 60, 14));
		// Thin 7-block island shelf fails 14-block thickness check
		assertFalse(NetherCavernHelper.hasMinimumSolidThickness(y -> y >= 53 && y < 60, 60, 14));
		// Disabled check (0) always passes
		assertTrue(NetherCavernHelper.hasMinimumSolidThickness(y -> false, 60, 0));
	}
}
