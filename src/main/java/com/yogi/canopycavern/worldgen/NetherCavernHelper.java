package com.yogi.canopycavern.worldgen;

import java.util.OptionalInt;
import java.util.function.IntPredicate;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.level.LevelHeightAccessor;
import net.minecraft.world.level.NoiseColumn;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.RandomState;

/**
 * Interior cavern terrain sampling and foundation helpers for Nether jigsaw structures.
 * Scans 3D {@link NoiseColumn} profiles instead of roof-clamping heightmaps so structures
 * settle onto dry Nether ledges cleanly above the Y=31 lava sea and below the Y=127 ceiling.
 */
public final class NetherCavernHelper {

	public static final int NETHER_LAVA_SEA_Y = 31;
	public static final int NETHER_CEILING_LIMIT = 120;

	private NetherCavernHelper() {
	}

	/** Summary of sampled Nether cavern floor/support heights across a rectangular footprint. */
	public record CavernFootprint(
		int minFloorY,
		int maxFloorY,
		int centerFloorY,
		int minSupportY,
		boolean hasLavaOrVoid,
		boolean withinRoofLimit
	) {
		/** Returns maximum local vertical drop between the highest floor and lowest solid support. */
		public int relief() {
			return maxFloorY - minSupportY;
		}
	}

	/**
	 * Checks whether {@code requiredHeadroom} blocks strictly above {@code floorBlockY} are clear and dry.
	 */
	public static boolean isHeadroomClear(
		IntPredicate isClearSpace,
		IntPredicate isFluid,
		int floorBlockY,
		int requiredHeadroom
	) {
		for (int dy = 1; dy <= requiredHeadroom; dy++) {
			int y = floorBlockY + dy;
			if (!isClearSpace.test(y) || isFluid.test(y)) {
				return false;
			}
		}
		return true;
	}

	/**
	 * Scans upward in {@code [minFloorY, maxFloorY]} for a dry 2-block-thick solid ledge with
	 * {@code requiredHeadroom} clear air blocks above it and ceiling clearance below {@code maxCeilingY}.
	 * Returns the standing air Y (`floorBlockY + 1`), matching heightmap semantics.
	 */
	public static OptionalInt findCavernFloorY(
		IntPredicate isSolidSupport,
		IntPredicate isClearSpace,
		IntPredicate isFluid,
		int minFloorY,
		int maxFloorY,
		int requiredHeadroom,
		int maxCeilingY
	) {
		int clampedMin = Math.max(NETHER_LAVA_SEA_Y + 2, minFloorY);
		int clampedMax = Math.min(maxFloorY, maxCeilingY - requiredHeadroom);
		for (int airY = clampedMin; airY <= clampedMax; airY++) {
			int floorBlockY = airY - 1;
			if (isFluid.test(floorBlockY) || isFluid.test(airY)) {
				continue;
			}
			if (!isSolidSupport.test(floorBlockY) || !isSolidSupport.test(floorBlockY - 1)) {
				continue;
			}
			if (isHeadroomClear(isClearSpace, isFluid, floorBlockY, requiredHeadroom)) {
				return OptionalInt.of(airY);
			}
		}
		return OptionalInt.empty();
	}

	/**
	 * Searches near {@code targetAirY} within {@code [-searchDown, +searchUp]} for a matching dry floor ledge.
	 */
	public static OptionalInt findMatchingFloorNear(
		IntPredicate isSolidSupport,
		IntPredicate isClearSpace,
		IntPredicate isFluid,
		int targetAirY,
		int searchDown,
		int searchUp,
		int minFloorY,
		int maxCeilingY,
		int requiredHeadroom
	) {
		int clampedMin = Math.max(NETHER_LAVA_SEA_Y + 2, minFloorY);
		int maxDelta = Math.max(searchDown, searchUp);
		for (int dist = 0; dist <= maxDelta; dist++) {
			int[] offsets = dist == 0 ? new int[]{0} : new int[]{dist, -dist};
			for (int offset : offsets) {
				if (offset > searchUp || -offset > searchDown) {
					continue;
				}
				int airY = targetAirY + offset;
				if (airY < clampedMin || airY + requiredHeadroom > maxCeilingY) {
					continue;
				}
				int floorBlockY = airY - 1;
				if (isFluid.test(floorBlockY) || isFluid.test(airY)) {
					continue;
				}
				if (!isSolidSupport.test(floorBlockY)) {
					continue;
				}
				if (isHeadroomClear(isClearSpace, isFluid, floorBlockY, requiredHeadroom)) {
					return OptionalInt.of(airY);
				}
			}
		}
		return OptionalInt.empty();
	}

