package com.yogi.canopycavern.world.spawn;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.BoolArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.suggestion.SuggestionProvider;
import com.yogi.canopycavern.CanopyCavernMod;
import com.yogi.canopycavern.config.CanopyCavernConfig;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.commands.arguments.coordinates.BlockPosArgument;
import net.minecraft.core.BlockPos;
import net.minecraft.core.SectionPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.levelgen.Heightmap;

import java.util.List;

/**
 * Registers server-enforced admin commands for Canopy Sanctuary backup, preflight,
 * read-only preview, bounded multi-tick placement, status, protection, and optional spawn update.
 */
public final class SanctuaryCommands {
	private static final SuggestionProvider<CommandSourceStack> ROTATION_SUGGESTIONS = (ctx, builder) ->
		SharedSuggestionProvider.suggest(List.of("none", "clockwise_90", "clockwise_180", "counterclockwise_90"), builder);

	private SanctuaryCommands() {
	}

	public static void register() {
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> registerCommands(dispatcher));
	}

	private static void registerCommands(CommandDispatcher<CommandSourceStack> dispatcher) {
		dispatcher.register(
			Commands.literal("canopy")
				.then(
					Commands.literal("sanctuary")
						.requires(SpawnSanctuaryProtection::hasAdminPermission)
						.then(Commands.literal("status").executes(SanctuaryCommands::executeStatus))
						.then(Commands.literal("backup").executes(SanctuaryCommands::executeBackup))
						.then(
							Commands.literal("preflight")
								.executes(ctx -> executePreflight(ctx, defaultCenter(ctx.getSource()), Rotation.NONE))
								.then(
									Commands.argument("center", BlockPosArgument.blockPos())
										.executes(ctx -> executePreflight(ctx, BlockPosArgument.getBlockPos(ctx, "center"), Rotation.NONE))
										.then(
											Commands.argument("rotation", StringArgumentType.word())
												.suggests(ROTATION_SUGGESTIONS)
												.executes(ctx -> executePreflightWithRot(ctx, BlockPosArgument.getBlockPos(ctx, "center"), StringArgumentType.getString(ctx, "rotation")))
										)
								)
						)
						.then(
							Commands.literal("preview")
								.executes(ctx -> executePreview(ctx, defaultCenter(ctx.getSource()), Rotation.NONE))
								.then(
									Commands.argument("center", BlockPosArgument.blockPos())
										.executes(ctx -> executePreview(ctx, BlockPosArgument.getBlockPos(ctx, "center"), Rotation.NONE))
										.then(
											Commands.argument("rotation", StringArgumentType.word())
												.suggests(ROTATION_SUGGESTIONS)
												.executes(ctx -> executePreviewWithRot(ctx, BlockPosArgument.getBlockPos(ctx, "center"), StringArgumentType.getString(ctx, "rotation")))
										)
								)
						)
						.then(
							Commands.literal("install")
								.executes(ctx -> executeInstall(ctx, defaultCenter(ctx.getSource()), Rotation.NONE))
								.then(
									Commands.argument("center", BlockPosArgument.blockPos())
										.executes(ctx -> executeInstall(ctx, BlockPosArgument.getBlockPos(ctx, "center"), Rotation.NONE))
										.then(
											Commands.argument("rotation", StringArgumentType.word())
												.suggests(ROTATION_SUGGESTIONS)
												.executes(ctx -> executeInstallWithRot(ctx, BlockPosArgument.getBlockPos(ctx, "center"), StringArgumentType.getString(ctx, "rotation")))
										)
								)
						)
						.then(Commands.literal("set-spawn").executes(SanctuaryCommands::executeSetSpawn))
						.then(
							Commands.literal("protection")
								.then(
									Commands.argument("enabled", BoolArgumentType.bool())
										.executes(ctx -> executeProtection(ctx, BoolArgumentType.getBool(ctx, "enabled")))
								)
						)
						.then(Commands.literal("reset-failed").executes(SanctuaryCommands::executeResetFailed))
				)
		);
	}

	private static boolean verifyPermissionServerSide(CommandSourceStack source) {
		if (SpawnSanctuaryProtection.hasAdminPermission(source)) {
			return true;
		}
		source.sendFailure(Component.literal("[Canopy Sanctuary] Permission denied (requires admin permission)."));
		return false;
	}

	private static int executeStatus(CommandContext<CommandSourceStack> ctx) {
		CommandSourceStack source = ctx.getSource();
		if (!verifyPermissionServerSide(source)) {
			return 0;
		}
		MinecraftServer server = source.getServer();
		CanopyCavernConfig config = CanopyCavernMod.getConfig();
		SanctuarySavedState state = SanctuarySavedState.get(server);
		String activeJob = SanctuaryPlacementService.activeJobProgress(server).orElse("none");
		boolean backupValid = SanctuaryBackupService.hasVerifiedBackup(state);

		source.sendSuccess(() -> Component.literal(
			"[Canopy Sanctuary] Status=" + state.status()
				+ ", spawnHubEnabled=" + config.spawnHubEnabled()
				+ ", center=" + state.center().toShortString()
				+ ", rotation=" + state.rotation().name()
				+ ", piecesPlaced=" + state.placedPieceIds().size() + "/" + SanctuaryManifest.loadDefault().pieces().size()
				+ ", protection=" + state.protectionEnabled()
				+ ", worldSpawnUpdated=" + state.worldSpawnUpdated()
				+ ", backupVerified=" + backupValid + (state.backupToken().isEmpty() ? "" : " (" + state.backupToken() + ")")
				+ ", activeJob=" + activeJob
		), false);
		return 1;
	}

	private static int executeBackup(CommandContext<CommandSourceStack> ctx) {
		CommandSourceStack source = ctx.getSource();
		if (!verifyPermissionServerSide(source)) {
			return 0;
		}
		SanctuaryBackupService.BackupResult result = SanctuaryBackupService.createVerifiedBackup(source.getServer(), org.slf4j.LoggerFactory.getLogger("canopycavern"));
		if (!result.success()) {
			source.sendFailure(Component.literal("[Canopy Sanctuary] Backup failed: " + result.errorMessage()));
			return 0;
		}
		source.sendSuccess(() -> Component.literal(
			"[Canopy Sanctuary] Verified world backup saved: " + result.backupFile().getFileName()
				+ " (" + (result.bytesWritten() / 1024L) + " KB, token=" + result.token() + ")"
		), true);
		return 1;
	}

	private static int executePreflightWithRot(CommandContext<CommandSourceStack> ctx, BlockPos center, String rawRot) {
		try {
			return executePreflight(ctx, center, SanctuaryManifest.parseRotation(rawRot));
		} catch (IllegalArgumentException ex) {
			ctx.getSource().sendFailure(Component.literal("[Canopy Sanctuary] " + ex.getMessage()));
			return 0;
		}
	}

	private static int executePreflight(CommandContext<CommandSourceStack> ctx, BlockPos center, Rotation rotation) {
		CommandSourceStack source = ctx.getSource();
		if (!verifyPermissionServerSide(source)) {
			return 0;
		}
		ServerLevel level = source.getLevel();
		SanctuaryPreflightValidator.PreflightReport report = SanctuaryPreflightValidator.runLivePreflight(
			CanopyCavernMod.getConfig(),
			SanctuaryManifest.loadDefault(),
			SanctuarySavedState.get(source.getServer()),
			level,
			center,
			rotation,
			true,
			true,
			false
		);
		sendReport(source, "Preflight", report);
		return report.passed() ? 1 : 0;
	}

	private static int executePreviewWithRot(CommandContext<CommandSourceStack> ctx, BlockPos center, String rawRot) {
		try {
			return executePreview(ctx, center, SanctuaryManifest.parseRotation(rawRot));
		} catch (IllegalArgumentException ex) {
			ctx.getSource().sendFailure(Component.literal("[Canopy Sanctuary] " + ex.getMessage()));
			return 0;
		}
	}

	private static int executePreview(CommandContext<CommandSourceStack> ctx, BlockPos center, Rotation rotation) {
		CommandSourceStack source = ctx.getSource();
		if (!verifyPermissionServerSide(source)) {
			return 0;
		}
		ServerPlayer player = source.getPlayer();
		SanctuaryPreflightValidator.PreflightReport report = SanctuaryPlacementService.preview(
			source.getServer(),
			source.getLevel(),
			center,
			rotation,
			true,
			player
		);
		sendReport(source, "Preview (no blocks modified)", report);
		return report.passed() ? 1 : 0;
	}

	private static int executeInstallWithRot(CommandContext<CommandSourceStack> ctx, BlockPos center, String rawRot) {
		try {
			return executeInstall(ctx, center, SanctuaryManifest.parseRotation(rawRot));
		} catch (IllegalArgumentException ex) {
			ctx.getSource().sendFailure(Component.literal("[Canopy Sanctuary] " + ex.getMessage()));
			return 0;
		}
	}

	private static int executeInstall(CommandContext<CommandSourceStack> ctx, BlockPos center, Rotation rotation) {
		CommandSourceStack source = ctx.getSource();
		if (!verifyPermissionServerSide(source)) {
			return 0;
		}
		SanctuaryPlacementService.InstallStartResult result = SanctuaryPlacementService.startInstall(
			source.getServer(),
			source.getLevel(),
			center,
			rotation,
			true,
			source.getTextName()
		);
		if (!result.started()) {
			source.sendFailure(Component.literal("[Canopy Sanctuary] " + result.message()));
			return 0;
		}
		source.sendSuccess(() -> Component.literal("[Canopy Sanctuary] " + result.message()), true);
		return 1;
	}

	private static int executeSetSpawn(CommandContext<CommandSourceStack> ctx) {
		CommandSourceStack source = ctx.getSource();
		if (!verifyPermissionServerSide(source)) {
			return 0;
		}
		SanctuaryPlacementService.SetSpawnResult result = SanctuaryPlacementService.setWorldSpawnToSanctuary(source.getServer());
		if (!result.success()) {
			source.sendFailure(Component.literal("[Canopy Sanctuary] " + result.message()));
			return 0;
		}
		source.sendSuccess(() -> Component.literal("[Canopy Sanctuary] " + result.message()), true);
		return 1;
	}

	private static int executeProtection(CommandContext<CommandSourceStack> ctx, boolean enabled) {
		CommandSourceStack source = ctx.getSource();
		if (!verifyPermissionServerSide(source)) {
			return 0;
		}
		SanctuarySavedState state = SanctuarySavedState.get(source.getServer());
		if (!state.isInstalled()) {
			source.sendFailure(Component.literal("[Canopy Sanctuary] Cannot toggle protection when Sanctuary is not installed."));
			return 0;
		}
		state.setProtectionEnabled(enabled);
		source.getServer().overworld().getDataStorage().saveAndJoin();
		source.sendSuccess(() -> Component.literal("[Canopy Sanctuary] Protection set to " + enabled + "."), true);
		return 1;
	}

	private static int executeResetFailed(CommandContext<CommandSourceStack> ctx) {
		CommandSourceStack source = ctx.getSource();
		if (!verifyPermissionServerSide(source)) {
			return 0;
		}
		SanctuarySavedState state = SanctuarySavedState.get(source.getServer());
		if (state.status() == SanctuarySavedState.InstallStatus.INSTALLED) {
			source.sendFailure(Component.literal("[Canopy Sanctuary] Refusing reset: Sanctuary is already cleanly installed."));
			return 0;
		}
		if (state.status() == SanctuarySavedState.InstallStatus.NONE) {
			source.sendSuccess(() -> Component.literal("[Canopy Sanctuary] State is already NONE."), false);
			return 1;
		}
		state.resetInterruptedOrFailedState();
		source.getServer().overworld().getDataStorage().saveAndJoin();
		source.sendSuccess(() -> Component.literal("[Canopy Sanctuary] Reset interrupted/failed install marker. Verify world backup before retrying."), true);
		return 1;
	}

	private static BlockPos defaultCenter(CommandSourceStack source) {
		ServerLevel level = source.getLevel();
		var pos = source.getPosition();
		boolean hasExplicitExecPos = source.getEntity() != null || pos.lengthSqr() > 1.0e-4;
		BlockPos raw = hasExplicitExecPos ? BlockPos.containing(pos) : level.getRespawnData().pos();
		level.getChunk(SectionPos.blockToSectionCoord(raw.getX()), SectionPos.blockToSectionCoord(raw.getZ()));
		int surfaceY = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, raw.getX(), raw.getZ()) - 1;
		return new BlockPos(raw.getX(), Math.max(level.getMinY() + 36, surfaceY), raw.getZ());
	}

	private static void sendReport(CommandSourceStack source, String label, SanctuaryPreflightValidator.PreflightReport report) {
		var m = report.terrainMetrics();
		String header = "[Canopy Sanctuary] " + label + " at " + report.requestedCenter().toShortString()
			+ " (rot=" + report.rotation().name() + ") => " + (report.passed() ? "PASS" : "FAIL")
			+ " | relief=" + m.relief() + " (Y " + m.minCoreY() + ".." + m.maxCoreY() + ", med " + m.medianCoreY() + ")"
			+ ", liquids=" + m.liquidHits() + ", nonNatural=" + m.nonNaturalHits()
			+ ", blockEntities=" + m.blockEntityHits() + ", structures=" + m.structureOverlapHits();
		if (report.passed()) {
			source.sendSuccess(() -> Component.literal(header), false);
		} else {
			source.sendFailure(Component.literal(header));
			for (SanctuaryPreflightValidator.CheckResult check : report.failures()) {
				source.sendFailure(Component.literal(" - [FAIL " + check.code() + "] " + check.detail()));
			}
		}
	}
}
