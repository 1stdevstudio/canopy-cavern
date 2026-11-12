package com.yogi.canopycavern.core;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Pure data catalog for player-triggered auto-shelter blueprints and equipment material verification.
 * Shared across server building validation, client Field Guide GUI, and unit tests.
 */
public final class ShelterBlueprints {

	public record MaterialCost(String itemId, int count) {
	}

	public record BlockSpec(int dx, int dy, int dz, String blockId) {
	}

	public record BlueprintDefinition(
		String id,
		String titleKey,
		String descKey,
		String iconItemId,
		int width,
		int height,
		int depth,
		List<MaterialCost> materials,
		List<BlockSpec> blocks
	) {}

	public record EquipmentEntry(
		String itemId,
		String titleKey,
		String categoryKey,
		List<MaterialCost> materials
	) {}

	private static final List<BlueprintDefinition> BLUEPRINTS = buildBlueprints();
	private static final List<EquipmentEntry> EQUIPMENT_CATALOG = buildEquipmentCatalog();

	private ShelterBlueprints() {
	}

	public static List<BlueprintDefinition> allBlueprints() {
		return BLUEPRINTS;
	}

	public static BlueprintDefinition findBlueprint(String id) {
		for (BlueprintDefinition blueprint : BLUEPRINTS) {
			if (blueprint.id().equals(id)) {
				return blueprint;
			}
		}
		return null;
	}

	public static List<EquipmentEntry> equipmentCatalog() {
		return EQUIPMENT_CATALOG;
	}

	/** Returns true when every required material count is met or exceeded in inventoryCounts. */
	public static boolean hasAllMaterials(Map<String, Integer> inventoryCounts, List<MaterialCost> costs) {
		for (MaterialCost cost : costs) {
			if (inventoryCounts.getOrDefault(cost.itemId(), 0) < cost.count()) {
				return false;
			}
		}
		return true;
	}

	/** Computes per-item missing counts (only entries with deficit > 0). */
	public static Map<String, Integer> missingMaterials(Map<String, Integer> inventoryCounts, List<MaterialCost> costs) {
		Map<String, Integer> missing = new LinkedHashMap<>();
		for (MaterialCost cost : costs) {
			int owned = inventoryCounts.getOrDefault(cost.itemId(), 0);
			if (owned < cost.count()) {
				missing.put(cost.itemId(), cost.count() - owned);
			}
		}
		return Collections.unmodifiableMap(missing);
	}

	private static List<BlueprintDefinition> buildBlueprints() {
		List<BlueprintDefinition> list = new ArrayList<>();
		list.add(createTrailsideCamp());
		list.add(createPeakStoneCabin());
		list.add(createGrottoSafeBunker());
		return List.copyOf(list);
	}