	/** Pure volume check ensuring no lava or fluid falls intersect {@code [minY, maxY]}. */
	public static boolean hasNoFluidInRange(IntPredicate isFluid, int minY, int maxY) {
		for (int y = minY; y <= maxY; y++) {
			if (isFluid.test(y)) {
				return false;
			}
		}
		return true;
	}

	/** Pure vertical thickness check ensuring at least {@code requiredThickness} solid blocks sit below {@code surfaceY}. */
	public static boolean hasMinimumSolidThickness(IntPredicate isSolid, int surfaceY, int requiredThickness) {
		if (requiredThickness <= 0) {
			return true;
		}
		for (int dy = 1; dy <= requiredThickness; dy++) {
			if (!isSolid.test(surfaceY - dy)) {
				return false;
			}
		}
		return true;
	}

	/** Validates a start core footprint against lava/void exposure, roof bounds, and relief. */
	public static boolean fitsStartFootprint(CavernFootprint footprint, int maxRelief) {
		if (footprint.hasLavaOrVoid() || !footprint.withinRoofLimit()) {
			return false;
		}
		return footprint.relief() <= maxRelief;
	}

	/** Validates a structure piece footprint against Nether floor relief, embed depth, and roof bounds. */
	public static boolean fitsPiecePlacement(
		CavernFootprint footprint,
		int pieceMinY,
		int pieceMaxY,
		int maxRelief,
		int maxEmbed,
		int maxFoundationDepth,
		int minFloorY,
		int maxCeilingY
	) {
		if (!fitsStartFootprint(footprint, maxRelief)) {
			return false;
		}
		if (pieceMinY < minFloorY || pieceMaxY > maxCeilingY) {
			return false;
		}
		if (pieceMinY - footprint.minSupportY() > maxFoundationDepth) {
			return false;
		}
		return footprint.maxFloorY() - pieceMinY <= maxEmbed;
	}

	/**
	 * Finds a valid dry cavern floor Y at the center of a candidate structure chunk.
	 */
	public static OptionalInt findAnchorFloorY(
		ChunkGenerator generator,
		LevelHeightAccessor heightAccessor,
		RandomState randomState,
		int x,
		int z,
		int minFloorY,
		int maxFloorY,
		int requiredHeadroom,
		int maxCeilingY
	) {
		int boundedMin = Math.max(heightAccessor.getMinY() + 2, minFloorY);
		int boundedCeiling = Math.min(heightAccessor.getMaxY() - 1, Math.min(NETHER_CEILING_LIMIT, maxCeilingY));
		if (boundedMin + requiredHeadroom > boundedCeiling) {
			return OptionalInt.empty();
		}
		NoiseColumn col = generator.getBaseColumn(x, z, heightAccessor, randomState);
		return findCavernFloorY(
			y -> isSolidSupport(col.getBlock(y)),
			y -> isClearAir(col.getBlock(y)),
			y -> isFluidOrHazard(col.getBlock(y)),
			boundedMin,
			boundedCeiling,
			requiredHeadroom,
			boundedCeiling
		);
	}

