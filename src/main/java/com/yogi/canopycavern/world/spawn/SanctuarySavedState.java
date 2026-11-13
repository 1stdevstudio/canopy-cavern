package com.yogi.canopycavern.world.spawn;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.util.datafix.DataFixTypes;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.saveddata.SavedDataType;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Persistent Overworld SavedData tracking Canopy Sanctuary installation state, backup verification,
 * orientation, placed modules (for crash/interruption recovery), and active spawn protection.
 */
public final class SanctuarySavedState extends SavedData {
	public static final Identifier DATA_ID = Identifier.fromNamespaceAndPath("canopycavern", "canopy_sanctuary_state");

	public enum InstallStatus {
		NONE,
		IN_PROGRESS,
		INSTALLED,
		FAILED;

		public static final Codec<InstallStatus> CODEC = Codec.STRING.xmap(
			name -> {
				try {
					return InstallStatus.valueOf(name);
				} catch (IllegalArgumentException ex) {
					return NONE;
				}
			},
			InstallStatus::name
		);
	}

	private InstallStatus status;
	private int schemaVersion;
	private String hubId;
	private String dimension;
	private BlockPos center;
	private Rotation rotation;
	private int safeZoneRadius;
	private boolean protectionEnabled;
	private boolean worldSpawnUpdated;
	private String backupToken;
	private String backupPath;
	private final List<String> placedPieceIds;
	private String lastError;
	private long updatedEpochSeconds;

	public static final Codec<SanctuarySavedState> CODEC = RecordCodecBuilder.create(instance ->
		instance.group(
			InstallStatus.CODEC.fieldOf("status").forGetter(SanctuarySavedState::status),
			Codec.INT.fieldOf("schemaVersion").forGetter(SanctuarySavedState::schemaVersion),
			Codec.STRING.fieldOf("hubId").forGetter(SanctuarySavedState::hubId),
			Codec.STRING.fieldOf("dimension").forGetter(SanctuarySavedState::dimension),
			BlockPos.CODEC.fieldOf("center").forGetter(SanctuarySavedState::center),
			Rotation.CODEC.fieldOf("rotation").forGetter(SanctuarySavedState::rotation),
			Codec.INT.fieldOf("safeZoneRadius").forGetter(SanctuarySavedState::safeZoneRadius),
			Codec.BOOL.fieldOf("protectionEnabled").forGetter(SanctuarySavedState::protectionEnabled),
			Codec.BOOL.fieldOf("worldSpawnUpdated").forGetter(SanctuarySavedState::worldSpawnUpdated),
			Codec.STRING.fieldOf("backupToken").forGetter(SanctuarySavedState::backupToken),
			Codec.STRING.fieldOf("backupPath").forGetter(SanctuarySavedState::backupPath),
			Codec.STRING.listOf().fieldOf("placedPieceIds").forGetter(SanctuarySavedState::placedPieceIds),
			Codec.STRING.fieldOf("lastError").forGetter(SanctuarySavedState::lastError),
			Codec.LONG.fieldOf("updatedEpochSeconds").forGetter(SanctuarySavedState::updatedEpochSeconds)
		).apply(instance, SanctuarySavedState::new)
	);

	public static final SavedDataType<SanctuarySavedState> TYPE = new SavedDataType<>(
		DATA_ID,
		SanctuarySavedState::new,
		CODEC,
		DataFixTypes.SAVED_DATA_COMMAND_STORAGE
	);

	public SanctuarySavedState() {
		this(
			InstallStatus.NONE,
			1,
			"canopy_sanctuary",
			"minecraft:overworld",
			BlockPos.ZERO,
			Rotation.NONE,
			48,
			false,
			false,
			"",
			"",
			List.of(),
			"",
			0L
		);
	}

	public SanctuarySavedState(
		InstallStatus status,
		int schemaVersion,
		String hubId,
		String dimension,
		BlockPos center,
		Rotation rotation,
		int safeZoneRadius,
		boolean protectionEnabled,
		boolean worldSpawnUpdated,
		String backupToken,
		String backupPath,
		List<String> placedPieceIds,
		String lastError,
		long updatedEpochSeconds
	) {
		this.status = status == null ? InstallStatus.NONE : status;
		this.schemaVersion = schemaVersion;
		this.hubId = hubId == null ? "canopy_sanctuary" : hubId;
		this.dimension = dimension == null ? "minecraft:overworld" : dimension;
		this.center = center == null ? BlockPos.ZERO : center;
		this.rotation = rotation == null ? Rotation.NONE : rotation;
		this.safeZoneRadius = safeZoneRadius <= 0 ? 48 : safeZoneRadius;
		this.protectionEnabled = protectionEnabled;
		this.worldSpawnUpdated = worldSpawnUpdated;
		this.backupToken = backupToken == null ? "" : backupToken;
		this.backupPath = backupPath == null ? "" : backupPath;
		this.placedPieceIds = new ArrayList<>(placedPieceIds == null ? List.of() : placedPieceIds);
		this.lastError = lastError == null ? "" : lastError;
		this.updatedEpochSeconds = updatedEpochSeconds;
	}