	private static BlueprintDefinition createTrailsideCamp() {
		List<BlockSpec> blocks = new ArrayList<>();
		// 5x4x5 open-front warm timber outpost ahead of player (dz 1..5, dx -2..2)
		for (int dx = -2; dx <= 2; dx++) {
			for (int dz = 1; dz <= 5; dz++) {
				blocks.add(new BlockSpec(dx, -1, dz, "minecraft:spruce_planks"));
			}
		}
		// Corner log pillars (3 tall) + sloped canopy slab roof
		for (int dx : new int[]{-2, 2}) {
			for (int dz : new int[]{1, 5}) {
				for (int dy = 0; dy <= 2; dy++) {
					blocks.add(new BlockSpec(dx, dy, dz, "minecraft:spruce_log"));
				}
			}
		}
		// Back & side half-walls + campfire hearth
		for (int dx = -1; dx <= 1; dx++) {
			blocks.add(new BlockSpec(dx, 0, 5, "minecraft:spruce_planks"));
			blocks.add(new BlockSpec(dx, 1, 5, dx == 0 ? "minecraft:glass_pane" : "minecraft:spruce_planks"));
			blocks.add(new BlockSpec(dx, 2, 5, "minecraft:spruce_planks"));
		}
		for (int dz = 2; dz <= 4; dz++) {
			blocks.add(new BlockSpec(-2, 0, dz, "minecraft:spruce_fence"));
			blocks.add(new BlockSpec(2, 0, dz, "minecraft:spruce_fence"));
		}
		for (int dx = -2; dx <= 2; dx++) {
			for (int dz = 1; dz <= 5; dz++) {
				blocks.add(new BlockSpec(dx, 3, dz, "minecraft:spruce_slab"));
			}
		}
		blocks.add(new BlockSpec(0, 0, 3, "minecraft:campfire"));
		blocks.add(new BlockSpec(-1, 0, 4, "minecraft:crafting_table"));
		blocks.add(new BlockSpec(1, 0, 4, "minecraft:chest"));
		blocks.add(new BlockSpec(0, 2, 2, "minecraft:lantern"));

		return new BlueprintDefinition(
			"trailside_camp",
			"blueprint.canopycavern.trailside_camp",
			"blueprint.canopycavern.trailside_camp.desc",
			"minecraft:campfire",
			5,
			4,
			5,
			List.of(
				new MaterialCost("minecraft:spruce_planks", 28),
				new MaterialCost("minecraft:spruce_log", 12),
				new MaterialCost("minecraft:campfire", 1),
				new MaterialCost("minecraft:crafting_table", 1),
				new MaterialCost("minecraft:chest", 1),
				new MaterialCost("minecraft:lantern", 1)
			),
			List.copyOf(blocks)
		);
	}

	private static BlueprintDefinition createPeakStoneCabin() {
		List<BlockSpec> blocks = new ArrayList<>();
		// 5x5x5 enclosed alpine cabin with stone walls, gable roof, bed & furnace
		for (int dx = -2; dx <= 2; dx++) {
			for (int dz = 1; dz <= 5; dz++) {
				blocks.add(new BlockSpec(dx, -1, dz, "minecraft:cobblestone"));
				if (Math.abs(dx) == 2 || dz == 1 || dz == 5) {
					for (int dy = 0; dy <= 2; dy++) {
						if (dx == 0 && dz == 1 && (dy == 0 || dy == 1)) {
							continue; // doorway space
						}
						if (dy == 1 && ((Math.abs(dx) == 2 && dz == 3) || (dx == 0 && dz == 5))) {
							blocks.add(new BlockSpec(dx, dy, dz, "minecraft:glass_pane"));
						} else {
							boolean corner = Math.abs(dx) == 2 && (dz == 1 || dz == 5);
							blocks.add(new BlockSpec(dx, dy, dz, corner ? "minecraft:spruce_log" : "minecraft:cobblestone"));
						}
					}
				} else {
					for (int dy = 0; dy <= 2; dy++) {
						blocks.add(new BlockSpec(dx, dy, dz, "minecraft:air"));
					}
				}
			}
		}
		// Gable roof (dy = 3 & 4)
		for (int dz = 1; dz <= 5; dz++) {
			for (int dx = -2; dx <= 2; dx++) {
				int roofY = Math.abs(dx) <= 1 ? 4 : 3;
				if (Math.abs(dx) == 2) {
					blocks.add(new BlockSpec(dx, 3, dz, "minecraft:spruce_planks"));
				} else if (Math.abs(dx) == 1) {
					blocks.add(new BlockSpec(dx, 3, dz, "minecraft:spruce_planks"));
					blocks.add(new BlockSpec(dx, 4, dz, "minecraft:spruce_slab"));
				} else {
					blocks.add(new BlockSpec(0, roofY, dz, "minecraft:spruce_planks"));
				}
			}
		}
		blocks.add(new BlockSpec(-1, 0, 4, "minecraft:furnace"));
		blocks.add(new BlockSpec(1, 0, 4, "minecraft:crafting_table"));
		blocks.add(new BlockSpec(0, 0, 4, "minecraft:campfire"));
		blocks.add(new BlockSpec(1, 0, 2, "minecraft:chest"));
		blocks.add(new BlockSpec(0, 2, 3, "minecraft:lantern"));

		return new BlueprintDefinition(
			"peak_stone_cabin",
			"blueprint.canopycavern.peak_stone_cabin",
			"blueprint.canopycavern.peak_stone_cabin.desc",
			"minecraft:cobblestone",
			5,
			5,
			5,
			List.of(
				new MaterialCost("minecraft:cobblestone", 36),
				new MaterialCost("minecraft:spruce_planks", 24),
				new MaterialCost("minecraft:spruce_log", 12),
				new MaterialCost("minecraft:glass_pane", 3),
				new MaterialCost("minecraft:furnace", 1),
				new MaterialCost("minecraft:campfire", 1),
				new MaterialCost("minecraft:chest", 1),
				new MaterialCost("minecraft:lantern", 1)
			),
			List.copyOf(blocks)
		);
	}

