package com.yogi.canopycavern.world.spawn;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.yogi.canopycavern.config.CanopyCavernConfig;
import net.minecraft.core.BlockPos;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.NbtAccounter;
import net.minecraft.nbt.NbtIo;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.levelgen.structure.BoundingBox;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Stream;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Comprehensive verification suite for Canopy Sanctuary NBT templates, rotation geometry,
 * fail-closed preflight safety, backup archival, persistence/interruption handling,
 * protection & climate boundaries, server/client separation, and bilingual localization.
 */
class CanopySanctuarySuiteTest {

	private static final Set<String> FORBIDDEN_HAZARDS = Set.of(
		"minecraft:lava",
		"minecraft:flowing_lava",
		"minecraft:tnt",
		"minecraft:magma_block",
		"minecraft:fire",
		"minecraft:soul_fire",
		"minecraft:campfire",
		"minecraft:soul_campfire",
		"minecraft:command_block",
		"minecraft:repeating_command_block",
		"minecraft:chain_command_block",
		"minecraft:structure_block",
		"minecraft:jigsaw"
	);

	@Test
	void allTenTemplatesLoadAndTransformCleanlyAcrossAllRotations() throws Exception {
		SanctuaryManifest manifest = SanctuaryManifest.loadDefault();
		assertEquals("canopy_sanctuary", manifest.hubId());
		assertEquals(5023, manifest.dataVersion());
		assertEquals(10, manifest.pieces().size());

		// Also verify world-space non-overlap across all 4 rotations and validate arrival pad & sign/lectern bindings
		for (Rotation rotation : Rotation.values()) {
			Map<Long, String> occupiedWorld = new HashMap<>();

			for (SanctuaryManifest.PieceSpec piece : manifest.pieces()) {
				for (int axisSize : piece.size()) {
					assertTrue(axisSize >= 1 && axisSize <= 48, "Piece " + piece.id() + " exceeds 48-block modular limit: " + axisSize);
				}

				String resourcePath = "/data/canopycavern/structure/server_spawn/" + piece.id() + ".nbt";
				CompoundTag root;
				try (InputStream stream = CanopySanctuarySuiteTest.class.getResourceAsStream(resourcePath)) {
					assertNotNull(stream, "Missing structure NBT resource: " + resourcePath);
					root = NbtIo.readCompressed(stream, NbtAccounter.unlimitedHeap());
				}

				assertEquals(manifest.dataVersion(), root.getIntOr("DataVersion", 0), "Wrong DataVersion in " + piece.id());
				ListTag sizeTag = root.getListOrEmpty("size");
				assertEquals(3, sizeTag.size());
				assertEquals(piece.size()[0], sizeTag.getIntOr(0, 0));
				assertEquals(piece.size()[1], sizeTag.getIntOr(1, 0));
				assertEquals(piece.size()[2], sizeTag.getIntOr(2, 0));

				ListTag palette = root.getListOrEmpty("palette");
				assertFalse(palette.isEmpty(), "Empty palette in " + piece.id());
				List<String> paletteIds = new java.util.ArrayList<>(palette.size());
				for (int i = 0; i < palette.size(); i++) {
					CompoundTag entry = palette.getCompoundOrEmpty(i);
					String id = entry.getStringOr("Name", entry.getStringOr("id", ""));
					assertFalse(id.isBlank(), "Blank block ID in palette of " + piece.id());
					assertTrue(id.startsWith("minecraft:"), "Unexpected namespace in palette: " + id);
					assertFalse(FORBIDDEN_HAZARDS.contains(id), "Hazard block " + id + " found in " + piece.id());
					paletteIds.add(id);
				}

				ListTag blocks = root.getListOrEmpty("blocks");
				Map<BlockPos, String> localNonAir = new HashMap<>();
				for (int i = 0; i < blocks.size(); i++) {
					CompoundTag blockTag = blocks.getCompoundOrEmpty(i);
					ListTag posTag = blockTag.getListOrEmpty("pos");
					int lx = posTag.getIntOr(0, -1);
					int ly = posTag.getIntOr(1, -1);
					int lz = posTag.getIntOr(2, -1);
					int stateIdx = blockTag.getIntOr("state", -1);

					assertTrue(lx >= 0 && lx < piece.size()[0]);
					assertTrue(ly >= 0 && ly < piece.size()[1]);
					assertTrue(lz >= 0 && lz < piece.size()[2]);
					assertTrue(stateIdx >= 0 && stateIdx < paletteIds.size());

					String blockId = paletteIds.get(stateIdx);
					if (!"minecraft:air".equals(blockId)) {
						int hx = piece.offset()[0] + lx;
						int hy = piece.offset()[1] + ly;
						int hz = piece.offset()[2] + lz;
						localNonAir.put(new BlockPos(lx, ly, lz), blockId);

						BlockPos transformed = SanctuaryManifest.transformHubOffset(hx, hy, hz, rotation);
						String prev = occupiedWorld.put(transformed.asLong(), piece.id());
						assertTrue(
							prev == null,
							"Rotation " + rotation + " collision between " + prev + " and " + piece.id() + " at " + transformed
						);
					}
				}

				if (rotation == Rotation.NONE) {
					assertEquals(piece.nonAirBlocks(), localNonAir.size(), "Non-air count mismatch for " + piece.id());

					for (SanctuaryManifest.SignSpec sign : piece.signs()) {
						BlockPos local = new BlockPos(
							sign.offset()[0] - piece.offset()[0],
							sign.offset()[1] - piece.offset()[1],
							sign.offset()[2] - piece.offset()[2]
						);
						String placed = localNonAir.get(local);
						assertNotNull(placed, "Missing sign block at " + local + " in " + piece.id());
						assertTrue(placed.endsWith("_sign"), "Expected sign at " + local + " in " + piece.id() + ", found " + placed);
					}

					for (SanctuaryManifest.LecternSpec lectern : piece.lecterns()) {
						BlockPos local = new BlockPos(
							lectern.offset()[0] - piece.offset()[0],
							lectern.offset()[1] - piece.offset()[1],
							lectern.offset()[2] - piece.offset()[2]
						);
						assertEquals("minecraft:lectern", localNonAir.get(local), "Missing lectern at " + local + " in " + piece.id());
					}
				}
			}

			// Verify arrival coordinate sits safely on solid footing with unobstructed 4-block headroom in EVERY rotation
			BlockPos center = new BlockPos(100, 68, -200);
			BlockPos arrival = manifest.arrivalWorldPos(center, rotation);
			BlockPos arrivalRel = arrival.subtract(center);
			assertNotNull(occupiedWorld.get(arrivalRel.below().asLong()), "Missing arrival floor block in rotation " + rotation);
			for (int dy = 0; dy <= 3; dy++) {
				assertTrue(
					occupiedWorld.get(arrivalRel.above(dy).asLong()) == null,
					"Obstructed arrival headroom dy=" + dy + " in rotation " + rotation
				);
			}
		}
	}

