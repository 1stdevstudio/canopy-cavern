package com.yogi.canopycavern.world.spawn;

import com.yogi.canopycavern.CanopyCavernMod;
import com.yogi.canopycavern.config.CanopyCavernConfig;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.LecternBlockEntity;
import net.minecraft.world.level.block.entity.SignBlockEntity;
import net.minecraft.world.level.block.entity.SignTextSlot;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.gamerules.GameRules;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.minecraft.world.level.storage.LevelData;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Coordinates fail-closed preflight preview, bounded multi-tick modular installation,
 * foundation skirt stabilization, localized signage/lecterns, and optional post-install spawn updates.
 */
public final class SanctuaryPlacementService {
	private static final Logger LOGGER = LoggerFactory.getLogger("canopycavern-sanctuary");
	private static final int LARGE_PIECE_BLOCK_THRESHOLD = 9000;
	private static final int SLICE_BAND_HEIGHT = 8;

	private static final Map<MinecraftServer, ActiveInstallJob> ACTIVE_JOBS = new ConcurrentHashMap<>();

	private SanctuaryPlacementService() {
	}

	private record PlacementSlice(
		SanctuaryManifest.PieceSpec piece,
		BoundingBox clipBox,
		boolean finalSliceOfPiece
	) {
	}

	private static final class ActiveInstallJob {
		final SanctuaryManifest manifest;
		final BlockPos center;
		final Rotation rotation;
		final int totalSlices;
		final Deque<PlacementSlice> queue = new ArrayDeque<>();
		final long startNanos = System.nanoTime();
		int completedSlices = 0;
		int ticksElapsed = 0;
		String initiatorName;

		ActiveInstallJob(SanctuaryManifest manifest, BlockPos center, Rotation rotation, String initiatorName) {
			this.manifest = manifest;
			this.center = center.immutable();
			this.rotation = rotation;
			this.initiatorName = initiatorName;

			for (SanctuaryManifest.PieceSpec piece : manifest.pieces()) {
				BoundingBox pieceBox = manifest.pieceBoundingBoxWorld(center, piece, rotation);
				if (piece.nonAirBlocks() > LARGE_PIECE_BLOCK_THRESHOLD) {
					var bands = SanctuaryManifest.sliceVerticalBands(pieceBox, SLICE_BAND_HEIGHT);
					for (int i = 0; i < bands.size(); i++) {
						queue.addLast(new PlacementSlice(piece, bands.get(i), i == bands.size() - 1));
					}
				} else {
					queue.addLast(new PlacementSlice(piece, pieceBox, true));
				}
			}
			this.totalSlices = queue.size();
		}
	}

	public record InstallStartResult(boolean started, String message, SanctuaryPreflightValidator.PreflightReport report) {
	}

	public record SetSpawnResult(boolean success, String message, BlockPos arrivalPos, float yaw) {
	}

	/** Registers server startup diagnostics, bounded tick worker, and clean shutdown cleanup. */
	public static void registerLifecycle() {
		ServerLifecycleEvents.SERVER_STARTED.register(server -> {
			SanctuarySavedState state = SanctuarySavedState.get(server);
			switch (state.status()) {
				case IN_PROGRESS -> LOGGER.warn(
					"Detected interrupted Canopy Sanctuary installation at {} ({}/{} pieces). World left untouched; admin should inspect or restore backup and run /canopy sanctuary reset-failed.",
					state.center(),
					state.placedPieceIds().size(),
					SanctuaryManifest.loadDefault().pieces().size()
				);
				case INSTALLED -> LOGGER.info(
					"Canopy Sanctuary active at {} (rot={}, protectionEnabled={}, worldSpawnUpdated={}).",
					state.center(),
					state.rotation(),
					state.protectionEnabled(),
					state.worldSpawnUpdated()
				);
				case FAILED -> LOGGER.warn(
					"Previous Canopy Sanctuary installation failed: {}",
					state.lastError()
				);
				case NONE -> LOGGER.debug("Canopy Sanctuary status: NONE (spawnHubEnabled={}).", CanopyCavernMod.getConfig().spawnHubEnabled());
			}
		});

		ServerLifecycleEvents.SERVER_STOPPED.register(ACTIVE_JOBS::remove);
		ServerTickEvents.END_SERVER_TICK.register(SanctuaryPlacementService::onServerTick);
	}