	private static BlueprintDefinition createGrottoSafeBunker() {
		List<BlockSpec> blocks = new ArrayList<>();
		// 5x4x5 sealed deepslate & moss bunker for humid caves / deep seams
		for (int dx = -2; dx <= 2; dx++) {
			for (int dz = 1; dz <= 5; dz++) {
				blocks.add(new BlockSpec(dx, -1, dz, "minecraft:polished_deepslate"));
				boolean wall = Math.abs(dx) == 2 || dz == 1 || dz == 5;
				for (int dy = 0; dy <= 2; dy++) {
					if (dx == 0 && dz == 1 && (dy == 0 || dy == 1)) {
						blocks.add(new BlockSpec(dx, dy, dz, dy == 0 ? "minecraft:oak_door" : "minecraft:air"));
					} else if (wall) {
						boolean window = dy == 1 && ((Math.abs(dx) == 2 && dz == 3) || (dx == 0 && dz == 5));
						blocks.add(new BlockSpec(dx, dy, dz, window ? "minecraft:glass" : "minecraft:deepslate_bricks"));
					} else {
						blocks.add(new BlockSpec(dx, dy, dz, "minecraft:air"));
					}
				}
				blocks.add(new BlockSpec(dx, 3, dz, "minecraft:polished_deepslate"));
			}
		}
		blocks.add(new BlockSpec(-1, 0, 4, "minecraft:crafting_table"));
		blocks.add(new BlockSpec(1, 0, 4, "minecraft:chest"));
		blocks.add(new BlockSpec(0, 0, 4, "minecraft:lantern"));
		blocks.add(new BlockSpec(-1, 0, 2, "minecraft:moss_block"));
		blocks.add(new BlockSpec(1, 0, 2, "minecraft:amethyst_block"));

		return new BlueprintDefinition(
			"grotto_safe_bunker",
			"blueprint.canopycavern.grotto_safe_bunker",
			"blueprint.canopycavern.grotto_safe_bunker.desc",
			"minecraft:deepslate_bricks",
			5,
			4,
			5,
			List.of(
				new MaterialCost("minecraft:deepslate_bricks", 32),
				new MaterialCost("minecraft:polished_deepslate", 32),
				new MaterialCost("minecraft:glass", 3),
				new MaterialCost("minecraft:oak_door", 1),
				new MaterialCost("minecraft:moss_block", 1),
				new MaterialCost("minecraft:amethyst_block", 1),
				new MaterialCost("minecraft:crafting_table", 1),
				new MaterialCost("minecraft:chest", 1),
				new MaterialCost("minecraft:lantern", 1)
			),
			List.copyOf(blocks)
		);
	}

