package com.yogi.canopycavern.worldgen;

import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Vec3i;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.block.Rotation;

/**
 * Pure geometric layout plan for the multi-chunk {@code elder_great_tree} monument.
 * Computes aligned world origins across the 3 stacked structure templates for any
 * cardinal {@link Rotation} and defines terrain relief probes.
 */
public final class ElderTreePlan {
	public static final int MIN_GROUND_Y = 62;
	public static final int MAX_RELIEF = 7;
	public static final int MAX_ROOT_ANCHOR_DROP = 8;

	public static final PieceSpec ROOT_HOLLOW_BASE = new PieceSpec(
		Identifier.fromNamespaceAndPath("canopycavern", "elder_great_tree/root_hollow_base"),
		37, 20, 37,
		18, 18,
		-2,
		true
	);

	public static final PieceSpec MID_BOUGH_BRIDGES = new PieceSpec(
		Identifier.fromNamespaceAndPath("canopycavern", "elder_great_tree/mid_bough_bridges"),
		45, 20, 45,
		22, 22,
		18,
		false
	);

	public static final PieceSpec CROWN_OBSERVATORY = new PieceSpec(
		Identifier.fromNamespaceAndPath("canopycavern", "elder_great_tree/crown_observatory"),
		39, 18, 39,
		19, 19,
		38,
		false
	);

	public static final List<PieceSpec> PIECES = List.of(
		ROOT_HOLLOW_BASE,
		MID_BOUGH_BRIDGES,
		CROWN_OBSERVATORY
	);

	private static final List<Vec3i> TERRAIN_PROBE_OFFSETS = List.of(
		new Vec3i(0, 0, 0),
		new Vec3i(12, 0, 0),
		new Vec3i(-12, 0, 0),
		new Vec3i(0, 0, 12),
		new Vec3i(0, 0, -12),
		new Vec3i(8, 0, 8),
		new Vec3i(8, 0, -8),
		new Vec3i(-8, 0, 8),
		new Vec3i(-8, 0, -8)
	);

	private ElderTreePlan() {
	}

	/**
	 * Specification for a single modular template slice in {@code elder_great_tree}.
	 */
	public record PieceSpec(
		Identifier templateId,
		int sizeX,
		int sizeY,
		int sizeZ,
		int axisX,
		int axisZ,
		int relativeY,
		boolean anchorRootsToTerrain
	) {
		/**
		 * Returns true if this piece lies within Minecraft's 48x48x48 structure block limit.
		 */
		public boolean fitsVanillaTemplateLimit() {
			return this.sizeX <= 48 && this.sizeY <= 48 && this.sizeZ <= 48;
		}
	}

	/**
	 * 2D integer offset on the XZ plane.
	 */
	public record XZOffset(int x, int z) {
	}

	/**
	 * Applies Minecraft's template rotation around template origin {@code (0, 0)} on the XZ plane.
	 */
	public static XZOffset rotateXZ(int x, int z, Rotation rotation) {
		return switch (rotation) {
			case NONE -> new XZOffset(x, z);
			case CLOCKWISE_90 -> new XZOffset(-z, x);
			case CLOCKWISE_180 -> new XZOffset(-x, -z);
			case COUNTERCLOCKWISE_90 -> new XZOffset(z, -x);
		};
	}

	/**
	 * Computes the world template origin so that the piece's internal trunk axis {@code (axisX, axisZ)}
	 * lands directly on {@code treeCenterXZ} after {@code rotation} is applied.
	 */
	public static BlockPos rotatedOrigin(BlockPos treeCenter, PieceSpec spec, Rotation rotation) {
		XZOffset rotatedAxis = rotateXZ(spec.axisX(), spec.axisZ(), rotation);
		return new BlockPos(
			treeCenter.getX() - rotatedAxis.x(),
			treeCenter.getY() + spec.relativeY(),
			treeCenter.getZ() - rotatedAxis.z()
		);
	}

	/**
	 * Computes the world position of any template-local voxel {@code (localX, localY, localZ)}
	 * once placed with {@link #rotatedOrigin(BlockPos, PieceSpec, Rotation)}.
	 */
	public static BlockPos transformLocalPos(BlockPos treeCenter, PieceSpec spec, Rotation rotation, int localX, int localY, int localZ) {
		BlockPos origin = rotatedOrigin(treeCenter, spec, rotation);
		XZOffset rotatedLocal = rotateXZ(localX, localZ, rotation);
		return origin.offset(rotatedLocal.x(), localY, rotatedLocal.z());
	}

	/**
	 * Returns the 9 surface probe offsets (center + radius 12 ring) around the tree axis.
	 */
	public static List<Vec3i> terrainProbes() {
		return TERRAIN_PROBE_OFFSETS;
	}
}
