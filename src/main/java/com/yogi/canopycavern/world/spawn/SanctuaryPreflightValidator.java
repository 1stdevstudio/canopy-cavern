package com.yogi.canopycavern.world.spawn;

import com.yogi.canopycavern.config.CanopyCavernConfig;
import net.minecraft.core.BlockPos;
import net.minecraft.core.SectionPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.entity.BeehiveBlockEntity;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.border.WorldBorder;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.level.chunk.status.ChunkStatus;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.StructureStart;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Fail-closed safety & terrain validator run before preview or server installation of Canopy Sanctuary.
 */
public final class SanctuaryPreflightValidator {
	public static final int MAX_CORE_RELIEF_BLOCKS = 16;
	public static final int MAX_CENTER_GROUND_DELTA = 6;
	public static final int CORE_SAMPLE_RADIUS = 36;
	public static final int SAMPLE_STEP = 4;

	private static final class NaturalBlockSetHolder {
		static final Set<Block> EXTRA_NATURAL_BLOCKS = Set.of(
			Blocks.AIR,
			Blocks.CAVE_AIR,
			Blocks.VOID_AIR,
			Blocks.GRASS_BLOCK,
			Blocks.MYCELIUM,
			Blocks.PODZOL,
			Blocks.MUD,
			Blocks.MUDDY_MANGROVE_ROOTS,
			Blocks.MOSS_BLOCK,
			Blocks.MOSS_CARPET,
			Blocks.PALE_MOSS_BLOCK,
			Blocks.PALE_MOSS_CARPET,
			Blocks.GRAVEL,
			Blocks.CLAY,
			Blocks.CALCITE,
			Blocks.TUFF,
			Blocks.DRIPSTONE_BLOCK,
			Blocks.POINTED_DRIPSTONE,
			Blocks.SHORT_GRASS,
			Blocks.TALL_GRASS,
			Blocks.FERN,
			Blocks.LARGE_FERN,
			Blocks.DEAD_BUSH,
			Blocks.AZALEA,
			Blocks.FLOWERING_AZALEA,
			Blocks.GLOW_LICHEN,
			Blocks.VINE,
			Blocks.SUGAR_CANE,
			Blocks.BAMBOO,
			Blocks.SNOW_BLOCK,
			Blocks.POWDER_SNOW,
			Blocks.ICE,
			Blocks.PACKED_ICE,
			Blocks.BLUE_ICE,
			Blocks.RED_MUSHROOM,
			Blocks.BROWN_MUSHROOM,
			Blocks.SEAGRASS,
			Blocks.TALL_SEAGRASS,
			Blocks.KELP,
			Blocks.KELP_PLANT,
			Blocks.COAL_ORE,
			Blocks.DEEPSLATE_COAL_ORE,
			Blocks.REDSTONE_ORE,
			Blocks.DEEPSLATE_REDSTONE_ORE,
			Blocks.LAPIS_ORE,
			Blocks.DEEPSLATE_LAPIS_ORE,
			Blocks.EMERALD_ORE,
			Blocks.DEEPSLATE_EMERALD_ORE,
			Blocks.DIAMOND_ORE,
			Blocks.DEEPSLATE_DIAMOND_ORE,
			Blocks.AMETHYST_BLOCK,
			Blocks.AMETHYST_CLUSTER,
			Blocks.BUDDING_AMETHYST,
			Blocks.SMOOTH_BASALT,
			Blocks.SNOW,
			Blocks.PUMPKIN,
			Blocks.MELON,
			Blocks.SWEET_BERRY_BUSH,
			Blocks.BEE_NEST,
			Blocks.MUSHROOM_STEM,
			Blocks.RED_MUSHROOM_BLOCK,
			Blocks.BROWN_MUSHROOM_BLOCK,
			Blocks.LILY_PAD,
			Blocks.CACTUS,
			Blocks.BUSH,
			Blocks.SHORT_DRY_GRASS,
			Blocks.TALL_DRY_GRASS,
			Blocks.CACTUS_FLOWER,
			Blocks.PINK_PETALS,
			Blocks.WILDFLOWERS,
			Blocks.LEAF_LITTER,
			Blocks.FIREFLY_BUSH,
			Blocks.SPORE_BLOSSOM,
			Blocks.BIG_DRIPLEAF,
			Blocks.BIG_DRIPLEAF_STEM,
			Blocks.SMALL_DRIPLEAF,
			Blocks.HANGING_ROOTS,
			Blocks.ROOTED_DIRT,
			Blocks.PACKED_MUD,
			Blocks.SANDSTONE,
			Blocks.RED_SANDSTONE,
			Blocks.MOSSY_COBBLESTONE,
			Blocks.INFESTED_STONE,
			Blocks.INFESTED_DEEPSLATE
		);
	}

