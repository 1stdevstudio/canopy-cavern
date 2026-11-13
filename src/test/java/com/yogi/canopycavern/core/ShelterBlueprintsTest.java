package com.yogi.canopycavern.core;

import com.yogi.canopycavern.core.ShelterBlueprints.BlueprintDefinition;
import com.yogi.canopycavern.core.ShelterBlueprints.EquipmentEntry;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ShelterBlueprintsTest {

	@Test
	void verifiesInventoryRequirementsAndDeficitsCleanly() {
		BlueprintDefinition camp = ShelterBlueprints.findBlueprint("trailside_camp");
		assertNotNull(camp);

		Map<String, Integer> partial = Map.of(
			"minecraft:spruce_planks", 20,
			"minecraft:spruce_log", 12,
			"minecraft:campfire", 1,
			"minecraft:crafting_table", 1,
			"minecraft:chest", 1
		);
		assertFalse(ShelterBlueprints.hasAllMaterials(partial, camp.materials()));
		Map<String, Integer> missing = ShelterBlueprints.missingMaterials(partial, camp.materials());
		assertEquals(8, missing.get("minecraft:spruce_planks"));
		assertEquals(1, missing.get("minecraft:lantern"));

		Map<String, Integer> complete = Map.of(
			"minecraft:spruce_planks", 32,
			"minecraft:spruce_log", 12,
			"minecraft:campfire", 1,
			"minecraft:crafting_table", 1,
			"minecraft:chest", 1,
			"minecraft:lantern", 1
		);
		assertTrue(ShelterBlueprints.hasAllMaterials(complete, camp.materials()));
		assertTrue(ShelterBlueprints.missingMaterials(complete, camp.materials()).isEmpty());
	}

	@Test
	void includesAbyssalAirlockDomeAndEquipmentCatalogEntriesForAllModGear() {
		assertEquals(4, ShelterBlueprints.allBlueprints().size());
		BlueprintDefinition airlock = ShelterBlueprints.findBlueprint("abyssal_airlock_dome");
		assertNotNull(airlock);
		assertEquals("blueprint.canopycavern.abyssal_airlock_dome", airlock.titleKey());
		assertFalse(airlock.materials().isEmpty());
		assertFalse(airlock.blocks().isEmpty());
		assertTrue(airlock.materials().stream().anyMatch(m -> m.itemId().equals("minecraft:glass")));
		assertTrue(airlock.materials().stream().anyMatch(m -> m.itemId().equals("minecraft:cut_copper")));

		assertEquals(16, ShelterBlueprints.equipmentCatalog().size());
		for (EquipmentEntry entry : ShelterBlueprints.equipmentCatalog()) {
			assertFalse(entry.materials().isEmpty(), "Missing materials for " + entry.itemId());
		}
		assertNotNull(ShelterBlueprints.equipmentCatalog().stream()
			.filter(e -> e.itemId().equals("canopycavern:abyssal_tide_compass"))
			.findFirst().orElse(null));
		assertNotNull(ShelterBlueprints.equipmentCatalog().stream()
			.filter(e -> e.itemId().equals("canopycavern:sea_glass_charm"))
			.findFirst().orElse(null));
	}
}
