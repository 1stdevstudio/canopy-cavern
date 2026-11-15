package com.yogi.canopycavern.core;

import java.util.Locale;

/**
 * Pure domain evaluator for vertical depth zones and apparent ambient temperature.
 * Independent of Minecraft runtime types so client previews and future server rules share one model.
 */
public final class EnvironmentTelemetry {
	private static final double CAVE_EQUILIBRIUM_CELSIUS = 13.0;
	private static final int HIGH_RIDGE_OFFSET = 42;
	private static final int SHALLOW_CAVE_MAX_SKY_LIGHT = 2;

	private EnvironmentTelemetry() {
	}

	public enum DepthZone {
		HIGH_RIDGE("hud.canopycavern.zone.high_ridge", 0xFF9CD4FF),
		SURFACE("hud.canopycavern.zone.surface", 0xFFAEE8A8),
		SHALLOW_CAVE("hud.canopycavern.zone.shallow_cave", 0xFF7BE0C3),
		DEEP_CAVERN("hud.canopycavern.zone.deep_cavern", 0xFFF3C677),
		ABYSSAL_DEPTHS("hud.canopycavern.zone.abyssal_depths", 0xFFD98BFF),
		NETHER_CAVERN("hud.canopycavern.zone.nether_cavern", 0xFFFF8855),
		END_ISLANDS("hud.canopycavern.zone.end_islands", 0xFFD9A6FF);

		private final String translationKey;
		private final int accentColor;

		DepthZone(String translationKey, int accentColor) {
			this.translationKey = translationKey;
			this.accentColor = accentColor;
		}

		public String translationKey() {
			return translationKey;
		}

		public int accentColor() {
			return accentColor;
		}
	}

	public enum ThermalBand {
		FREEZING("hud.canopycavern.thermal.freezing", 0xFF7BD3FF),
		COLD("hud.canopycavern.thermal.cold", 0xFFA4E0FF),
		COOL("hud.canopycavern.thermal.cool", 0xFFB8F2D6),
		COMFORTABLE("hud.canopycavern.thermal.comfortable", 0xFFE8F5C8),
		WARM("hud.canopycavern.thermal.warm", 0xFFFFCA7A),
		SCORCHING("hud.canopycavern.thermal.scorching", 0xFFFF7A6B);

		private final String translationKey;
		private final int accentColor;

		ThermalBand(String translationKey, int accentColor) {
			this.translationKey = translationKey;
			this.accentColor = accentColor;
		}

		public String translationKey() {
			return translationKey;
		}

		public int accentColor() {
			return accentColor;
		}
	}

	/** Raw environmental snapshot sampled from world coordinates and weather state. */
	public record AmbientInput(
		float biomeBaseTemperature,
		int blockY,
		int seaLevel,
		boolean canSeeSky,
		int skyLight,
		boolean raining,
		boolean night,
		boolean inWater
	) {
	}

	/** Evaluated zone classification and apparent temperature metrics. */
	public record AmbientSnapshot(
		DepthZone depthZone,
		double apparentCelsius,
		ThermalBand thermalBand,
		boolean dampCave
	) {
	}

	/** Evaluates depth classification and apparent temperature from an environmental sample. */
	public static AmbientSnapshot evaluate(AmbientInput input) {
		DepthZone zone = classifyDepthZone(input);
		boolean underground = isUnderground(zone);
		double apparentCelsius = computeApparentCelsius(input, underground);
		ThermalBand band = classifyThermalBand(apparentCelsius);
		boolean dampCave = underground && (input.inWater() || input.blockY() >= -12);
		return new AmbientSnapshot(zone, apparentCelsius, band, dampCave);
	}

	/**
	 * Biome-aware telemetry evaluator that classifies Nether caverns and outer End islands
	 * cleanly alongside Overworld elevation and cavern zones without breaking Overworld defaults.
	 */
	public static AmbientSnapshot evaluateForBiome(AmbientInput input, String biomeId) {
		if (isNetherBiome(biomeId)) {
			double celsius = switch (biomeId) {
				case "minecraft:soul_sand_valley" -> 24.5;
				case "minecraft:warped_forest" -> 28.5;
				case "minecraft:crimson_forest" -> 31.0;
				case "minecraft:basalt_deltas" -> 33.5;
				default -> 32.0;
			};
			if (input.inWater()) {
				celsius -= 3.0;
			}
			celsius = roundTenths(celsius);
			return new AmbientSnapshot(DepthZone.NETHER_CAVERN, celsius, classifyThermalBand(celsius), false);
		}
		if (isEndBiome(biomeId)) {
			double celsius = input.blockY() >= 96 ? 6.0 : 8.5;
			if (input.inWater()) {
				celsius -= 2.5;
			}
			celsius = roundTenths(celsius);
			return new AmbientSnapshot(DepthZone.END_ISLANDS, celsius, classifyThermalBand(celsius), false);
		}
		return evaluate(input);
	}