	/** Non-mutating site preview: runs preflight diagnostics and emits client-visible particles for admin. */
	public static SanctuaryPreflightValidator.PreflightReport preview(
		MinecraftServer server,
		ServerLevel level,
		BlockPos center,
		Rotation rotation,
		boolean hasAdminPermission,
		ServerPlayer visualViewer
	) {
		SanctuaryManifest manifest = SanctuaryManifest.loadDefault();
		SanctuarySavedState state = SanctuarySavedState.get(server);
		SanctuaryPreflightValidator.PreflightReport report = SanctuaryPreflightValidator.runLivePreflight(
			CanopyCavernMod.getConfig(),
			manifest,
			state,
			level,
			center,
			rotation,
			hasAdminPermission,
			false
		);

		if (visualViewer != null && Level.OVERWORLD.equals(level.dimension())) {
			emitPreviewOutlineParticles(level, visualViewer, manifest, center, rotation, report.passed());
		}
		return report;
	}

	/** Starts a bounded multi-tick Sanctuary installation after re-verifying all fail-closed gates. */
	public static InstallStartResult startInstall(
		MinecraftServer server,
		ServerLevel level,
		BlockPos center,
		Rotation rotation,
		boolean hasAdminPermission,
		String initiatorName
	) {
		if (ACTIVE_JOBS.containsKey(server)) {
			return new InstallStartResult(false, "A Canopy Sanctuary installation is already in progress.", null);
		}

		CanopyCavernConfig config = CanopyCavernMod.getConfig();
		SanctuaryManifest manifest = SanctuaryManifest.loadDefault();
		SanctuarySavedState state = SanctuarySavedState.get(server);

		SanctuaryPreflightValidator.PreflightReport report = SanctuaryPreflightValidator.runLivePreflight(
			config,
			manifest,
			state,
			level,
			center,
			rotation,
			hasAdminPermission,
			true
		);
		if (!report.passed()) {
			String summary = report.failures().stream()
				.map(f -> f.code() + ": " + f.detail())
				.reduce((a, b) -> a + " | " + b)
				.orElse("Preflight rejected");
			return new InstallStartResult(false, "Preflight failed — placement aborted without modifying blocks: " + summary, report);
		}

		// Verify every template asset resolves cleanly BEFORE mutating any world block
		var templateMgr = level.getStructureTemplateManager();
		for (SanctuaryManifest.PieceSpec piece : manifest.pieces()) {
			if (templateMgr.get(piece.templateIdentifier()).isEmpty()) {
				return new InstallStartResult(
					false,
					"Missing Sanctuary structure template asset: " + piece.template(),
					report
				);
			}
		}

		state.markInstallStarted(
			manifest.schemaVersion(),
			manifest.hubId(),
			center,
			rotation,
			config.spawnHubArrivalSafeRadius()
		);
		server.overworld().getDataStorage().saveAndJoin();

		ActiveInstallJob job = new ActiveInstallJob(manifest, center, rotation, initiatorName);
		ACTIVE_JOBS.put(server, job);
		LOGGER.info(
			"Started Canopy Sanctuary installation at {} (rot={}, slices={}, initiator={})",
			center,
			rotation,
			job.totalSlices,
			initiatorName
		);
		return new InstallStartResult(
			true,
			"Started Canopy Sanctuary installation (" + manifest.pieces().size() + " modules, " + job.totalSlices + " bounded ticks).",
			report
		);
	}

