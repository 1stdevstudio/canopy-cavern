package com.yogi.canopycavern.core;

import com.yogi.canopycavern.core.EnvironmentTelemetry.AmbientInput;
import com.yogi.canopycavern.core.EnvironmentTelemetry.AmbientSnapshot;
import com.yogi.canopycavern.core.EnvironmentTelemetry.DepthZone;

/**
 * Pure server-deterministic simulation of Canopy Cavern micro-weather, humidity,
 * campfire/shelter comfort buffs, and thermal/mossweave armor insulation.
 */
public final class ClimateSimulation {

	public enum MicroWeather {
		CLEAR("clear"),
		MISTY_WIND("misty_wind"),
		BLIZZARD_CHILL("blizzard_chill"),
		CAVERN_HUMID("cavern_humid"),
		THERMAL_STEAM("thermal_steam");

		private final String id;

		MicroWeather(String id) {
			this.id = id;
		}

		public String id() {
			return id;
		}

		public static MicroWeather fromId(String id) {
			for (MicroWeather value : values()) {
				if (value.id.equals(id)) {
					return value;
				}
			}
			return CLEAR;
		}
	}

	public enum ClimateStatus {
		COMFORTABLE("comfortable"),
		CHILLY("chilly"),
		FREEZING("freezing"),
		HUMID("humid"),
		OVERHEATED("overheated"),
		SHELTERED("sheltered");

		private final String id;

		ClimateStatus(String id) {
			this.id = id;
		}

		public String id() {
			return id;
		}

		public static ClimateStatus fromId(String id) {
			for (ClimateStatus value : values()) {
				if (value.id.equals(id)) {
					return value;
				}
			}
			return COMFORTABLE;
		}
	}

	public record ClimateInput(
		AmbientInput ambient,
		String biomeId,
		int thermalArmorPieces,
		int mossweaveArmorPieces,
		boolean hasGlowLantern,
		boolean nearCampfire,
		boolean enclosedShelter,
		boolean nearLava,
		long worldTimeTicks,
		int thermalWeaveLevel,
		int sporeFilterLevel
	) {
		public ClimateInput(
			AmbientInput ambient, String biomeId, int thermalArmorPieces, int mossweaveArmorPieces,
			boolean hasGlowLantern, boolean nearCampfire, boolean enclosedShelter, boolean nearLava,
			long worldTimeTicks
		) {
			this(ambient, biomeId, thermalArmorPieces, mossweaveArmorPieces, hasGlowLantern,
				nearCampfire, enclosedShelter, nearLava, worldTimeTicks, 0, 0);
		}
	}

	public record ClimateSnapshot(
		AmbientSnapshot telemetry,
		int humidityPercent,
		MicroWeather microWeather,
		ClimateStatus status,
		int thermalInsulationPercent,
		int cavernCoolingPercent,
		double perceivedCelsius,
		boolean frostPenaltyActive,
		boolean heatPenaltyActive,
		boolean warmthRecoveryActive
	) {
		public static ClimateSnapshot neutral() {
			return evaluate(new ClimateInput(
				new AmbientInput(0.7f, 64, 63, true, 15, false, false, false),
				"minecraft:plains",
				0,
				0,
				false,
				false,
				false,
				false,
				0L
			));
		}
	}

	private ClimateSimulation() {
	}

	/** Evaluates micro-weather, humidity, armor mitigation, and survival debuff flags. */
	public static ClimateSnapshot evaluate(ClimateInput input) {
		AmbientSnapshot base = EnvironmentTelemetry.evaluateForBiome(input.ambient(), input.biomeId());
		int thermalPieces = clampPieces(input.thermalArmorPieces());
		int mossPieces = clampPieces(input.mossweaveArmorPieces());
		int thermalInsulation = Math.min(100, thermalPieces * 25
			+ ExpeditionEnchantmentRules.clampTwoLevels(input.thermalWeaveLevel()) * 10);
		int cavernCooling = mossPieces * 25;

		int humidity = computeHumidity(input, base);
		MicroWeather weather = classifyMicroWeather(input, base, humidity);
		double shifted = computePerceivedTemperature(input, base, weather, thermalInsulation, mossPieces);
		ClimateStatus status = classifyStatus(input, base.depthZone(), shifted, humidity);

		boolean frostPenalty = status == ClimateStatus.FREEZING && thermalPieces < 4;
		boolean heatPenalty = status == ClimateStatus.OVERHEATED && mossPieces < 4;
		boolean warmthRecovery = input.nearCampfire() || (input.enclosedShelter() && !frostPenalty && !heatPenalty);

		return new ClimateSnapshot(
			base,
			humidity,
			weather,
			status,
			thermalInsulation,
			cavernCooling,
			shifted,
			frostPenalty,
			heatPenalty,
			warmthRecovery
		);
	}

