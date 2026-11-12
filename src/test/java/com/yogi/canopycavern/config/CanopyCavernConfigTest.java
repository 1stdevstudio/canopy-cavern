package com.yogi.canopycavern.config;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.slf4j.LoggerFactory;

import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class CanopyCavernConfigTest {

	@Test
	void createsAndReloadsDefaultConfig(@TempDir Path tempDir) {
		Path path = tempDir.resolve("canopycavern.json");
		var logger = LoggerFactory.getLogger(CanopyCavernConfigTest.class);

		CanopyCavernConfig created = CanopyCavernConfig.loadOrCreate(path, logger);
		assertTrue(Files.exists(path));
		assertEquals(CanopyCavernConfig.defaults(), created);

		CanopyCavernConfig toggled = created.withClientHudEnabled(false);
		CanopyCavernConfig.save(path, toggled, logger);

		CanopyCavernConfig reloaded = CanopyCavernConfig.loadOrCreate(path, logger);
		assertFalse(reloaded.clientHudEnabled());
		assertTrue(reloaded.caveOverhaulEnabled());
	}

	@Test
	void fallsBackToDefaultsOnCorruptedJson(@TempDir Path tempDir) throws Exception {
		Path path = tempDir.resolve("broken.json");
		Files.writeString(path, "{invalid json");
		var logger = LoggerFactory.getLogger(CanopyCavernConfigTest.class);

		CanopyCavernConfig loaded = CanopyCavernConfig.loadOrCreate(path, logger);
		assertEquals(CanopyCavernConfig.defaults(), loaded);
	}
}
