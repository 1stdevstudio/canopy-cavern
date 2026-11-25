package com.yogi.canopycavern.core;

import net.minecraft.core.BlockPos;
import org.junit.jupiter.api.Test;

import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

class SurvivalItemsTest {
	/** Regression: an invalid crafting category ("tools") made the whole datapack fail to load. */
	@Test
	void craftingRecipesUseValidBookCategories() throws Exception {
		var valid = Set.of("building", "redstone", "equipment", "misc");
		try (var files = java.nio.file.Files.list(java.nio.file.Path.of("src/main/resources/data/canopycavern/recipe"))) {
			for (var file : files.toList()) {
				var json = com.google.gson.JsonParser.parseString(java.nio.file.Files.readString(file)).getAsJsonObject();
				if (json.get("type").getAsString().startsWith("minecraft:crafting_") && json.has("category")) {
					assertTrue(valid.contains(json.get("category").getAsString()), file.getFileName() + " category");
				}
			}
		}
	}

	@Test
	void vineStopsAtFloorWallGapAndMaxLength() {
		BlockPos start = new BlockPos(0, 10, 0);
		assertEquals(4, VineColumn.plan(start, 16, p -> p.getY() > 6, p -> true).size(), "stops at the floor");
		assertEquals(2, VineColumn.plan(start, 16, p -> true, p -> p.getY() > 8).size(), "stops where the wall ends");
		assertEquals(16, VineColumn.plan(start, 16, p -> true, p -> true).size(), "capped at 16");
		assertTrue(VineColumn.plan(start, 16, p -> false, p -> true).isEmpty());
		assertEquals(Set.of(start, start.below()), Set.copyOf(VineColumn.plan(start, 2, p -> true, p -> true)));
	}
}