	private static List<EquipmentEntry> buildEquipmentCatalog() {
		return List.of(
			new EquipmentEntry("canopycavern:thermal_hood", "item.canopycavern.thermal_hood", "guide.cat.thermal",
				List.of(new MaterialCost("minecraft:white_wool", 3), new MaterialCost("minecraft:leather", 2))),
			new EquipmentEntry("canopycavern:thermal_parka", "item.canopycavern.thermal_parka", "guide.cat.thermal",
				List.of(new MaterialCost("minecraft:white_wool", 4), new MaterialCost("minecraft:leather", 3), new MaterialCost("minecraft:iron_ingot", 1))),
			new EquipmentEntry("canopycavern:thermal_leggings", "item.canopycavern.thermal_leggings", "guide.cat.thermal",
				List.of(new MaterialCost("minecraft:white_wool", 4), new MaterialCost("minecraft:leather", 3))),
			new EquipmentEntry("canopycavern:thermal_boots", "item.canopycavern.thermal_boots", "guide.cat.thermal",
				List.of(new MaterialCost("minecraft:white_wool", 2), new MaterialCost("minecraft:leather", 2))),
			new EquipmentEntry("canopycavern:mossweave_cap", "item.canopycavern.mossweave_cap", "guide.cat.mossweave",
				List.of(new MaterialCost("minecraft:moss_block", 3), new MaterialCost("minecraft:leather", 2))),
			new EquipmentEntry("canopycavern:mossweave_tunic", "item.canopycavern.mossweave_tunic", "guide.cat.mossweave",
				List.of(new MaterialCost("minecraft:moss_block", 4), new MaterialCost("minecraft:leather", 3), new MaterialCost("minecraft:amethyst_shard", 1))),
			new EquipmentEntry("canopycavern:mossweave_trousers", "item.canopycavern.mossweave_trousers", "guide.cat.mossweave",
				List.of(new MaterialCost("minecraft:moss_block", 4), new MaterialCost("minecraft:leather", 3))),
			new EquipmentEntry("canopycavern:mossweave_boots", "item.canopycavern.mossweave_boots", "guide.cat.mossweave",
				List.of(new MaterialCost("minecraft:moss_block", 2), new MaterialCost("minecraft:leather", 2))),
			new EquipmentEntry("canopycavern:grotto_crystal_pickaxe", "item.canopycavern.grotto_crystal_pickaxe", "guide.cat.tools",
				List.of(new MaterialCost("minecraft:amethyst_shard", 3), new MaterialCost("minecraft:stick", 2))),
			new EquipmentEntry("canopycavern:alpine_climbing_pick", "item.canopycavern.alpine_climbing_pick", "guide.cat.tools",
				List.of(new MaterialCost("minecraft:iron_ingot", 2), new MaterialCost("minecraft:stick", 2), new MaterialCost("minecraft:leather", 1))),
			new EquipmentEntry("canopycavern:flare_torch", "item.canopycavern.flare_torch", "guide.cat.tools",
				List.of(new MaterialCost("minecraft:torch", 2), new MaterialCost("minecraft:glowstone_dust", 1))),
			new EquipmentEntry("canopycavern:glow_lantern", "item.canopycavern.glow_lantern", "guide.cat.tools",
				List.of(new MaterialCost("minecraft:lantern", 1), new MaterialCost("minecraft:glow_berries", 2), new MaterialCost("minecraft:amethyst_shard", 1))),
			new EquipmentEntry("canopycavern:grotto_relic_compass", "item.canopycavern.grotto_relic_compass", "guide.cat.tools",
				List.of(new MaterialCost("minecraft:compass", 1), new MaterialCost("minecraft:amethyst_shard", 2), new MaterialCost("minecraft:glow_berries", 1))),
			new EquipmentEntry("canopycavern:canopy_field_guide", "item.canopycavern.canopy_field_guide", "guide.cat.tools",
				List.of(new MaterialCost("minecraft:book", 1), new MaterialCost("minecraft:moss_block", 1)))
		);
	}
}