	private static int clampPieces(int count) {
		return Math.max(0, Math.min(4, count));
	}

	private static int computeHumidity(ClimateInput input, AmbientSnapshot base) {
		String biome = input.biomeId() == null ? "" : input.biomeId();
		boolean cave = isCave(base.depthZone());
		int humidity = switch (biome) {
			case "canopycavern:verdant_grotto", "minecraft:lush_caves" -> 84;
			case "canopycavern:luminous_depths" -> 88;
			case "canopycavern:sunlit_shallows" -> 82;
			case "canopycavern:coral_drift" -> 80;
			case "canopycavern:temperate_sound" -> 78;
			case "canopycavern:abyssal_trench" -> 78;
			case "canopycavern:kelpwood_sea" -> 74;
			case "canopycavern:floe_sea" -> 66;
			case "canopycavern:meandering_river" -> 72;
			case "canopycavern:frostbound_river" -> 60;
			case "canopycavern:golden_strand" -> 64;
			case "canopycavern:frostline_shore" -> 56;
			case "canopycavern:wildgrass_plains" -> 50;
			case "canopycavern:sunbaked_savanna" -> 30;
			case "canopycavern:dune_expanse" -> 12;
			case "canopycavern:rustrock_badlands" -> 10;
			case "canopycavern:oakhollow_woods" -> 70;
			case "canopycavern:bloomveil_forest" -> 72;
			case "canopycavern:silverbirch_glade" -> 66;
			case "canopycavern:blossom_terrace" -> 64;
			case "canopycavern:dapplelight_wood" -> 68;
			case "canopycavern:ashen_garden" -> 62;
			case "canopycavern:spruce_hollow" -> 74;
			case "canopycavern:giant_spruce_reach" -> 78;
			case "canopycavern:tanglewild_jungle" -> 92;
			case "canopycavern:bamboo_thicket" -> 90;
			case "canopycavern:bogwater_fen" -> 94;
			case "canopycavern:mangrove_tangle" -> 96;
			case "canopycavern:snowbound_tundra" -> 40;
			case "canopycavern:rime_spires" -> 36;
			case "canopycavern:frostpine_taiga" -> 58;
			case "canopycavern:hoarfrost_grove" -> 54;
			case "canopycavern:powder_slopes" -> 46;
			case "canopycavern:glacier_crown" -> 38;
			case "canopycavern:slatestone_peaks" -> 40;
			case "canopycavern:gravel_barrens" -> 42;
			case "canopycavern:windbent_forest" -> 56;
			case "canopycavern:gale_savanna" -> 28;
			case "canopycavern:mycelium_isles" -> 88;
			case "canopycavern:hushed_depths" -> 70;
			case "canopycavern:sulfur_hollows" -> 58;
			case "canopycavern:elder_bough_grove" -> 82;
			case "canopycavern:mossy_canopy" -> 76;
			case "canopycavern:crystal_steppe" -> 46;
			case "canopycavern:whispering_peaks" -> 54;
			case "canopycavern:frostspire_crags" -> 48;
			case "canopycavern:windcarved_cliffs" -> 44;
			case "minecraft:nether_wastes", "minecraft:basalt_deltas", "minecraft:soul_sand_valley" -> 24;
			case "minecraft:crimson_forest", "minecraft:warped_forest" -> 38;
			case "minecraft:the_end", "minecraft:end_highlands", "minecraft:end_midlands",
				"minecraft:small_end_islands", "minecraft:end_barrens" -> 32;
			default -> cave ? 66 : 52;
		};

		boolean extraterrestrial = base.depthZone() == DepthZone.NETHER_CAVERN
			|| base.depthZone() == DepthZone.END_ISLANDS;
		if (input.ambient().raining() && !cave && !extraterrestrial) {
			humidity += 16;
		}
		if (base.dampCave()) {
			humidity += 12;
		}
		if (input.ambient().inWater()) {
			humidity += 20;
		}
		if (input.nearLava()) {
			humidity -= 24;
		}
		if (input.enclosedShelter() && !input.ambient().inWater()) {
			humidity -= 10;
		}
		return Math.max(10, Math.min(100, humidity));
	}