	/** Retrieves (without mutating chunks) or initializes the Overworld Sanctuary state. */
	public static SanctuarySavedState get(MinecraftServer server) {
		return server.overworld().getDataStorage().computeIfAbsent(TYPE);
	}

	public InstallStatus status() {
		return status;
	}

	public int schemaVersion() {
		return schemaVersion;
	}

	public String hubId() {
		return hubId;
	}

	public String dimension() {
		return dimension;
	}

	public BlockPos center() {
		return center;
	}

	public Rotation rotation() {
		return rotation;
	}

	public int safeZoneRadius() {
		return safeZoneRadius;
	}

	public boolean protectionEnabled() {
		return protectionEnabled;
	}

	public boolean worldSpawnUpdated() {
		return worldSpawnUpdated;
	}

	public String backupToken() {
		return backupToken;
	}

	public String backupPath() {
		return backupPath;
	}

	public List<String> placedPieceIds() {
		return Collections.unmodifiableList(placedPieceIds);
	}

	public String lastError() {
		return lastError;
	}

	public long updatedEpochSeconds() {
		return updatedEpochSeconds;
	}

	public boolean isInstalled() {
		return status == InstallStatus.INSTALLED;
	}

	public boolean isProtectionActive() {
		return status == InstallStatus.INSTALLED && protectionEnabled;
	}

	public void recordBackup(String token, String path) {
		this.backupToken = token == null ? "" : token;
		this.backupPath = path == null ? "" : path;
		this.updatedEpochSeconds = Instant.now().getEpochSecond();
		setDirty();
	}

	public void markInstallStarted(int schemaVersion, String hubId, BlockPos center, Rotation rotation, int safeZoneRadius) {
		this.status = InstallStatus.IN_PROGRESS;
		this.schemaVersion = schemaVersion;
		this.hubId = hubId;
		this.dimension = "minecraft:overworld";
		this.center = center.immutable();
		this.rotation = rotation;
		this.safeZoneRadius = safeZoneRadius;
		this.protectionEnabled = false;
		this.worldSpawnUpdated = false;
		this.placedPieceIds.clear();
		this.lastError = "";
		this.updatedEpochSeconds = Instant.now().getEpochSecond();
		setDirty();
	}

	public void recordPiecePlaced(String pieceId) {
		if (!this.placedPieceIds.contains(pieceId)) {
			this.placedPieceIds.add(pieceId);
		}
		this.updatedEpochSeconds = Instant.now().getEpochSecond();
		setDirty();
	}

	public void markInstallCompleted() {
		this.status = InstallStatus.INSTALLED;
		this.protectionEnabled = true;
		this.lastError = "";
		this.updatedEpochSeconds = Instant.now().getEpochSecond();
		setDirty();
	}

	public void markInstallFailed(String reason) {
		this.status = InstallStatus.FAILED;
		this.protectionEnabled = false;
		this.lastError = reason == null ? "Unknown placement error" : reason;
		this.updatedEpochSeconds = Instant.now().getEpochSecond();
		setDirty();
	}

	public void markWorldSpawnUpdated(boolean updated) {
		this.worldSpawnUpdated = updated;
		this.updatedEpochSeconds = Instant.now().getEpochSecond();
		setDirty();
	}

	public void setProtectionEnabled(boolean enabled) {
		this.protectionEnabled = enabled;
		this.updatedEpochSeconds = Instant.now().getEpochSecond();
		setDirty();
	}

	public void resetInterruptedOrFailedState() {
		if (this.status == InstallStatus.INSTALLED) {
			throw new IllegalStateException("Cannot reset a completed Canopy Sanctuary installation.");
		}
		this.status = InstallStatus.NONE;
		this.protectionEnabled = false;
		this.worldSpawnUpdated = false;
		this.placedPieceIds.clear();
		this.lastError = "";
		this.updatedEpochSeconds = Instant.now().getEpochSecond();
		setDirty();
	}
}