	@Test
	void enUsAndIdIdHaveFullParityForAllSanctuaryKeysAndFieldGuide() throws Exception {
		JsonObject enUs = loadLang("/assets/canopycavern/lang/en_us.json");
		JsonObject idId = loadLang("/assets/canopycavern/lang/id_id.json");

		for (Map.Entry<String, String> entry : SanctuaryLocalization.allEnglishFallbacks().entrySet()) {
			String key = entry.getKey();
			assertTrue(enUs.has(key), "Missing key in en_us.json: " + key);
			assertTrue(idId.has(key), "Missing key in id_id.json: " + key);
			String enVal = enUs.get(key).getAsString();
			String idVal = idId.get(key).getAsString();
			assertFalse(enVal.isBlank(), "Blank en_us value for " + key);
			assertFalse(idVal.isBlank(), "Blank id_id value for " + key);
			if (key.startsWith("sign.canopycavern.")) {
				assertTrue(enVal.length() <= 16, "English sign text too long for wooden sign: '" + enVal + "'");
				assertTrue(idVal.length() <= 16, "Indonesian sign text too long for wooden sign: '" + idVal + "'");
			}
		}

		List<String> extraKeys = List.of(
			"message.canopycavern.sanctuary.protected",
			"guide.canopycavern.section.sanctuary_hub.title",
			"guide.canopycavern.section.sanctuary_hub.body",
			"guide.canopycavern.section.sanctuary_routes.title",
			"guide.canopycavern.section.sanctuary_routes.body",
			"guide.canopycavern.section.sanctuary_safety.title",
			"guide.canopycavern.section.sanctuary_safety.body",
			"guide.canopycavern.section.sanctuary_admin.title",
			"guide.canopycavern.section.sanctuary_admin.body"
		);
		for (String key : extraKeys) {
			assertTrue(enUs.has(key) && !enUs.get(key).getAsString().isBlank(), "Missing en_us key: " + key);
			assertTrue(idId.has(key) && !idId.get(key).getAsString().isBlank(), "Missing id_id key: " + key);
		}
	}

	@Test
	void serverSpawnPackageAndMixinsHaveZeroClientImports() throws Exception {
		Path spawnDir = Path.of("src/main/java/com/yogi/canopycavern/world/spawn");
		Path mixinDir = Path.of("src/main/java/com/yogi/canopycavern/mixin");
		try (Stream<Path> s1 = Files.list(spawnDir); Stream<Path> s2 = Files.list(mixinDir)) {
			List<Path> files = Stream.concat(s1, s2).filter(p -> p.toString().endsWith(".java")).toList();
			assertFalse(files.isEmpty());
			for (Path file : files) {
				String content = Files.readString(file, StandardCharsets.UTF_8);
				assertFalse(
					content.contains("net.minecraft.client"),
					"Dedicated-server incompatible client import found in " + file
				);
			}
		}
	}

