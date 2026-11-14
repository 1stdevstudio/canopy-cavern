package com.yogi.canopycavern.worldgen;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.tags.BlockTags;
import net.minecraft.tags.FluidTags;
import net.minecraft.world.level.LevelHeightAccessor;
import net.minecraft.world.level.NoiseColumn;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.RandomState;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.material.FluidState;

/**
 * Shared terrain-envelope sampling, fluid/cliff gating, and downward foundation anchoring for
 * surface structures. Prevents rigid templates from cantilevering off cliffs or hanging over rivers.
 */
public final class SurfaceTerrainHelper {

	public record TerrainProfile(
		int minSurfaceY,
		int maxSurfaceY,
		int centerSurfaceY,
		int minSolidY,
		int maxWaterDepth,
		boolean hasFluid,
		boolean hasLava,
		boolean withinBuildHeight
	) {
		public int relief() {
			return maxSurfaceY - minSolidY;
		}
	}

	private SurfaceTerrainHelper() {}

	/**
	 * Builds a deduplicated sample set containing all four corners, edge midpoints, center, and an
	 * interior grid spaced at {@code step} blocks.
	 */
	public static List<BlockPos> sampleColumns(int minX, int minZ, int maxX, int maxZ, int step) {
		int clampedStep = Math.max(1, step);
		int loX = Math.min(minX, maxX);
		int hiX = Math.max(minX, maxX);
		int loZ = Math.min(minZ, maxZ);
		int hiZ = Math.max(minZ, maxZ);
		int midX = (loX + hiX) / 2;
		int midZ = (loZ + hiZ) / 2;

		Set<Long> seen = new LinkedHashSet<>();
		List<BlockPos> columns = new ArrayList<>();
		addColumn(seen, columns, midX, midZ);
		addColumn(seen, columns, loX, loZ);
		addColumn(seen, columns, hiX, loZ);
		addColumn(seen, columns, loX, hiZ);
		addColumn(seen, columns, hiX, hiZ);
		addColumn(seen, columns, midX, loZ);
		addColumn(seen, columns, midX, hiZ);
		addColumn(seen, columns, loX, midZ);
		addColumn(seen, columns, hiX, midZ);

		for (int x = loX; x <= hiX; x += clampedStep) {
			for (int z = loZ; z <= hiZ; z += clampedStep) {
				addColumn(seen, columns, x, z);
			}
		}
		return columns;
	}

	private static void addColumn(Set<Long> seen, List<BlockPos> columns, int x, int z) {
		long key = ((long) x & 0xFFFFFFFFL) | (((long) z & 0xFFFFFFFFL) << 32);
		if (seen.add(key)) {
			columns.add(new BlockPos(x, 0, z));
		}
	}

