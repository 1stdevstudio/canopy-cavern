package com.yogi.canopycavern.worldgen.tree;

import java.util.ArrayList;
import java.util.List;
import java.util.function.IntSupplier;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.RandomSource;

/**
 * Pure deterministic geometry planner for complex trees (arching buttress roots,
 * slightly crooked single/double trunks, and spiraling horizontal boughs).
 */
public final class ComplexTreeGeometry {

	private ComplexTreeGeometry() {
	}

	/**
	 * Computes an outward-arching root path connecting the raised trunk collar to its ground anchor.
	 */
	public static List<BlockPos> planArchPath(BlockPos origin, int collarY, double angleRad, int spread) {
		List<BlockPos> path = new ArrayList<>();
		double dx = Math.cos(angleRad);
		double dz = Math.sin(angleRad);
		int clampedSpread = Math.max(1, Math.min(5, spread));
		int prevX = origin.getX();
		int prevY = collarY;
		int prevZ = origin.getZ();
		path.add(new BlockPos(prevX, prevY, prevZ));

		for (int step = 1; step <= clampedSpread; step++) {
			int x = origin.getX() + (int) Math.round(dx * step);
			int z = origin.getZ() + (int) Math.round(dz * step);
			double t = (double) step / clampedSpread;
			int targetY = (int) Math.round(collarY - t * Math.max(1, collarY - origin.getY() + 1));
			while (prevX != x || prevZ != z || prevY > targetY) {
				if (prevX != x) {
					prevX += Integer.signum(x - prevX);
				} else if (prevZ != z) {
					prevZ += Integer.signum(z - prevZ);
				}
				if (prevY > targetY) {
					prevY--;
				}
				path.add(new BlockPos(prevX, prevY, prevZ));
			}
		}
		return path;
	}

	/**
	 * Plans trunk voxels, spiraling horizontal boughs, and foliage crown anchor nodes.
	 */
	public static SkeletonPlan planSkeleton(
		BlockPos origin,
		int height,
		int branchCount,
		IntSupplier boughLengthSampler,
		boolean doubleTrunk,
		RandomSource random
	) {
		List<BlockPos> trunkBlocks = new ArrayList<>();
		List<BoughSegment> boughSegments = new ArrayList<>();
		List<CrownAnchor> attachments = new ArrayList<>();

		int effectiveHeight = Math.max(6, height);
		int shiftY = Math.max(3, effectiveHeight / 2);
		int shiftX = random.nextInt(3) - 1;
		int shiftZ = random.nextInt(3) - 1;
		int curX = origin.getX();
		int curZ = origin.getZ();

		for (int dy = 0; dy < effectiveHeight; dy++) {
			if (dy == shiftY || dy == effectiveHeight - 3) {
				curX += shiftX;
				curZ += shiftZ;
			}
			int y = origin.getY() + dy;
			trunkBlocks.add(new BlockPos(curX, y, curZ));
			if (doubleTrunk && dy < effectiveHeight - 2) {
				trunkBlocks.add(new BlockPos(curX + 1, y, curZ));
				trunkBlocks.add(new BlockPos(curX, y, curZ + 1));
				trunkBlocks.add(new BlockPos(curX + 1, y, curZ + 1));
			}
		}

		BlockPos crownApex = new BlockPos(curX, origin.getY() + effectiveHeight, curZ);
		attachments.add(new CrownAnchor(crownApex, doubleTrunk ? 1 : 0, doubleTrunk));

		double baseAngle = random.nextDouble() * (Math.PI * 2.0);
		int boughStartMin = Math.max(4, (int) Math.round(effectiveHeight * 0.45));
		int boughSpan = Math.max(2, effectiveHeight - boughStartMin - 2);

		for (int i = 0; i < branchCount; i++) {
			double angle = baseAngle + (Math.PI * 2.0 * i) / branchCount + (random.nextDouble() - 0.5) * 0.35;
			int len = Math.min(5, Math.max(1, boughLengthSampler.getAsInt()));
			int startOffsetY = boughStartMin + (boughSpan * i) / Math.max(1, branchCount);
			int anchorX = origin.getX() + (startOffsetY >= shiftY ? shiftX : 0);
			int anchorZ = origin.getZ() + (startOffsetY >= shiftY ? shiftZ : 0);
			if (doubleTrunk && Math.cos(angle) > 0) {
				anchorX++;
			}
			if (doubleTrunk && Math.sin(angle) > 0) {
				anchorZ++;
			}
			int anchorY = origin.getY() + startOffsetY;

			double dirX = Math.cos(angle);
			double dirZ = Math.sin(angle);
			int prevX = anchorX;
			int prevY = anchorY;
			int prevZ = anchorZ;

			for (int step = 1; step <= len; step++) {
				int nx = anchorX + (int) Math.round(dirX * step);
				int nz = anchorZ + (int) Math.round(dirZ * step);
				int ny = anchorY + (step + 1) / 2;
				int stepDx = nx - prevX;
				int stepDz = nz - prevZ;
				Direction.Axis axis = Math.abs(stepDx) >= Math.abs(stepDz)
					? (stepDx != 0 ? Direction.Axis.X : Direction.Axis.Y)
					: Direction.Axis.Z;
				boughSegments.add(new BoughSegment(new BlockPos(nx, ny, nz), axis));
				if (ny > prevY && (nx != prevX || nz != prevZ)) {
					boughSegments.add(new BoughSegment(new BlockPos(nx, prevY, nz), axis));
				}
				prevX = nx;
				prevY = ny;
				prevZ = nz;
			}
			attachments.add(new CrownAnchor(new BlockPos(prevX, prevY + 1, prevZ), 0, false));
		}

		return new SkeletonPlan(trunkBlocks, boughSegments, attachments);
	}

	public record BoughSegment(BlockPos pos, Direction.Axis axis) {
	}

	public record CrownAnchor(BlockPos pos, int radiusOffsetXZ, boolean doubleTrunk) {
	}

	public record SkeletonPlan(
		List<BlockPos> trunkBlocks,
		List<BoughSegment> boughSegments,
		List<CrownAnchor> attachments
	) {
	}
}