	private SanctuaryPreflightValidator() {
	}

	public record CheckResult(String code, boolean passed, String detail) {
	}

	public record TerrainMetrics(
		int minCoreY,
		int maxCoreY,
		int medianCoreY,
		int liquidHits,
		int nonNaturalHits,
		int blockEntityHits,
		int structureOverlapHits,
		String sampleDiagnostic
	) {
		public TerrainMetrics(
			int minCoreY,
			int maxCoreY,
			int medianCoreY,
			int liquidHits,
			int nonNaturalHits,
			int blockEntityHits,
			int structureOverlapHits
		) {
			this(minCoreY, maxCoreY, medianCoreY, liquidHits, nonNaturalHits, blockEntityHits, structureOverlapHits, "");
		}

		public int relief() {
			return maxCoreY - minCoreY;
		}
	}

	public record PreflightReport(
		boolean passed,
		BlockPos requestedCenter,
		Rotation rotation,
		TerrainMetrics terrainMetrics,
		List<CheckResult> checks
	) {
		public List<CheckResult> failures() {
			return checks.stream().filter(c -> !c.passed()).toList();
		}
	}

	/** Pure deterministic precondition validator (unit-testable without a running server). */
	public static List<CheckResult> validatePreconditions(
		CanopyCavernConfig config,
		SanctuarySavedState state,
		boolean hasAdminPermission,
		boolean isOverworld,
		boolean backupVerified,
		boolean requireBackupForAction
	) {
		List<CheckResult> results = new ArrayList<>();

		results.add(new CheckResult(
			"CONFIG_ENABLED",
			config != null && config.spawnHubEnabled(),
			config != null && config.spawnHubEnabled()
				? "spawnHubEnabled is true"
				: "Disabled by default in config/canopycavern.json (set spawnHubEnabled=true to opt in)"
		));

		results.add(new CheckResult(
			"ADMIN_PERMISSION",
			hasAdminPermission,
			hasAdminPermission
				? "Server-side admin permission verified"
				: "Insufficient server permission (requires admin level / canopycavern.command.sanctuary)"
		));

		results.add(new CheckResult(
			"DIMENSION_OVERWORLD",
			isOverworld,
			isOverworld
				? "Target dimension is minecraft:overworld"
				: "Canopy Sanctuary can only be installed in minecraft:overworld"
		));

		SanctuarySavedState.InstallStatus status = state == null ? SanctuarySavedState.InstallStatus.NONE : state.status();
		boolean cleanState = status == SanctuarySavedState.InstallStatus.NONE;
		String stateMsg = switch (status) {
			case NONE -> "No prior Sanctuary installation recorded";
			case INSTALLED -> "Sanctuary is already installed in this world (duplicate install blocked)";
			case IN_PROGRESS -> "Interrupted Sanctuary installation recorded (run /canopy sanctuary reset-failed after backup restore)";
			case FAILED -> "Previous Sanctuary installation failed (" + state.lastError() + "); restore backup before retry";
		};
		results.add(new CheckResult("IDEMPOTENT_STATE", cleanState, stateMsg));

		if (requireBackupForAction) {
			boolean requireBackup = config != null && config.spawnHubRequireBackupConfirmation();
			boolean backupOk = !requireBackup || backupVerified;
			results.add(new CheckResult(
				"WORLD_BACKUP",
				backupOk,
				backupOk
					? (requireBackup ? "Verified pre-install backup exists" : "Backup gate skipped by config")
					: "Mandatory world backup missing; run /canopy sanctuary backup first"
			));
		}

		return results;
	}