	@Test
	void preflightRejectsDisabledConfigNonAdminNonOverworldMissingBackupAndDuplicates() {
		CanopyCavernConfig disabled = CanopyCavernConfig.defaults();
		CanopyCavernConfig enabled = disabled.withSpawnHubEnabled(true);
		SanctuarySavedState clean = new SanctuarySavedState();

		assertFalse(allPassed(SanctuaryPreflightValidator.validatePreconditions(disabled, clean, true, true, true, true)));
		assertFalse(allPassed(SanctuaryPreflightValidator.validatePreconditions(enabled, clean, false, true, true, true)));
		assertFalse(allPassed(SanctuaryPreflightValidator.validatePreconditions(enabled, clean, true, false, true, true)));
		assertFalse(allPassed(SanctuaryPreflightValidator.validatePreconditions(enabled, clean, true, true, false, true)));
		assertTrue(allPassed(SanctuaryPreflightValidator.validatePreconditions(enabled, clean, true, true, false, false)));

		SanctuarySavedState installed = new SanctuarySavedState();
		installed.markInstallStarted(1, "canopy_sanctuary", BlockPos.ZERO, Rotation.NONE, 48);
		installed.markInstallCompleted();
		assertFalse(allPassed(SanctuaryPreflightValidator.validatePreconditions(enabled, installed, true, true, true, true)));

		SanctuarySavedState interrupted = new SanctuarySavedState();
		interrupted.markInstallStarted(1, "canopy_sanctuary", BlockPos.ZERO, Rotation.NONE, 48);
		assertFalse(allPassed(SanctuaryPreflightValidator.validatePreconditions(enabled, interrupted, true, true, true, true)));

		assertTrue(allPassed(SanctuaryPreflightValidator.validatePreconditions(enabled, clean, true, true, true, true)));
	}

	@Test
	void preflightEvaluatesBordersReliefLiquidsOccupiedAndVillages() {
		SanctuaryManifest manifest = SanctuaryManifest.loadDefault();
		BlockPos center = new BlockPos(0, 70, 0);
		BoundingBox env = manifest.envelopeBoundingBoxWorld(center, Rotation.NONE);
		var safeTerrain = new SanctuaryPreflightValidator.TerrainMetrics(68, 74, 70, 0, 0, 0, 0);

		assertTrue(allPassed(SanctuaryPreflightValidator.evaluateTerrainMetrics(center, -64, 320, env, true, false, safeTerrain)));
		assertFalse(allPassed(SanctuaryPreflightValidator.evaluateTerrainMetrics(center, -64, 320, env, false, false, safeTerrain)));
		assertFalse(allPassed(SanctuaryPreflightValidator.evaluateTerrainMetrics(new BlockPos(0, -40, 0), -64, 320, manifest.envelopeBoundingBoxWorld(new BlockPos(0, -40, 0), Rotation.NONE), true, false, safeTerrain)));
		assertFalse(allPassed(SanctuaryPreflightValidator.evaluateTerrainMetrics(center, -64, 320, env, true, true, safeTerrain)));
		assertFalse(allPassed(SanctuaryPreflightValidator.evaluateTerrainMetrics(center, -64, 320, env, true, false, new SanctuaryPreflightValidator.TerrainMetrics(68, 74, 70, 2, 0, 0, 0))));
		assertFalse(allPassed(SanctuaryPreflightValidator.evaluateTerrainMetrics(center, -64, 320, env, true, false, new SanctuaryPreflightValidator.TerrainMetrics(50, 90, 70, 0, 0, 0, 0))));
		assertFalse(allPassed(SanctuaryPreflightValidator.evaluateTerrainMetrics(center, -64, 320, env, true, false, new SanctuaryPreflightValidator.TerrainMetrics(68, 74, 70, 0, 1, 0, 0))));
		assertFalse(allPassed(SanctuaryPreflightValidator.evaluateTerrainMetrics(center, -64, 320, env, true, false, new SanctuaryPreflightValidator.TerrainMetrics(68, 74, 70, 0, 0, 1, 0))));
		assertFalse(allPassed(SanctuaryPreflightValidator.evaluateTerrainMetrics(center, -64, 320, env, true, false, new SanctuaryPreflightValidator.TerrainMetrics(68, 74, 70, 0, 0, 0, 1))));
	}