	/** Explicit post-install world spawn relocation (never modifies player beds, anchors, or inventories). */
	public static SetSpawnResult setWorldSpawnToSanctuary(MinecraftServer server) {
		SanctuarySavedState state = SanctuarySavedState.get(server);
		if (!state.isInstalled()) {
			return new SetSpawnResult(
				false,
				"Cannot set world spawn before Canopy Sanctuary installation completes (status=" + state.status() + ").",
				BlockPos.ZERO,
				0.0F
			);
		}
		SanctuaryManifest manifest = SanctuaryManifest.loadDefault();
		ServerLevel overworld = server.overworld();
		BlockPos arrival = manifest.arrivalWorldPos(state.center(), state.rotation());
		float yaw = manifest.arrivalYaw(state.rotation());

		if (!isSafeArrivalSpot(overworld, arrival)) {
			return new SetSpawnResult(
				false,
				"Arrival spot " + arrival + " is obstructed or lacks solid footing; world spawn left unchanged.",
				arrival,
				yaw
			);
		}

		overworld.setRespawnData(LevelData.RespawnData.of(Level.OVERWORLD, arrival, yaw, 0.0F));
		// Set Overworld respawn_radius to 0 so new/bedless arrivals land on the open Arrival Pad instead of scattered onto canopy limbs.
		overworld.getGameRules().set(GameRules.RESPAWN_RADIUS, 0, server);
		state.markWorldSpawnUpdated(true);
		overworld.getDataStorage().saveAndJoin();
		LOGGER.info("Updated Overworld spawn point to Canopy Sanctuary arrival pad {} (yaw={}); player beds & inventories untouched.", arrival, yaw);
		return new SetSpawnResult(
			true,
			"World spawn updated to Canopy Sanctuary arrival pad at " + arrival.toShortString() + " (yaw=" + Math.round(yaw) + ").",
			arrival,
			yaw
		);
	}

	private static void onServerTick(MinecraftServer server) {
		ActiveInstallJob job = ACTIVE_JOBS.get(server);
		if (job == null) {
			return;
		}
		job.ticksElapsed++;
		PlacementSlice slice = job.queue.pollFirst();
		if (slice == null) {
			completeInstallJob(server, job);
			return;
		}

		ServerLevel level = server.overworld();
		SanctuarySavedState state = SanctuarySavedState.get(server);
		try {
			Optional<StructureTemplate> maybeTemplate = level.getStructureTemplateManager().get(slice.piece().templateIdentifier());
			if (maybeTemplate.isEmpty()) {
				throw new IllegalStateException("Missing template " + slice.piece().template());
			}
			StructureTemplate template = maybeTemplate.get();
			BlockPos placeOrigin = job.manifest.pieceOriginWorld(job.center, slice.piece(), job.rotation);

			StructurePlaceSettings settings = new StructurePlaceSettings()
				.setMirror(Mirror.NONE)
				.setRotation(job.rotation)
				.setRotationPivot(BlockPos.ZERO)
				.setIgnoreEntities(true)
				.setKnownShape(true)
				.setBoundingBox(slice.clipBox());

			RandomSource random = RandomSource.create(placeOrigin.asLong());
			boolean placed = template.placeInWorld(level, placeOrigin, placeOrigin, settings, random, Block.UPDATE_CLIENTS);
			if (!placed) {
				throw new IllegalStateException("StructureTemplate.placeInWorld returned false for " + slice.piece().id());
			}

			if (slice.finalSliceOfPiece()) {
				applyFoundationSkirtIfNeeded(level, job, slice.piece());
				populateSignsAndLecterns(level, job, slice.piece());
				state.recordPiecePlaced(slice.piece().id());
			}
			job.completedSlices++;

			if (job.queue.isEmpty()) {
				completeInstallJob(server, job);
			}
		} catch (Exception ex) {
			LOGGER.error("Canopy Sanctuary placement failed on piece {}", slice.piece().id(), ex);
			ACTIVE_JOBS.remove(server);
			state.markInstallFailed("Failed placing " + slice.piece().id() + ": " + ex.getMessage());
			level.getDataStorage().saveAndJoin();
			broadcastAdminMessage(
				server,
				Component.literal("[Canopy Sanctuary] Install FAILED on " + slice.piece().id() + ": " + ex.getMessage() + ". Restore your backup before retrying.")
			);
		}
	}

	private static void completeInstallJob(MinecraftServer server, ActiveInstallJob job) {
		ACTIVE_JOBS.remove(server);
		ServerLevel overworld = server.overworld();
		ensureArrivalPadClearance(overworld, job.manifest, job.center, job.rotation);

		SanctuarySavedState state = SanctuarySavedState.get(server);
		state.markInstallCompleted();
		overworld.getDataStorage().saveAndJoin();

		long millis = (System.nanoTime() - job.startNanos) / 1_000_000L;
		BlockPos arrival = job.manifest.arrivalWorldPos(job.center, job.rotation);
		LOGGER.info(
			"Completed Canopy Sanctuary installation at {} (rot={}) in {} ms ({} ticks). Run /canopy sanctuary set-spawn when ready.",
			job.center,
			job.rotation,
			millis,
			job.ticksElapsed
		);
		broadcastAdminMessage(
			server,
			Component.literal(
				"[Canopy Sanctuary] Installation COMPLETE at " + job.center.toShortString()
					+ " (" + job.manifest.pieces().size() + " modules, " + job.ticksElapsed + " ticks, " + millis + " ms). "
					+ "Arrival pad=" + arrival.toShortString()
					+ ". Protection is ON. Run /canopy sanctuary set-spawn if you want Overworld spawn relocated here."
			)
		);
	}