	/** Evaluates terrain suitability rules purely from sampled surface metrics. */
	public static List<CheckResult> evaluateTerrainMetrics(
		BlockPos center,
		int worldMinY,
		int worldMaxY,
		BoundingBox envelope,
		boolean withinWorldBorder,
		boolean nearVanillaVillage,
		TerrainMetrics metrics
	) {
		List<CheckResult> results = new ArrayList<>();

		boolean heightOk = envelope.minY() >= worldMinY + 1 && envelope.maxY() <= worldMaxY - 1;
		results.add(new CheckResult(
			"HEIGHT_BOUNDS",
			heightOk,
			heightOk
				? "Envelope Y [" + envelope.minY() + ".." + envelope.maxY() + "] fits world limits"
				: "Envelope Y [" + envelope.minY() + ".." + envelope.maxY() + "] exceeds world bounds [" + worldMinY + ".." + worldMaxY + "]"
		));

		results.add(new CheckResult(
			"WORLD_BORDER",
			withinWorldBorder,
			withinWorldBorder
				? "Full 191x191 envelope lies within active WorldBorder"
				: "Hub footprint intersects or crosses active WorldBorder"
		));

		boolean dryOk = metrics.liquidHits() == 0;
		String diagSuffix = metrics.sampleDiagnostic().isBlank() ? "" : " [" + metrics.sampleDiagnostic() + "]";
		results.add(new CheckResult(
			"DRY_CORE_TERRAIN",
			dryOk,
			dryOk
				? "Core Sanctuary plaza/hall footprint is dry and solid"
				: "Detected " + metrics.liquidHits() + " surface/core liquid hazard column(s) (water/lava)" + diagSuffix
		));

		int relief = metrics.relief();
		int centerDelta = Math.abs(center.getY() - metrics.medianCoreY());
		boolean slopeOk = relief <= MAX_CORE_RELIEF_BLOCKS && centerDelta <= MAX_CENTER_GROUND_DELTA;
		results.add(new CheckResult(
			"TERRAIN_SLOPE",
			slopeOk,
			slopeOk
				? "Core relief=" + relief + " (<= " + MAX_CORE_RELIEF_BLOCKS + "), medianY=" + metrics.medianCoreY() + ", centerY=" + center.getY()
				: "Unsafe terrain elevation/slope (relief=" + relief + ", medianY=" + metrics.medianCoreY() + ", centerY=" + center.getY() + ")"
		));

		boolean occupancyOk = metrics.blockEntityHits() == 0 && metrics.nonNaturalHits() == 0;
		results.add(new CheckResult(
			"OCCUPIED_AREA_CHECK",
			occupancyOk,
			occupancyOk
				? "No existing player builds or block entities detected inside hub bounds"
				: "Refusing to overwrite occupied area (blockEntities=" + metrics.blockEntityHits() + ", nonNaturalBlocks=" + metrics.nonNaturalHits() + ")" + diagSuffix
		));

		boolean structuresOk = !nearVanillaVillage && metrics.structureOverlapHits() == 0;
		results.add(new CheckResult(
			"EXISTING_STRUCTURES",
			structuresOk,
			structuresOk
				? "No intersecting village or registered world structures detected"
				: "Overlaps existing structure/village (nearVillage=" + nearVanillaVillage + ", overlaps=" + metrics.structureOverlapHits() + ")" + diagSuffix
		));

		return results;
	}

	/** Full live ServerLevel preflight scan (safe read-only terrain + chunk collision verification). */
	public static PreflightReport runLivePreflight(
		CanopyCavernConfig config,
		SanctuaryManifest manifest,
		SanctuarySavedState state,
		ServerLevel level,
		BlockPos center,
		Rotation rotation,
		boolean hasAdminPermission,
		boolean requireBackupGate
	) {
		return runLivePreflight(
			config,
			manifest,
			state,
			level,
			center,
			rotation,
			hasAdminPermission,
			requireBackupGate,
			requireBackupGate
		);
	}

