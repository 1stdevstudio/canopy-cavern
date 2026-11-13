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

		Map<String, Integer> complete = new java.util.HashMap<>();
		for (var material : camp.materials()) {
			complete.put(material.itemId(), material.count());
		}
		assertTrue(ShelterBlueprints.hasAllMaterials(complete, camp.materials()));
		assertTrue(ShelterBlueprints.missingMaterials(complete, camp.materials()).isEmpty());

		Map<String, Integer> partial = new java.util.HashMap<>(complete);
		partial.put("minecraft:spruce_planks", complete.get("minecraft:spruce_planks") - 8);
		partial.remove("minecraft:lantern");
		assertFalse(ShelterBlueprints.hasAllMaterials(partial, camp.materials()));
		Map<String, Integer> missing = ShelterBlueprints.missingMaterials(partial, camp.materials());
		assertEquals(8, missing.get("minecraft:spruce_planks"));
		assertEquals(1, missing.get("minecraft:lantern"));
	}

	@Test
	void materialCostsMatchFinalBlockPlacementsForEveryBlueprint() {
		for (BlueprintDefinition bp : ShelterBlueprints.allBlueprints()) {
			Map<String, String> finalBlocks = new java.util.HashMap<>();
			for (var spec : bp.blocks()) {
				finalBlocks.put(spec.dx() + ":" + spec.dy() + ":" + spec.dz(), spec.blockId());
			}
			Map<String, Integer> expected = new java.util.HashMap<>();
			for (String blockId : finalBlocks.values()) {
				if (!"minecraft:air".equals(blockId)) {
					expected.merge(blockId, 1, Integer::sum);
				}
			}
			Map<String, Integer> actual = new java.util.HashMap<>();
			for (var cost : bp.materials()) {
				actual.merge(cost.itemId(), cost.count(), Integer::sum);
			}
			assertEquals(expected, actual, "Material mismatch for " + bp.id());
		}
		assertTrue(ShelterBlueprints.findBlueprint("peak_stone_cabin").blocks().stream()
			.anyMatch(b -> b.blockId().equals("minecraft:spruce_door")));
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
