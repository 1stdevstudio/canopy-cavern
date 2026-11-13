package com.yogi.canopycavern;

import com.yogi.canopycavern.config.CanopyCavernConfig;
import com.yogi.canopycavern.entity.ModEntities;
import com.yogi.canopycavern.item.ModItems;
import com.yogi.canopycavern.item.ExpeditionGearActions;

import com.yogi.canopycavern.network.ModNetworking;
import com.yogi.canopycavern.world.PlayerClimateHandler;
import com.yogi.canopycavern.worldgen.WorldOverhaulRegistry;
import com.yogi.canopycavern.worldgen.MiningCityStructure;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.resources.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.file.Path;

/**
 * Main shared entrypoint for Canopy Cavern. Keeps world generation and configuration
 * isolated from client-only code so future dedicated-server support drops in cleanly.
 */
public final class CanopyCavernMod implements ModInitializer {
	public static final String MOD_ID = "canopycavern";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	private static CanopyCavernConfig config = CanopyCavernConfig.defaults();

	@Override
	public void onInitialize() {
		Path configPath = configPath();
		config = CanopyCavernConfig.loadOrCreate(configPath, LOGGER);
		ModItems.register();
		ExpeditionGearActions.register();

		ModEntities.register();
		ModNetworking.register();
		PlayerClimateHandler.register();
		WorldOverhaulRegistry.register(config);
		MiningCityStructure.register();

		LOGGER.info(
			"Canopy Cavern initialized (surfaceOverhaul={}, caveOverhaul={}, surfaceLavaCleanup={}, climateSurvival={})",
			config.surfaceOverhaulEnabled(),
			config.caveOverhaulEnabled(),
			config.removeAbstractSurfaceLava(),
			config.climateSurvivalEnabled()
		);
	}

	/** Returns the active configuration snapshot. */
	public static CanopyCavernConfig getConfig() {
		return config;
	}

	/** Updates and persists configuration on disk. */
	public static void updateConfig(CanopyCavernConfig updated) {
		config = updated;
		CanopyCavernConfig.save(configPath(), updated, LOGGER);
	}

	/** Creates a namespaced {@link Identifier} under this mod's ID. */
	public static Identifier id(String path) {
		return Identifier.fromNamespaceAndPath(MOD_ID, path);
	}

	private static Path configPath() {
		return FabricLoader.getInstance().getConfigDir().resolve(MOD_ID + ".json");
	}
}