	/** Full live ServerLevel preflight scan with explicit precondition fast-fail control. */
	public static PreflightReport runLivePreflight(
		CanopyCavernConfig config,
		SanctuaryManifest manifest,
		SanctuarySavedState state,
		ServerLevel level,
		BlockPos center,
		Rotation rotation,
		boolean hasAdminPermission,
		boolean requireBackupGate,
		boolean fastFailOnPreconditionFailure
	) {
		boolean isOverworld = Level.OVERWORLD.equals(level.dimension());
		boolean backupOk = SanctuaryBackupService.hasVerifiedBackup(state);
		List<CheckResult> allChecks = new ArrayList<>(validatePreconditions(
			config, state, hasAdminPermission, isOverworld, backupOk, requireBackupGate
		));

		// Fast-fail before chunk scans when mandatory install gates (config, permission, idempotency, backup) already fail
		if (fastFailOnPreconditionFailure && allChecks.stream().anyMatch(c -> !c.passed())) {
			TerrainMetrics empty = new TerrainMetrics(center.getY(), center.getY(), center.getY(), 0, 0, 0, 0, "skipped-on-precondition-fail");
			return new PreflightReport(false, center.immutable(), rotation, empty, Collections.unmodifiableList(allChecks));
		}

		BoundingBox envelope = manifest.envelopeBoundingBoxWorld(center, rotation);
		WorldBorder border = level.getWorldBorder();
		boolean withinBorder =
			border.isWithinBounds(new BlockPos(envelope.minX(), center.getY(), envelope.minZ()))
			&& border.isWithinBounds(new BlockPos(envelope.maxX(), center.getY(), envelope.maxZ()))
			&& border.isWithinBounds(new BlockPos(envelope.minX(), center.getY(), envelope.maxZ()))
			&& border.isWithinBounds(new BlockPos(envelope.maxX(), center.getY(), envelope.minZ()));

		TerrainMetrics metrics = scanFootprint(manifest, level, center, rotation, envelope);
		boolean nearVillage = level.isCloseToVillage(center, 6);

		allChecks.addAll(evaluateTerrainMetrics(
			center,
			level.getMinY(),
			level.getMaxY(),
			envelope,
			withinBorder,
			nearVillage,
			metrics
		));

		boolean passed = allChecks.stream().allMatch(CheckResult::passed);
		return new PreflightReport(passed, center.immutable(), rotation, metrics, Collections.unmodifiableList(allChecks));
	}