	/** Returns true if the namespaced biome ID belongs to the Nether dimension. */
	public static boolean isNetherBiome(String biomeId) {
		if (biomeId == null) {
			return false;
		}
		return switch (biomeId) {
			case "minecraft:nether_wastes",
				"minecraft:crimson_forest",
				"minecraft:warped_forest",
				"minecraft:soul_sand_valley",
				"minecraft:basalt_deltas" -> true;
			default -> false;
		};
	}

	/** Returns true if the namespaced biome ID belongs to The End dimension. */
	public static boolean isEndBiome(String biomeId) {
		if (biomeId == null) {
			return false;
		}
		return switch (biomeId) {
			case "minecraft:the_end",
				"minecraft:end_highlands",
				"minecraft:end_midlands",
				"minecraft:small_end_islands",
				"minecraft:end_barrens" -> true;
			default -> false;
		};
	}

	/** Classifies vertical exploration zones across surface ridges and cave tiers. */
	public static DepthZone classifyDepthZone(AmbientInput input) {
		boolean enclosed = !input.canSeeSky() && input.skyLight() <= SHALLOW_CAVE_MAX_SKY_LIGHT;
		if (enclosed) {
			if (input.blockY() < -24) {
				return DepthZone.ABYSSAL_DEPTHS;
			}
			if (input.blockY() < 16) {
				return DepthZone.DEEP_CAVERN;
			}
			if (input.blockY() < input.seaLevel() - 4) {
				return DepthZone.SHALLOW_CAVE;
			}
		}

		if (input.blockY() >= input.seaLevel() + HIGH_RIDGE_OFFSET) {
			return DepthZone.HIGH_RIDGE;
		}
		return DepthZone.SURFACE;
	}

	private static boolean isUnderground(DepthZone zone) {
		return zone == DepthZone.SHALLOW_CAVE
			|| zone == DepthZone.DEEP_CAVERN
			|| zone == DepthZone.ABYSSAL_DEPTHS;
	}

	private static double computeApparentCelsius(AmbientInput input, boolean underground) {
		double clampedBiomeTemp = Math.max(-0.7, Math.min(2.2, input.biomeBaseTemperature()));
		double surfaceBase = 2.0 + clampedBiomeTemp * 18.0;

		if (underground) {
			// Subterranean rock dampens surface climate extremes and warms slightly near bedrock.
			double buffered = (surfaceBase * 0.2) + (CAVE_EQUILIBRIUM_CELSIUS * 0.8);
			if (input.blockY() < -20) {
				buffered += (-20 - input.blockY()) * 0.18;
			}
			if (input.inWater()) {
				buffered -= 3.5;
			}
			return roundTenths(buffered);
		}

		double temp = surfaceBase;
		if (input.blockY() > input.seaLevel()) {
			temp -= (input.blockY() - input.seaLevel()) * 0.11;
		}
		if (input.night() && input.canSeeSky()) {
			temp -= 4.5;
		}
		if (input.raining() && input.canSeeSky()) {
			temp -= 2.5;
		}
		if (input.inWater()) {
			temp -= 4.0;
		}
		return roundTenths(temp);
	}

	/** Maps apparent Celsius temperature to a qualitative comfort band. */
	public static ThermalBand classifyThermalBand(double celsius) {
		if (celsius <= 0.0) {
			return ThermalBand.FREEZING;
		}
		if (celsius < 10.0) {
			return ThermalBand.COLD;
		}
		if (celsius < 17.0) {
			return ThermalBand.COOL;
		}
		if (celsius < 27.0) {
			return ThermalBand.COMFORTABLE;
		}
		if (celsius < 34.0) {
			return ThermalBand.WARM;
		}
		return ThermalBand.SCORCHING;
	}

	/** Formats temperature in Celsius or Fahrenheit. */
	public static String formatTemperature(double celsius, boolean useCelsius) {
		if (useCelsius) {
			return String.format(Locale.ROOT, "%.1f°C", celsius);
		}
		double fahrenheit = (celsius * 9.0 / 5.0) + 32.0;
		return String.format(Locale.ROOT, "%.1f°F", fahrenheit);
	}

	/** Converts a namespaced biome key like "minecraft:dripstone_caves" into "Dripstone Caves". */
	public static String formatBiomeName(String rawKey) {
		if (rawKey == null || rawKey.isBlank()) {
			return "Unknown";
		}
		int colon = rawKey.indexOf(':');
		String path = colon >= 0 ? rawKey.substring(colon + 1) : rawKey;
		String[] parts = path.split("_");
		StringBuilder sb = new StringBuilder();
		for (String part : parts) {
			if (part.isEmpty()) {
				continue;
			}
			if (!sb.isEmpty()) {
				sb.append(' ');
			}
			sb.append(Character.toUpperCase(part.charAt(0)));
			if (part.length() > 1) {
				sb.append(part.substring(1));
			}
		}
		return sb.isEmpty() ? "Unknown" : sb.toString();
	}

	private static double roundTenths(double value) {
		return Math.round(value * 10.0) / 10.0;
	}
}