	/**
	 * Probes world-generation heightmaps and block columns across the given XZ bounds to measure
	 * slope relief, open or frozen water depth, and lava hazards.
	 */
	public static TerrainProfile sampleFootprint(
		ChunkGenerator generator,
		LevelHeightAccessor heightAccessor,
		RandomState randomState,
		int minX,
		int minZ,
		int maxX,
		int maxZ,
		int step
	) {
		int minSurfaceY = Integer.MAX_VALUE;
		int maxSurfaceY = Integer.MIN_VALUE;
		int minSolidY = Integer.MAX_VALUE;
		int centerSurfaceY = Integer.MIN_VALUE;
		int maxWaterDepth = 0;
		boolean hasFluid = false;
		boolean hasLava = false;
		boolean withinHeight = true;

		List<BlockPos> columns = sampleColumns(minX, minZ, maxX, maxZ, step);
		for (int i = 0; i < columns.size(); i++) {
			int px = columns.get(i).getX();
			int pz = columns.get(i).getZ();
			int surfaceY = generator.getFirstOccupiedHeight(
				px, pz, Heightmap.Types.WORLD_SURFACE_WG, heightAccessor, randomState
			);
			int oceanFloorY = generator.getFirstOccupiedHeight(
				px, pz, Heightmap.Types.OCEAN_FLOOR_WG, heightAccessor, randomState
			);
			if (i == 0) {
				centerSurfaceY = surfaceY;
			}
			if (heightAccessor.isOutsideBuildHeight(surfaceY) || heightAccessor.isOutsideBuildHeight(oceanFloorY)) {
				withinHeight = false;
				break;
			}

			NoiseColumn column = generator.getBaseColumn(px, pz, heightAccessor, randomState);
			BlockState atSurface = column.getBlock(surfaceY);
			BlockState belowSurface = surfaceY - 1 >= heightAccessor.getMinY()
				? column.getBlock(surfaceY - 1)
				: atSurface;

			FluidState surfaceFluid = atSurface.getFluidState();
			FluidState belowFluid = belowSurface.getFluidState();
			int columnSolidY = Math.min(surfaceY, oceanFloorY);

			if (!surfaceFluid.isEmpty()) {
				hasFluid = true;
				if (surfaceFluid.is(FluidTags.LAVA)) {
					hasLava = true;
				}
				maxWaterDepth = Math.max(maxWaterDepth, Math.max(1, surfaceY - oceanFloorY));
			} else if (atSurface.is(BlockTags.ICE) && !belowFluid.isEmpty()) {
				// Treat frozen rivers/lakes identically to open water so structures never span thin ice.
				hasFluid = true;
				if (belowFluid.is(FluidTags.LAVA)) {
					hasLava = true;
				}
				int iceFluidDepth = scanFluidDepth(column, surfaceY - 1, heightAccessor.getMinY(), 16);
				columnSolidY = Math.min(columnSolidY, surfaceY - 1 - iceFluidDepth);
				maxWaterDepth = Math.max(maxWaterDepth, iceFluidDepth);
			} else if (surfaceY > oceanFloorY) {
				hasFluid = true;
				maxWaterDepth = Math.max(maxWaterDepth, surfaceY - oceanFloorY);
			}

			minSurfaceY = Math.min(minSurfaceY, surfaceY);
			maxSurfaceY = Math.max(maxSurfaceY, surfaceY);
			minSolidY = Math.min(minSolidY, columnSolidY);
		}

		return new TerrainProfile(
			minSurfaceY,
			maxSurfaceY,
			centerSurfaceY,
			minSolidY,
			maxWaterDepth,
			hasFluid,
			hasLava,
			withinHeight
		);
	}

	private static int scanFluidDepth(NoiseColumn column, int startY, int minWorldY, int maxScan) {
		int depth = 0;
		for (int y = startY; y >= minWorldY && depth < maxScan; y--) {
			if (column.getBlock(y).getFluidState().isEmpty()) {
				break;
			}
			depth++;
		}
		return Math.max(1, depth);
	}

	/** Validates whether the initial footprint terrain passes slope and fluid constraints. */
	public static boolean fitsStartTerrain(
		TerrainProfile profile,
		int maxRelief,
		boolean allowWater,
		int maxWaterDepth
	) {
		if (!profile.withinBuildHeight() || profile.hasLava()) {
			return false;
		}
		if (!allowWater && profile.hasFluid()) {
			return false;
		}
		if (profile.maxWaterDepth() > maxWaterDepth) {
			return false;
		}
		return profile.relief() <= maxRelief;
	}

	/**
	 * Validates an individual rigid piece's placed Y height and footprint envelope against slopes,
	 * deep water, cliff drops, and hillside wall burial.
	 */
	public static boolean fitsPiecePlacement(
		TerrainProfile profile,
		int pieceMinY,
		int maxRelief,
		int maxEmbed,
		int maxFoundationDepth,
		int minYAboveSea,
		int seaLevel,
		boolean allowWater,
		int maxWaterDepth
	) {
		if (!fitsStartTerrain(profile, maxRelief, allowWater, maxWaterDepth)) {
			return false;
		}
		if (pieceMinY < seaLevel + minYAboveSea) {
			return false;
		}
		if (pieceMinY - profile.minSolidY() > maxFoundationDepth) {
			return false;
		}
		return profile.maxSurfaceY() - pieceMinY <= maxEmbed;
	}

	/**
	 * Extends sturdy foundation masonry or pilings downward from {@code baseY - 1} until encountering
	 * dry sturdy natural ground, or stopping at {@code maxDepth}.
	 */
	public static void extendColumnFoundation(
		WorldGenLevel level,
		int px,
		int pz,
		int baseY,
		int maxDepth,
		BlockState foundationState
	) {
		int minY = Math.max(level.getMinY(), baseY - maxDepth);
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
		for (int py = baseY - 1; py >= minY; py--) {
			pos.set(px, py, pz);
			BlockState existing = level.getBlockState(pos);
			if (!existing.isAir()
				&& existing.getFluidState().isEmpty()
				&& !existing.is(BlockTags.LEAVES)
				&& !existing.canBeReplaced()
				&& existing.isFaceSturdy(level, pos, Direction.UP)) {
				break;
			}
			level.setBlock(pos, foundationState, 2);
		}
	}
}
