package com.yogi.canopycavern.worldgen;

import com.yogi.canopycavern.CanopyCavernMod;
import terrablender.api.MaterialRuleManager;
import terrablender.api.Regions;
import terrablender.api.TerraBlenderApi;

/**
 * TerraBlender entrypoint registering Canopy Cavern's Overworld biome region
 * and surface material rules.
 */
public final class CanopyTerraBlender implements TerraBlenderApi {
	public static final int OVERWORLD_REGION_WEIGHT = 7;

	@Override
	public void onTerraBlenderInitialized() {
		Regions.register(new CanopyOverworldRegion(CanopyCavernMod.id("overworld"), OVERWORLD_REGION_WEIGHT));
		MaterialRuleManager.addRules(
			MaterialRuleManager.RuleCategory.OVERWORLD,
			CanopyCavernMod.MOD_ID,
			CanopyMaterialRules::makeRules
		);
		CanopyCavernMod.LOGGER.info(
			"Registered TerraBlender Overworld region ({} biomes, weight={})",
			ModBiomes.ALL_BIOMES.size(),
			OVERWORLD_REGION_WEIGHT
		);
	}
}