	private static TerrainMetrics scanFootprint(
		SanctuaryManifest manifest,
		ServerLevel level,
		BlockPos center,
		Rotation rotation,
		BoundingBox envelope
	) {
		// Build exact rotated piece bounding boxes (with 2-block XZ buffer) so unrelated deep mineshafts
		// outside placed modules do not falsely block valid surface sites.
		List<BoundingBox> bufferedPieceBoxes = new ArrayList<>(manifest.pieces().size());
		for (SanctuaryManifest.PieceSpec piece : manifest.pieces()) {
			BoundingBox box = manifest.pieceBoundingBoxWorld(center, piece, rotation);
			bufferedPieceBoxes.add(new BoundingBox(
				box.minX() - 2, box.minY() - 1, box.minZ() - 2,
				box.maxX() + 2, box.maxY() + 2, box.maxZ() + 2
			));
		}

		// Load chunks FIRST so Heightmap and getBlockState never read empty/unloaded sections (-64)
		int blockEntityHits = 0;
		int structureOverlapHits = 0;
		StringBuilder diagnostics = new StringBuilder();
		int minChunkX = SectionPos.blockToSectionCoord(envelope.minX());
		int maxChunkX = SectionPos.blockToSectionCoord(envelope.maxX());
		int minChunkZ = SectionPos.blockToSectionCoord(envelope.minZ());
		int maxChunkZ = SectionPos.blockToSectionCoord(envelope.maxZ());
		var structureRegistry = level.registryAccess().lookup(Registries.STRUCTURE);

		for (int cx = minChunkX; cx <= maxChunkX; cx++) {
			for (int cz = minChunkZ; cz <= maxChunkZ; cz++) {
				LevelChunk chunk = (LevelChunk) level.getChunk(cx, cz, ChunkStatus.FULL, true);
				if (chunk == null) {
					continue;
				}
				for (Map.Entry<BlockPos, BlockEntity> entry : chunk.getBlockEntities().entrySet()) {
					BlockPos bPos = entry.getKey();
					if (intersectsAny(bPos, bufferedPieceBoxes)) {
						// Natural tree bee nests on virgin oak/birch trunks do not indicate player structures
						if (entry.getValue() instanceof BeehiveBlockEntity && chunk.getBlockState(bPos).is(Blocks.BEE_NEST)) {
							continue;
						}
						blockEntityHits++;
						if (diagnostics.length() < 140) {
							diagnostics.append("be=").append(BuiltInRegistries.BLOCK.getKey(chunk.getBlockState(bPos).getBlock()))
								.append('@').append(bPos.toShortString()).append(';');
						}
					}
				}
				for (Map.Entry<net.minecraft.world.level.levelgen.structure.Structure, StructureStart> entry : chunk.getAllStarts().entrySet()) {
					StructureStart start = entry.getValue();
					if (start == null || !start.isValid() || !start.getBoundingBox().intersects(envelope)) {
						continue;
					}
					boolean pieceCollision = start.getPieces().stream()
						.anyMatch(sp -> sp != null && intersectsAny(sp.getBoundingBox(), bufferedPieceBoxes));
					if (pieceCollision) {
						structureOverlapHits++;
						if (diagnostics.length() < 140) {
							String name = structureRegistry.flatMap(r -> r.getResourceKey(entry.getKey()))
								.map(k -> k.identifier().toString()).orElse("structure");
							diagnostics.append("struct=").append(name).append(';');
						}
					}
				}
			}
		}

		List<Integer> coreHeights = new ArrayList<>();
		int liquidHits = 0;
		int nonNaturalHits = 0;

		// 1. Sample surface relief & surface liquids / constructed blocks across core hub radius
		for (int dx = -CORE_SAMPLE_RADIUS; dx <= CORE_SAMPLE_RADIUS; dx += SAMPLE_STEP) {
			for (int dz = -CORE_SAMPLE_RADIUS; dz <= CORE_SAMPLE_RADIUS; dz += SAMPLE_STEP) {
				int wx = center.getX() + dx;
				int wz = center.getZ() + dz;
				int groundY = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, wx, wz) - 1;
				coreHeights.add(groundY);

				BlockPos topPos = new BlockPos(wx, groundY, wz);
				BlockState topState = level.getBlockState(topPos);
				BlockState aboveState = level.getBlockState(topPos.above());
				if (!topState.getFluidState().isEmpty() || !aboveState.getFluidState().isEmpty()) {
					liquidHits++;
					if (diagnostics.length() < 140) {
						BlockState liq = !aboveState.getFluidState().isEmpty() ? aboveState : topState;
						diagnostics.append("liq=").append(BuiltInRegistries.BLOCK.getKey(liq.getBlock()))
							.append('@').append(topPos.toShortString()).append(';');
					}
				} else if (!isNaturalReplaceableBlock(topState)) {
					nonNaturalHits++;
					if (diagnostics.length() < 140) {
						diagnostics.append("blk=").append(BuiltInRegistries.BLOCK.getKey(topState.getBlock()))
							.append('@').append(topPos.toShortString()).append(';');
					}
				}
			}
		}