	/** Grounds outer edges of surface pieces down into gentle natural slopes up to {@code foundationSkirt} blocks. */
	private static void applyFoundationSkirtIfNeeded(ServerLevel level, ActiveInstallJob job, SanctuaryManifest.PieceSpec piece) {
		if (piece.foundationSkirt() <= 0) {
			return;
		}
		BoundingBox box = job.manifest.pieceBoundingBoxWorld(job.center, piece, job.rotation);
		int baseY = job.center.getY() + piece.offset()[1];
		int skirtDepth = piece.foundationSkirt();
		BlockState filler = baseY < job.center.getY() - 8
			? Blocks.DEEPSLATE.defaultBlockState()
			: Blocks.STONE.defaultBlockState();
		BlockState cap = Blocks.TUFF.defaultBlockState();

		for (int x = box.minX(); x <= box.maxX(); x++) {
			for (int z = box.minZ(); z <= box.maxZ(); z++) {
				// Anchor skirt along perimeter and every 2nd grid support beam for natural blended terrain contact
				boolean onPerimeter = x == box.minX() || x == box.maxX() || z == box.minZ() || z == box.maxZ();
				if (!onPerimeter && ((x & 1) != 0 || (z & 1) != 0)) {
					continue;
				}
				BlockPos basePos = new BlockPos(x, baseY, z);
				if (level.getBlockState(basePos).isAir()) {
					continue;
				}
				for (int dy = 1; dy <= skirtDepth; dy++) {
					BlockPos below = new BlockPos(x, baseY - dy, z);
					if (below.getY() <= level.getMinY()) {
						break;
					}
					BlockState existing = level.getBlockState(below);
					if (!existing.isAir() && existing.getFluidState().isEmpty() && existing.isSolidRender()) {
						break;
					}
					level.setBlock(below, dy == 1 ? cap : filler, Block.UPDATE_CLIENTS);
				}
			}
		}
	}

	private static void populateSignsAndLecterns(ServerLevel level, ActiveInstallJob job, SanctuaryManifest.PieceSpec piece) {
		if (piece.signs() != null) {
			for (SanctuaryManifest.SignSpec signSpec : piece.signs()) {
				BlockPos signPos = SanctuaryManifest.toWorldPos(
					job.center,
					signSpec.offset()[0],
					signSpec.offset()[1],
					signSpec.offset()[2],
					job.rotation
				);
				BlockEntity be = level.getBlockEntity(signPos);
				if (be instanceof SignBlockEntity signEntity) {
					signEntity.setText(SanctuaryLocalization.buildSignText(signSpec.lines(), signSpec.glowing()), SignTextSlot.FRONT);
					signEntity.setWaxed(true);
					signEntity.setChanged();
					BlockState state = level.getBlockState(signPos);
					level.sendBlockUpdated(signPos, state, state, Block.UPDATE_ALL);
				} else {
					LOGGER.warn("Expected SignBlockEntity at {} for piece {}, found {}", signPos, piece.id(), be);
				}
			}
		}

		if (piece.lecterns() != null) {
			for (SanctuaryManifest.LecternSpec lecternSpec : piece.lecterns()) {
				BlockPos lecternPos = SanctuaryManifest.toWorldPos(
					job.center,
					lecternSpec.offset()[0],
					lecternSpec.offset()[1],
					lecternSpec.offset()[2],
					job.rotation
				);
				BlockEntity be = level.getBlockEntity(lecternPos);
				if (be instanceof LecternBlockEntity lecternEntity) {
					lecternEntity.setBook(SanctuaryLocalization.buildLecternBook(lecternSpec.bookKey()));
					lecternEntity.setChanged();
					BlockState state = level.getBlockState(lecternPos);
					if (state.hasProperty(net.minecraft.world.level.block.LecternBlock.HAS_BOOK)
						&& !state.getValue(net.minecraft.world.level.block.LecternBlock.HAS_BOOK)) {
						state = state.setValue(net.minecraft.world.level.block.LecternBlock.HAS_BOOK, true);
						level.setBlock(lecternPos, state, Block.UPDATE_ALL);
					} else {
						level.sendBlockUpdated(lecternPos, state, state, Block.UPDATE_ALL);
					}
				} else {
					LOGGER.warn("Expected LecternBlockEntity at {} for piece {}, found {}", lecternPos, piece.id(), be);
				}
			}
		}
	}

