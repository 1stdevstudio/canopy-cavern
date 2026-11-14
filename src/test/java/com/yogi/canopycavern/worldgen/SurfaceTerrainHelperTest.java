package com.yogi.canopycavern.worldgen;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.yogi.canopycavern.worldgen.SurfaceTerrainHelper.TerrainProfile;
import net.minecraft.core.BlockPos;
import org.junit.jupiter.api.Test;

import java.util.List;

class SurfaceTerrainHelperTest {

	@Test
	void sampleColumnsAlwaysIncludesCenterCornersEdgeMidpointsWithoutDuplicates() {
		List<BlockPos> columns = SurfaceTerrainHelper.sampleColumns(0, 0, 8, 8, 4);
		assertEquals(9, columns.size());
		assertEquals(new BlockPos(4, 0, 4), columns.getFirst());
		assertTrue(columns.contains(new BlockPos(0, 0, 0)));
		assertTrue(columns.contains(new BlockPos(8, 0, 0)));
		assertTrue(columns.contains(new BlockPos(0, 0, 8)));
		assertTrue(columns.contains(new BlockPos(8, 0, 8)));
		assertTrue(columns.contains(new BlockPos(4, 0, 0)));
		assertTrue(columns.contains(new BlockPos(4, 0, 8)));
		assertTrue(columns.contains(new BlockPos(0, 0, 4)));
		assertTrue(columns.contains(new BlockPos(8, 0, 4)));
	}

	@Test
	void rejectsFluidLavaAndSteepCliffsOnDrySurfaceStructures() {
		TerrainProfile flatDry = new TerrainProfile(72, 74, 73, 72, 0, false, false, true);
		assertTrue(SurfaceTerrainHelper.fitsStartTerrain(flatDry, 4, false, 0));
		assertTrue(SurfaceTerrainHelper.fitsPiecePlacement(flatDry, 73, 5, 3, 6, -64, 63, false, 0));

		TerrainProfile overhangingRiver = new TerrainProfile(62, 74, 73, 56, 6, true, false, true);
		assertFalse(SurfaceTerrainHelper.fitsStartTerrain(overhangingRiver, 4, false, 0));
		assertFalse(SurfaceTerrainHelper.fitsPiecePlacement(overhangingRiver, 73, 5, 3, 6, -64, 63, false, 0));

		TerrainProfile steepCliffDrop = new TerrainProfile(60, 74, 74, 60, 0, false, false, true);
		assertFalse(SurfaceTerrainHelper.fitsStartTerrain(steepCliffDrop, 5, false, 0));
		assertFalse(SurfaceTerrainHelper.fitsPiecePlacement(steepCliffDrop, 74, 5, 3, 6, -64, 63, false, 0));

		TerrainProfile buriedInCliff = new TerrainProfile(72, 78, 72, 72, 0, false, false, true);
		assertFalse(SurfaceTerrainHelper.fitsPiecePlacement(buriedInCliff, 72, 8, 3, 6, -64, 63, false, 0));

		TerrainProfile lavaHazard = new TerrainProfile(70, 71, 71, 70, 0, true, true, true);
		assertFalse(SurfaceTerrainHelper.fitsStartTerrain(lavaHazard, 4, true, 4));
	}

	@Test
	void supportsShallowMarshStiltsWhileRejectingDeepWaterAndSubmergedFloors() {
		TerrainProfile shallowMarsh = new TerrainProfile(62, 65, 64, 61, 1, true, false, true);
		assertTrue(SurfaceTerrainHelper.fitsStartTerrain(shallowMarsh, 4, true, 2));
		assertTrue(SurfaceTerrainHelper.fitsPiecePlacement(shallowMarsh, 64, 4, 3, 6, 0, 63, true, 2));

		// Floor sunk below sea level must be rejected so villager beds and interiors stay dry.
		assertFalse(SurfaceTerrainHelper.fitsPiecePlacement(shallowMarsh, 62, 4, 3, 6, 0, 63, true, 2));

		TerrainProfile deepRiverChannel = new TerrainProfile(62, 65, 64, 57, 5, true, false, true);
		assertFalse(SurfaceTerrainHelper.fitsStartTerrain(deepRiverChannel, 5, true, 2));
		assertFalse(SurfaceTerrainHelper.fitsPiecePlacement(deepRiverChannel, 64, 5, 3, 6, 0, 63, true, 2));
	}
}
