package com.yogi.canopycavern.worldgen;

import java.util.Map;

/**
 * Vanilla overworld biome -> Canopy biome, used to build the "Canopy" world preset.
 * The preset keeps vanilla's climate layout (so terrain, rivers and caves line up) but every
 * slot is filled with a Canopy Cavern biome. Phase 0 reuses the existing nine biomes as
 * stand-ins; later phases swap in dedicated ocean, river, desert, jungle... biomes here.
 */
public final class CanopyBiomeMap {
	private static final String GROVE = "canopycavern:elder_bough_grove";
	private static final String CANOPY = "canopycavern:mossy_canopy";
	private static final String STEPPE = "canopycavern:crystal_steppe";
	private static final String PEAKS = "canopycavern:whispering_peaks";
	private static final String FROST = "canopycavern:frostspire_crags";
	private static final String CLIFFS = "canopycavern:windcarved_cliffs";
	private static final String GROTTO = "canopycavern:verdant_grotto";
	private static final String AMBER = "canopycavern:amber_caverns";
	private static final String DEPTHS = "canopycavern:luminous_depths";

	public static final Map<String, String> VANILLA_TO_CANOPY = Map.ofEntries(
		// Water and coast (Phase 1); stony shore keeps Windcarved Cliffs
		Map.entry("minecraft:ocean", "canopycavern:temperate_sound"), Map.entry("minecraft:deep_ocean", "canopycavern:abyssal_trench"),
		Map.entry("minecraft:warm_ocean", "canopycavern:sunlit_shallows"), Map.entry("minecraft:lukewarm_ocean", "canopycavern:coral_drift"),
		Map.entry("minecraft:deep_lukewarm_ocean", "canopycavern:abyssal_trench"), Map.entry("minecraft:cold_ocean", "canopycavern:kelpwood_sea"),
		Map.entry("minecraft:deep_cold_ocean", "canopycavern:abyssal_trench"), Map.entry("minecraft:frozen_ocean", "canopycavern:floe_sea"),
		Map.entry("minecraft:deep_frozen_ocean", "canopycavern:floe_sea"), Map.entry("minecraft:river", "canopycavern:meandering_river"),
		Map.entry("minecraft:frozen_river", "canopycavern:frostbound_river"), Map.entry("minecraft:beach", "canopycavern:golden_strand"),
		Map.entry("minecraft:snowy_beach", "canopycavern:frostline_shore"), Map.entry("minecraft:stony_shore", CLIFFS),
		Map.entry("minecraft:mushroom_fields", "canopycavern:mycelium_isles"),
		// Lowlands
		Map.entry("minecraft:plains", "canopycavern:wildgrass_plains"), Map.entry("minecraft:sunflower_plains", STEPPE),
		Map.entry("minecraft:meadow", PEAKS), Map.entry("minecraft:savanna", "canopycavern:sunbaked_savanna"),
		Map.entry("minecraft:savanna_plateau", "canopycavern:sunbaked_savanna"), Map.entry("minecraft:windswept_savanna", "canopycavern:gale_savanna"),
		Map.entry("minecraft:desert", "canopycavern:dune_expanse"), Map.entry("minecraft:badlands", "canopycavern:rustrock_badlands"),
		Map.entry("minecraft:eroded_badlands", "canopycavern:rustrock_badlands"), Map.entry("minecraft:wooded_badlands", "canopycavern:rustrock_badlands"),
		// Forests and wetlands
		Map.entry("minecraft:forest", "canopycavern:oakhollow_woods"), Map.entry("minecraft:flower_forest", "canopycavern:bloomveil_forest"),
		Map.entry("minecraft:birch_forest", "canopycavern:silverbirch_glade"), Map.entry("minecraft:old_growth_birch_forest", "canopycavern:elder_bough_grove"),
		Map.entry("minecraft:cherry_grove", "canopycavern:blossom_terrace"), Map.entry("minecraft:dappled_forest", "canopycavern:dapplelight_wood"), Map.entry("minecraft:dark_forest", CANOPY),
		Map.entry("minecraft:pale_garden", "canopycavern:ashen_garden"), Map.entry("minecraft:taiga", "canopycavern:spruce_hollow"),
		Map.entry("minecraft:old_growth_pine_taiga", "canopycavern:giant_spruce_reach"), Map.entry("minecraft:old_growth_spruce_taiga", "canopycavern:giant_spruce_reach"),
		Map.entry("minecraft:jungle", "canopycavern:tanglewild_jungle"), Map.entry("minecraft:sparse_jungle", "canopycavern:tanglewild_jungle"),
		Map.entry("minecraft:bamboo_jungle", "canopycavern:bamboo_thicket"), Map.entry("minecraft:swamp", "canopycavern:bogwater_fen"),
		Map.entry("minecraft:mangrove_swamp", "canopycavern:mangrove_tangle"),
		// Cold and mountains
		Map.entry("minecraft:snowy_plains", "canopycavern:snowbound_tundra"), Map.entry("minecraft:ice_spikes", "canopycavern:rime_spires"),
		Map.entry("minecraft:snowy_taiga", "canopycavern:frostpine_taiga"), Map.entry("minecraft:grove", "canopycavern:hoarfrost_grove"),
		Map.entry("minecraft:snowy_slopes", "canopycavern:powder_slopes"), Map.entry("minecraft:frozen_peaks", "canopycavern:glacier_crown"),
		Map.entry("minecraft:jagged_peaks", "canopycavern:frostspire_crags"), Map.entry("minecraft:stony_peaks", "canopycavern:slatestone_peaks"),
		Map.entry("minecraft:windswept_hills", CLIFFS), Map.entry("minecraft:windswept_gravelly_hills", "canopycavern:gravel_barrens"),
		Map.entry("minecraft:windswept_forest", "canopycavern:windbent_forest"),
		// Caves
		Map.entry("minecraft:lush_caves", GROTTO), Map.entry("minecraft:dripstone_caves", AMBER),
		Map.entry("minecraft:deep_dark", "canopycavern:hushed_depths"), Map.entry("minecraft:sulfur_caves", "canopycavern:sulfur_hollows")
	);

	private CanopyBiomeMap() {
	}
}
