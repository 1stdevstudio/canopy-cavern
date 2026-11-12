package com.yogi.canopycavern.config;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParseException;
import com.google.gson.JsonParser;
import org.slf4j.Logger;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Immutable configuration settings for Canopy Cavern world overhaul, climate survival, and client presentation.
 */
public record CanopyCavernConfig(
	boolean surfaceOverhaulEnabled,
	boolean caveOverhaulEnabled,
	boolean removeAbstractSurfaceLava,
	boolean clientHudEnabled,
	boolean clientAtmosphereParticlesEnabled,
	boolean useCelsius,
	boolean climateSurvivalEnabled,
	boolean starterFieldGuideEnabled,
	boolean dynamicAmbienceEnabled
) {
	private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();

	/** Backwards-compatible 6-flag constructor defaulting v0.3.0 additions to enabled. */
	public CanopyCavernConfig(
		boolean surfaceOverhaulEnabled,
		boolean caveOverhaulEnabled,
		boolean removeAbstractSurfaceLava,
		boolean clientHudEnabled,
		boolean clientAtmosphereParticlesEnabled,
		boolean useCelsius
	) {
		this(
			surfaceOverhaulEnabled,
			caveOverhaulEnabled,
			removeAbstractSurfaceLava,
			clientHudEnabled,
			clientAtmosphereParticlesEnabled,
			useCelsius,
			true,
			true,
			true
		);
	}

	/** Returns recommended default settings. */
	public static CanopyCavernConfig defaults() {
		return new CanopyCavernConfig(true, true, true, true, true, true, true, true, true);
	}

	/** Loads configuration from disk, creating defaults if missing or backfilling newly added v0.3.0 options. */
	public static CanopyCavernConfig loadOrCreate(Path configPath, Logger logger) {
		if (!Files.exists(configPath)) {
			CanopyCavernConfig defaults = defaults();
			save(configPath, defaults, logger);
			return defaults;
		}

		try {
			String raw = Files.readString(configPath, StandardCharsets.UTF_8);
			JsonElement element = JsonParser.parseString(raw);
			if (element == null || !element.isJsonObject()) {
				logger.warn("Empty config at {}, falling back to defaults.", configPath);
				return defaults();
			}
			JsonObject obj = element.getAsJsonObject();
			JsonObject defaultObj = GSON.toJsonTree(defaults()).getAsJsonObject();
			boolean migrated = false;
			for (String key : defaultObj.keySet()) {
				if (!obj.has(key)) {
					obj.add(key, defaultObj.get(key));
					migrated = true;
				}
			}
			CanopyCavernConfig parsed = GSON.fromJson(obj, CanopyCavernConfig.class);
			if (parsed == null) {
				return defaults();
			}
			if (migrated) {
				save(configPath, parsed, logger);
			}
			return parsed;
		} catch (IOException | JsonParseException | IllegalStateException ex) {
			logger.warn("Failed to parse config at {}, using defaults: {}", configPath, ex.getMessage());
			return defaults();
		}
	}

	/** Persists configuration atomically when possible. */
	public static void save(Path configPath, CanopyCavernConfig config, Logger logger) {
		try {
			Path parent = configPath.getParent();
			if (parent != null) {
				Files.createDirectories(parent);
			}
			Files.writeString(configPath, GSON.toJson(config), StandardCharsets.UTF_8);
		} catch (IOException ex) {
			logger.warn("Unable to write config at {}: {}", configPath, ex.getMessage());
		}
	}

	/** Returns a copy with toggled HUD visibility. */
	public CanopyCavernConfig withClientHudEnabled(boolean enabled) {
		return new CanopyCavernConfig(
			surfaceOverhaulEnabled,
			caveOverhaulEnabled,
			removeAbstractSurfaceLava,
			enabled,
			clientAtmosphereParticlesEnabled,
			useCelsius,
			climateSurvivalEnabled,
			starterFieldGuideEnabled,
			dynamicAmbienceEnabled
		);
	}
}