	/**
	 * Samples a horizontal footprint around {@code targetAirY}, checking terrain smoothness and
	 * verifying that the piece's vertical span is free of lava pools and bedrock ceilings.
	 */
	public static CavernFootprint sampleFootprint(
		ChunkGenerator generator,
		LevelHeightAccessor heightAccessor,
		RandomState randomState,
		int minX,
		int minZ,
		int maxX,
		int maxZ,
		int stride,
		int targetAirY,
		int searchDown,
		int searchUp,
		int minFloorY,
		int maxCeilingY,
		int clearCheckHeight
	) {
		int boundedCeiling = Math.min(heightAccessor.getMaxY() - 1, Math.min(NETHER_CEILING_LIMIT, maxCeilingY));
		int step = Math.max(1, stride);
		int centerX = (minX + maxX) >> 1;
		int centerZ = (minZ + maxZ) >> 1;

		int minFloor = Integer.MAX_VALUE;
		int maxFloor = Integer.MIN_VALUE;
		int minSupport = Integer.MAX_VALUE;
		int centerFloor = targetAirY;
		boolean hasLavaOrVoid = false;
		boolean withinRoof = targetAirY + clearCheckHeight <= boundedCeiling;

		for (int x = minX; ; ) {
			for (int z = minZ; ; ) {
				NoiseColumn col = generator.getBaseColumn(x, z, heightAccessor, randomState);
				int volumeTop = Math.min(boundedCeiling, targetAirY + clearCheckHeight);
				int volumeBottom = Math.max(heightAccessor.getMinY(), targetAirY - 1);
				if (!hasNoFluidInRange(y -> isFluidOrHazard(col.getBlock(y)), volumeBottom, volumeTop)) {
					hasLavaOrVoid = true;
				}
				OptionalInt matched = findMatchingFloorNear(
					y -> isSolidSupport(col.getBlock(y)),
					y -> isClearAir(col.getBlock(y)),
					y -> isFluidOrHazard(col.getBlock(y)),
					targetAirY,
					searchDown,
					searchUp,
					minFloorY,
					boundedCeiling,
					clearCheckHeight
				);
				if (matched.isEmpty()) {
					hasLavaOrVoid = true;
				} else {
					int floorY = matched.getAsInt();
					minFloor = Math.min(minFloor, floorY);
					maxFloor = Math.max(maxFloor, floorY);
					minSupport = Math.min(minSupport, floorY);
					if (x == centerX && z == centerZ) {
						centerFloor = floorY;
					}
				}
				if (z == maxZ) {
					break;
				}
				z = Math.min(maxZ, z + step);
			}
			if (x == maxX) {
				break;
			}
			x = Math.min(maxX, x + step);
		}

		if (minFloor == Integer.MAX_VALUE) {
			return new CavernFootprint(targetAirY, targetAirY, targetAirY, targetAirY, true, false);
		}
		return new CavernFootprint(minFloor, maxFloor, centerFloor, minSupport, hasLavaOrVoid, withinRoof);
	}

	/**
	 * Extends sturdy foundation piers beneath {@code baseY} down into Nether bedrock/netherrack/basalt ledges.
	 */
	public static void extendColumnFoundation(
		WorldGenLevel level,
		int x,
		int z,
		int baseY,
		int maxDepth,
		BlockState foundationState
	) {
		BlockPos.MutableBlockPos pos = new BlockPos.MutableBlockPos();
		for (int dy = 1; dy <= maxDepth; dy++) {
			int y = baseY - dy;
			if (level.isOutsideBuildHeight(y) || y <= NETHER_LAVA_SEA_Y) {
				break;
			}
			pos.set(x, y, z);
			BlockState existing = level.getBlockState(pos);
			if (existing.getFluidState().isEmpty()
				&& !existing.isAir()
				&& !existing.canBeReplaced()
				&& existing.isFaceSturdy(level, pos, Direction.UP)) {
				break;
			}
			level.setBlock(pos, foundationState, 2);
		}
	}

	private static boolean isSolidSupport(BlockState state) {
		return !state.isAir()
			&& state.getFluidState().isEmpty()
			&& !state.canBeReplaced()
			&& !state.is(Blocks.BEDROCK)
			&& !state.is(Blocks.MAGMA_BLOCK);
	}

	private static boolean isClearAir(BlockState state) {
		return (state.isAir() || state.canBeReplaced()) && state.getFluidState().isEmpty();
	}

	private static boolean isFluidOrHazard(BlockState state) {
		return !state.getFluidState().isEmpty()
			|| state.is(Blocks.LAVA)
			|| state.is(Blocks.FIRE)
			|| state.is(Blocks.SOUL_FIRE);
	}
}