	private static void ensureArrivalPadClearance(ServerLevel level, SanctuaryManifest manifest, BlockPos center, Rotation rotation) {
		BlockPos arrival = manifest.arrivalWorldPos(center, rotation);
		for (int dx = -1; dx <= 1; dx++) {
			for (int dz = -1; dz <= 1; dz++) {
				for (int dy = 0; dy <= 3; dy++) {
					BlockPos clearPos = arrival.offset(dx, dy, dz);
					if (!level.getBlockState(clearPos).isAir()) {
						level.setBlock(clearPos, Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS);
					}
				}
			}
		}
	}

	public static boolean isSafeArrivalSpot(ServerLevel level, BlockPos arrival) {
		BlockState below = level.getBlockState(arrival.below());
		BlockState feet = level.getBlockState(arrival);
		BlockState head = level.getBlockState(arrival.above());
		return !below.isAir()
			&& below.getFluidState().isEmpty()
			&& feet.isAir()
			&& head.isAir()
			&& feet.getFluidState().isEmpty()
			&& head.getFluidState().isEmpty();
	}

	private static void emitPreviewOutlineParticles(
		ServerLevel level,
		ServerPlayer viewer,
		SanctuaryManifest manifest,
		BlockPos center,
		Rotation rotation,
		boolean passed
	) {
		var particle = passed ? ParticleTypes.HAPPY_VILLAGER : ParticleTypes.FLAME;
		// Central 13x13 arrival pad markers & 4 cardinal trail endpoints
		for (int d = -6; d <= 6; d += 3) {
			sendParticle(level, viewer, particle, SanctuaryManifest.toWorldPos(center, d, 2, -6, rotation));
			sendParticle(level, viewer, particle, SanctuaryManifest.toWorldPos(center, d, 2, 6, rotation));
			sendParticle(level, viewer, particle, SanctuaryManifest.toWorldPos(center, -6, 2, d, rotation));
			sendParticle(level, viewer, particle, SanctuaryManifest.toWorldPos(center, 6, 2, d, rotation));
		}
		int[][] landmarks = {
			{0, 2, 0}, {0, 2, -24}, {0, 2, 24}, {-24, 2, 0}, {24, 2, 0},
			{0, 2, -95}, {0, 2, 95}, {-95, 2, 0}, {95, 2, 0},
			{20, 29, 20}, {0, -29, 54}
		};
		for (int[] lm : landmarks) {
			sendParticle(level, viewer, ParticleTypes.END_ROD, SanctuaryManifest.toWorldPos(center, lm[0], lm[1], lm[2], rotation));
		}
	}

	private static void sendParticle(
		ServerLevel level,
		ServerPlayer viewer,
		net.minecraft.core.particles.SimpleParticleType type,
		BlockPos pos
	) {
		level.sendParticles(viewer, type, true, false, pos.getX() + 0.5, pos.getY() + 0.5, pos.getZ() + 0.5, 4, 0.15, 0.15, 0.15, 0.01);
	}

	private static void broadcastAdminMessage(MinecraftServer server, Component msg) {
		for (ServerPlayer player : server.getPlayerList().getPlayers()) {
			if (SpawnSanctuaryProtection.hasAdminPermission(player.createCommandSourceStack())) {
				player.sendSystemMessage(msg);
			}
		}
	}

	public static Optional<String> activeJobProgress(MinecraftServer server) {
		ActiveInstallJob job = ACTIVE_JOBS.get(server);
		if (job == null) {
			return Optional.empty();
		}
		return Optional.of(job.completedSlices + "/" + job.totalSlices + " slices (initiator=" + job.initiatorName + ")");
	}
}
