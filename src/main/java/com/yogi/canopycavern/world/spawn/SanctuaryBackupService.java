package com.yogi.canopycavern.world.spawn;

import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.storage.LevelResource;
import org.slf4j.Logger;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.DigestOutputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HexFormat;
import java.util.List;
import java.util.stream.Stream;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

/**
 * Creates verified pre-modification world backups before Canopy Sanctuary writes blocks into an existing world.
 */
public final class SanctuaryBackupService {
	private static final DateTimeFormatter TS_FORMAT = DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss");
	private static final int BUFFER_SIZE = 16 * 1024;

	private SanctuaryBackupService() {
	}

	public record BackupResult(boolean success, String token, Path backupFile, long bytesWritten, String errorMessage) {
	}

	/** Flushes server state and archives the world directory into {@code <world>/backups/}. */
	public static BackupResult createVerifiedBackup(MinecraftServer server, Logger logger) {
		Path worldRoot = server.getWorldPath(LevelResource.ROOT).toAbsolutePath().normalize();
		Path backupDir = worldRoot.resolve("backups");
		try {
			server.saveEverything(false, true, false);
			server.overworld().getDataStorage().saveAndJoin();
			BackupResult result = createArchiveFromDirectory(worldRoot, backupDir);
			if (result.success()) {
				SanctuarySavedState state = SanctuarySavedState.get(server);
				state.recordBackup(result.token(), result.backupFile().toAbsolutePath().toString());
				server.overworld().getDataStorage().saveAndJoin();
				logger.info(
					"Created Canopy Sanctuary pre-install backup {} ({} bytes, token={})",
					result.backupFile(),
					result.bytesWritten(),
					result.token()
				);
			}
			return result;
		} catch (Exception ex) {
			logger.error("Failed creating Canopy Sanctuary world backup", ex);
			return new BackupResult(false, "", backupDir, 0L, ex.getMessage());
		}
	}

	/** Archives {@code sourceRoot} into {@code backupDir/canopy-sanctuary-<ts>.zip}, skipping {@code backups/} and lock files. */
	public static BackupResult createArchiveFromDirectory(Path sourceRoot, Path backupDir) throws IOException {
		Files.createDirectories(backupDir);
		String timestamp = TS_FORMAT.format(ZonedDateTime.now(ZoneOffset.UTC));
		Path zipPath = backupDir.resolve("canopy-sanctuary-" + timestamp + ".zip");

		MessageDigest digest;
		try {
			digest = MessageDigest.getInstance("SHA-256");
		} catch (NoSuchAlgorithmException ex) {
			throw new IllegalStateException("SHA-256 unavailable", ex);
		}

		try (
			OutputStream rawOut = Files.newOutputStream(zipPath);
			DigestOutputStream digestOut = new DigestOutputStream(rawOut, digest);
			ZipOutputStream zipOut = new ZipOutputStream(digestOut)
		) {
			List<Path> files;
			try (Stream<Path> walk = Files.walk(sourceRoot)) {
				files = walk
					.filter(Files::isRegularFile)
					.filter(path -> !path.normalize().startsWith(backupDir.normalize()))
					.filter(path -> !"session.lock".equals(path.getFileName().toString()))
					.sorted()
					.toList();
			}

			byte[] buffer = new byte[BUFFER_SIZE];
			for (Path file : files) {
				String entryName = sourceRoot.relativize(file).toString().replace('\\', '/');
				zipOut.putNextEntry(new ZipEntry(entryName));
				try (InputStream in = Files.newInputStream(file)) {
					int read;
					while ((read = in.read(buffer)) >= 0) {
						zipOut.write(buffer, 0, read);
					}
				} catch (IOException unreadable) {
					// If an active file vanishes mid-backup, fail closed rather than storing a partial archive.
					throw new IOException("Unable to read world file during backup: " + entryName, unreadable);
				}
				zipOut.closeEntry();
			}
		}

		long size = Files.size(zipPath);
		if (size <= 0L) {
			return new BackupResult(false, "", zipPath, 0L, "Backup archive is empty");
		}
		String hex = HexFormat.of().formatHex(digest.digest()).substring(0, 12);
		String token = "bkp-" + timestamp + "-" + hex;
		return new BackupResult(true, token, zipPath, size, "");
	}

	/** Verifies that recorded backup metadata points to an existing non-empty ZIP archive. */
	public static boolean hasVerifiedBackup(SanctuarySavedState state) {
		if (state == null) {
			return false;
		}
		return isBackupFileValid(state.backupToken(), state.backupPath());
	}

	public static boolean isBackupFileValid(String token, String rawPath) {
		if (token == null || token.isBlank() || rawPath == null || rawPath.isBlank()) {
			return false;
		}
		try {
			Path path = Path.of(rawPath);
			return Files.isRegularFile(path) && Files.size(path) > 0L;
		} catch (Exception ex) {
			return false;
		}
	}
}