		// Also check Arrival Pad corners & center + surface road corridor ends at +-88 so roads don't cross open ocean/lava.
		int[][] criticalSurfacePoints = {
			{0, 0}, {-6, -6}, {6, -6}, {-6, 6}, {6, 6},
			{0, -40}, {0, 40}, {-40, 0}, {40, 0}, {0, -88}, {0, 88}, {-88, 0}, {88, 0}
		};
		for (int[] rel : criticalSurfacePoints) {
			BlockPos wp = SanctuaryManifest.toWorldPos(center, rel[0], 0, rel[1], rotation);
			int gy = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, wp.getX(), wp.getZ()) - 1;
			BlockPos gp = new BlockPos(wp.getX(), gy, wp.getZ());
			BlockState groundState = level.getBlockState(gp);
			BlockState aboveGround = level.getBlockState(gp.above());
			if (!groundState.getFluidState().isEmpty() || !aboveGround.getFluidState().isEmpty()) {
				liquidHits++;
				if (diagnostics.length() < 140) {
					BlockState liq = !aboveGround.getFluidState().isEmpty() ? aboveGround : groundState;
					diagnostics.append("roadLiq=").append(BuiltInRegistries.BLOCK.getKey(liq.getBlock()))
						.append('@').append(gp.toShortString()).append(';');
				}
			} else if (!isNaturalReplaceableBlock(groundState)) {
				nonNaturalHits++;
			}
		}

		// 2. Sample vertical slices inside every building/pavilion/cavern piece AABB for underground lava/player bases
		for (SanctuaryManifest.PieceSpec piece : manifest.pieces()) {
			BoundingBox box = manifest.pieceBoundingBoxWorld(center, piece, rotation);
			int yStep = 6;
			int xzStep = 8;
			for (int x = box.minX(); x <= box.maxX(); x += xzStep) {
				for (int z = box.minZ(); z <= box.maxZ(); z += xzStep) {
					for (int y = box.minY(); y <= Math.min(box.maxY(), center.getY() + 12); y += yStep) {
						BlockPos p = new BlockPos(x, y, z);
						BlockState state = level.getBlockState(p);
						if (state.is(Blocks.LAVA)) {
							liquidHits++;
							if (diagnostics.length() < 140) {
								diagnostics.append("lava@").append(p.toShortString()).append(';');
							}
						} else if (state.getFluidState().isEmpty() && !isNaturalReplaceableBlock(state)) {
							nonNaturalHits++;
							if (diagnostics.length() < 140) {
								diagnostics.append("ug=").append(BuiltInRegistries.BLOCK.getKey(state.getBlock()))
									.append('@').append(p.toShortString()).append(';');
							}
						}
					}
				}
			}
		}

		if (coreHeights.isEmpty()) {
			return new TerrainMetrics(center.getY(), center.getY(), center.getY(), liquidHits, nonNaturalHits, blockEntityHits, structureOverlapHits, diagnostics.toString());
		}
		Collections.sort(coreHeights);
		int minCoreY = coreHeights.getFirst();
		int maxCoreY = coreHeights.getLast();
		int medianCoreY = coreHeights.get(coreHeights.size() / 2);

		return new TerrainMetrics(minCoreY, maxCoreY, medianCoreY, liquidHits, nonNaturalHits, blockEntityHits, structureOverlapHits, diagnostics.toString());
	}

	private static boolean intersectsAny(BlockPos pos, List<BoundingBox> boxes) {
		for (BoundingBox box : boxes) {
			if (box.isInside(pos)) {
				return true;
			}
		}
		return false;
	}

	private static boolean intersectsAny(BoundingBox target, List<BoundingBox> boxes) {
		for (BoundingBox box : boxes) {
			if (box.intersects(target)) {
				return true;
			}
		}
		return false;
	}

	/** Allowlist of unmodified vanilla & TerraBlender natural terrain blocks safe to adapt cleanly. */
	public static boolean isNaturalReplaceableBlock(BlockState state) {
		if (state == null || state.isAir()) {
			return true;
		}
		if (NaturalBlockSetHolder.EXTRA_NATURAL_BLOCKS.contains(state.getBlock())) {
			return true;
		}
		return state.is(BlockTags.DIRT)
			|| state.is(BlockTags.SAND)
			|| state.is(BlockTags.BASE_STONE_OVERWORLD)
			|| state.is(BlockTags.TERRACOTTA)
			|| state.is(BlockTags.LOGS)
			|| state.is(BlockTags.LEAVES)
			|| state.is(BlockTags.FLOWERS)
			|| state.is(BlockTags.IRON_ORES)
			|| state.is(BlockTags.COPPER_ORES)
			|| state.is(BlockTags.GOLD_ORES)
			|| state.is(BlockTags.DEEPSLATE_ORE_REPLACEABLES)
			|| state.is(BlockTags.STONE_ORE_REPLACEABLES);
	}
}