	private static boolean isCave(DepthZone zone) {
		return zone == DepthZone.SHALLOW_CAVE || zone == DepthZone.DEEP_CAVERN || zone == DepthZone.ABYSSAL_DEPTHS;
	}

	private static MicroWeather classifyMicroWeather(ClimateInput input, AmbientSnapshot base, int humidity) {
		if (base.depthZone() == DepthZone.NETHER_CAVERN) {
			return input.nearLava() ? MicroWeather.THERMAL_STEAM : MicroWeather.CLEAR;
		}
		if (base.depthZone() == DepthZone.END_ISLANDS) {
			boolean highSpire = input.ambient().blockY() >= 100 && !input.enclosedShelter() && !input.nearCampfire();
			return highSpire ? MicroWeather.MISTY_WIND : MicroWeather.CLEAR;
		}
		boolean cave = isCave(base.depthZone());
		if (input.nearLava() && cave) {
			return MicroWeather.THERMAL_STEAM;
		}
		if (cave) {
			return humidity >= 74 ? MicroWeather.CAVERN_HUMID : MicroWeather.CLEAR;
		}

		boolean peakZone = base.depthZone() == DepthZone.HIGH_RIDGE
			|| "canopycavern:whispering_peaks".equals(input.biomeId())
			|| "canopycavern:frostspire_crags".equals(input.biomeId());
		boolean snowing = input.ambient().raining() && input.ambient().biomeBaseTemperature() <= 0.15f;
		boolean blizzardCycle = snowing || ((input.worldTimeTicks() / 2400L) % 3L == 0L);
		if (peakZone && base.apparentCelsius() <= 2.0 && blizzardCycle) {
			return MicroWeather.BLIZZARD_CHILL;
		}
		if (peakZone
			|| "canopycavern:mossy_canopy".equals(input.biomeId())
			|| "canopycavern:windcarved_cliffs".equals(input.biomeId())
			|| (input.worldTimeTicks() / 3600L) % 4L == 1L) {
			return MicroWeather.MISTY_WIND;
		}
		return MicroWeather.CLEAR;
	}

	private static double computePerceivedTemperature(
		ClimateInput input,
		AmbientSnapshot base,
		MicroWeather weather,
		int thermalInsulation,
		int mossPieces
	) {
		double temp = base.apparentCelsius();
		double steamBoost = base.depthZone() == DepthZone.NETHER_CAVERN ? 4.0 : 8.5;
		temp += switch (weather) {
			case BLIZZARD_CHILL -> -5.5;
			case MISTY_WIND -> -2.5;
			case THERMAL_STEAM -> steamBoost;
			case CAVERN_HUMID -> 2.0;
			case CLEAR -> 0.0;
		};

		if (input.nearLava()) {
			temp += 11.0;
		}
		if (input.nearCampfire()) {
			temp = temp < 18.0 ? Math.min(19.0, temp + 11.0) : temp + 2.0;
		}
		if (input.enclosedShelter()) {
			temp = temp + (18.0 - temp) * 0.55;
		}

		if (temp < 15.0 && thermalInsulation > 0) {
			double coldDeficit = 15.0 - temp;
			temp += coldDeficit * (thermalInsulation / 100.0);
		}
		if (temp > 23.0 && mossPieces > 0) {
			double heatExcess = temp - 23.0;
			temp -= heatExcess * (mossPieces * 0.25);
		}
		if (input.hasGlowLantern() && isCave(base.depthZone()) && temp < 14.0) {
			temp += 2.5;
		}
		return temp;
	}

	private static ClimateStatus classifyStatus(
		ClimateInput input, DepthZone zone, double perceivedCelsius, int humidity
	) {
		if (perceivedCelsius <= -2.0) {
			return ClimateStatus.FREEZING;
		}
		if (perceivedCelsius <= 6.5) {
			return ClimateStatus.CHILLY;
		}
		if (perceivedCelsius >= 35.0) {
			return ClimateStatus.OVERHEATED;
		}
		int effectiveHumidity = humidity - (isCave(zone)
			? ExpeditionEnchantmentRules.clampTwoLevels(input.sporeFilterLevel()) * 10 : 0);
		boolean unshieldedHumid = effectiveHumidity >= 82
			&& !input.enclosedShelter()
			&& input.mossweaveArmorPieces() < 2
			&& !input.hasGlowLantern();
		if (unshieldedHumid) {
			return ClimateStatus.HUMID;
		}
		if (input.nearCampfire() || input.enclosedShelter()) {
			return ClimateStatus.SHELTERED;
		}
		return ClimateStatus.COMFORTABLE;
	}
}