	@Test
	void savedStateTracksInterruptionAndBackupValidation(@TempDir Path worldDir) throws Exception {
		Files.writeString(worldDir.resolve("level.dat"), "dummy-level");
		Files.writeString(worldDir.resolve("session.lock"), "locked");
		Files.createDirectories(worldDir.resolve("region"));
		Files.writeString(worldDir.resolve("region/r.0.0.mca"), "dummy-region");

		Path backupDir = worldDir.resolve("backups");
		var backup = SanctuaryBackupService.createArchiveFromDirectory(worldDir, backupDir);
		assertTrue(backup.success());
		assertTrue(backup.bytesWritten() > 0L);
		assertTrue(SanctuaryBackupService.isBackupFileValid(backup.token(), backup.backupFile().toString()));
		assertFalse(SanctuaryBackupService.isBackupFileValid("", backup.backupFile().toString()));
		assertFalse(SanctuaryBackupService.isBackupFileValid(backup.token(), worldDir.resolve("missing.zip").toString()));

		SanctuarySavedState state = new SanctuarySavedState();
		state.recordBackup(backup.token(), backup.backupFile().toString());
		assertTrue(SanctuaryBackupService.hasVerifiedBackup(state));

		state.markInstallStarted(1, "canopy_sanctuary", new BlockPos(10, 68, 10), Rotation.CLOCKWISE_90, 48);
		state.recordPiecePlaced("plaza_core");
		assertEquals(SanctuarySavedState.InstallStatus.IN_PROGRESS, state.status());
		assertEquals(List.of("plaza_core"), state.placedPieceIds());

		state.markInstallFailed("simulated crash");
		assertEquals(SanctuarySavedState.InstallStatus.FAILED, state.status());
		state.resetInterruptedOrFailedState();
		assertEquals(SanctuarySavedState.InstallStatus.NONE, state.status());

		state.markInstallStarted(1, "canopy_sanctuary", new BlockPos(10, 68, 10), Rotation.NONE, 48);
		state.markInstallCompleted();
		assertTrue(state.isInstalled());
		assertTrue(state.isProtectionActive());
		assertThrows(IllegalStateException.class, state::resetInterruptedOrFailedState);
	}

	@Test
	void protectionAndArrivalClimateSafeZoneBoundsWorkCorrectly() {
		SanctuaryManifest manifest = SanctuaryManifest.loadDefault();
		BlockPos center = new BlockPos(200, 72, -100);

		assertTrue(SpawnSanctuaryProtection.isProtectedCoordinate(center, center, Rotation.NONE, manifest, 8));
		assertTrue(SpawnSanctuaryProtection.isProtectedCoordinate(center.offset(35, 0, 0), center, Rotation.CLOCKWISE_90, manifest, 8));
		assertTrue(SpawnSanctuaryProtection.isProtectedCoordinate(center.offset(0, -24, 30), center, Rotation.NONE, manifest, 8));
		assertFalse(SpawnSanctuaryProtection.isProtectedCoordinate(center.offset(55, 0, 0), center, Rotation.NONE, manifest, 8));
		assertFalse(SpawnSanctuaryProtection.isProtectedCoordinate(center.offset(130, 0, 0), center, Rotation.NONE, manifest, 48));

		assertTrue(SpawnSanctuaryProtection.isWithinChebyshevClimateZone(center, center, 48));
		assertTrue(SpawnSanctuaryProtection.isWithinChebyshevClimateZone(center.offset(48, -28, -48), center, 48));
		assertFalse(SpawnSanctuaryProtection.isWithinChebyshevClimateZone(center.offset(49, 0, 0), center, 48));

		assertEquals(Rotation.CLOCKWISE_90, SanctuaryManifest.parseRotation("cw_90"));
		assertEquals(Rotation.COUNTERCLOCKWISE_90, SanctuaryManifest.parseRotation("ccw_90"));
		assertThrows(IllegalArgumentException.class, () -> SanctuaryManifest.parseRotation("diagonal_45"));

		List<BoundingBox> bands = SanctuaryManifest.sliceVerticalBands(new BoundingBox(0, -34, 0, 10, -3, 10), 8);
		assertEquals(4, bands.size());
		assertEquals(-34, bands.getFirst().minY());
		assertEquals(-3, bands.getLast().maxY());
	}

	private static boolean allPassed(List<SanctuaryPreflightValidator.CheckResult> checks) {
		return checks.stream().allMatch(SanctuaryPreflightValidator.CheckResult::passed);
	}

	private static JsonObject loadLang(String resourcePath) throws Exception {
		try (InputStream stream = CanopySanctuarySuiteTest.class.getResourceAsStream(resourcePath)) {
			assertNotNull(stream, "Missing language file: " + resourcePath);
			return JsonParser.parseReader(new InputStreamReader(stream, StandardCharsets.UTF_8)).getAsJsonObject();
		}
	}
}
