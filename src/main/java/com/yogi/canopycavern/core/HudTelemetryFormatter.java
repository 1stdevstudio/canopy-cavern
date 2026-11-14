package com.yogi.canopycavern.core;

import com.yogi.canopycavern.core.ClimateSimulation.ClimateStatus;
import com.yogi.canopycavern.core.ClimateSimulation.MicroWeather;
import com.yogi.canopycavern.core.EnvironmentTelemetry.DepthZone;
import com.yogi.canopycavern.core.EnvironmentTelemetry.ThermalBand;

import java.util.ArrayList;
import java.util.List;

/**
 * Builds a minimal, progressive-disclosure presentation model for the environmental HUD.
 * Keeps neutral states down to two compact lines and surfaces status, micro-weather,
 * and active armor protection only when non-idle.
 */
public final class HudTelemetryFormatter {

	public static final int COLOR_BIOME = 0xFFF2F7F4;
	public static final int COLOR_SEPARATOR = 0xFF7D9287;
	public static final int COLOR_HUMIDITY = 0xFFB4CCC0;
	public static final int COLOR_WEATHER = 0xFFCDE2D8;
	public static final int COLOR_WEATHER_BLIZZARD = 0xFF9EE0FF;
	public static final int COLOR_WEATHER_STEAM = 0xFFFFBF8E;
	public static final int COLOR_GEAR_WARM = 0xFFFFD58C;
	public static final int COLOR_GEAR_COOL = 0xFF80E8D0;

	public static final int BG_CALM = 0x460A100E;
	public static final int BG_FREEZING = 0x680A151E;
	public static final int BG_OVERHEATED = 0x6E1B0D0C;

	public static final int ACCENT_CALM = 0xFF4AA87F;
	public static final int ACCENT_FREEZING = 0xFF7FD7FF;
	public static final int ACCENT_CHILLY = 0xFFB0E4FF;
	public static final int ACCENT_OVERHEATED = 0xFFFF6B57;
	public static final int ACCENT_HUMID = 0xFF7DE8A8;
	public static final int ACCENT_SHELTERED = 0xFFFFD885;

	private HudTelemetryFormatter() {
	}

	/** Text span representing either a literal string or a translation key with arguments. */
	public record HudSpan(String key, String literal, int color, List<Object> args) {
		public static HudSpan literal(String text, int color) {
			return new HudSpan(null, text, color, List.of());
		}

		public static HudSpan translatable(String key, int color, Object... args) {
			return new HudSpan(key, null, color, List.of(args));
		}

		public boolean isTranslatable() {
			return key != null;
		}
	}

	/** Complete horizontal strip composed of inline colored spans. */
	public record HudLine(List<HudSpan> spans) {
	}

	/** Visual backing and accent bar tokens derived from current climate urgency. */
	public record HudStyle(int backgroundColor, int accentBarColor) {
	}

	/**
	 * Minimal HUD layout containing a 2-line core (location + climate) and an optional 3rd line
	 * reserved strictly for active micro-weather or armor protection percentages.
	 */
	public record HudPresentation(
		HudLine headerLine,
		HudLine telemetryLine,
		HudLine modifierLine,
		HudStyle style
	) {
		public int rowCount() {
			return modifierLine == null ? 2 : 3;
		}
	}

	/**
	 * Formats sampled biome/zone telemetry alongside synchronized climate state into compact lines.
	 */
	public static HudPresentation buildPresentation(
		String biomeName,
		DepthZone depthZone,
		ThermalBand thermalBand,
		double perceivedCelsius,
		int humidityPercent,
		MicroWeather microWeather,
		ClimateStatus status,
		int thermalInsulationPercent,
		int cavernCoolingPercent,
		boolean useCelsius
	) {
		String safeBiome = (biomeName == null || biomeName.isBlank()) ? "Unknown" : biomeName.trim();
		DepthZone safeZone = depthZone == null ? DepthZone.SURFACE : depthZone;
		ThermalBand safeBand = thermalBand == null ? ThermalBand.COMFORTABLE : thermalBand;
		MicroWeather safeWeather = microWeather == null ? MicroWeather.CLEAR : microWeather;
		ClimateStatus safeStatus = status == null ? ClimateStatus.COMFORTABLE : status;

		HudLine header = new HudLine(List.of(
			HudSpan.literal(safeBiome, COLOR_BIOME),
			HudSpan.translatable(safeZone.translationKey(), safeZone.accentColor())
		));

		List<HudSpan> telemetry = new ArrayList<>(3);
		telemetry.add(HudSpan.literal(
			EnvironmentTelemetry.formatTemperature(perceivedCelsius, useCelsius),
			safeBand.accentColor()
		));
		telemetry.add(HudSpan.literal(Math.max(0, humidityPercent) + "% RH", COLOR_HUMIDITY));
		if (safeStatus != ClimateStatus.COMFORTABLE) {
			telemetry.add(HudSpan.translatable(
				"hud.canopycavern.chip." + safeStatus.id(),
				statusColor(safeStatus)
			));
		}

		List<HudSpan> modifiers = buildModifiers(safeWeather, thermalInsulationPercent, cavernCoolingPercent);
		HudLine modifierLine = modifiers.isEmpty() ? null : new HudLine(modifiers);

		return new HudPresentation(
			header,
			new HudLine(List.copyOf(telemetry)),
			modifierLine,
			styleFor(safeStatus)
		);
	}

	private static List<HudSpan> buildModifiers(
		MicroWeather weather,
		int thermalInsulationPercent,
		int cavernCoolingPercent
	) {
		List<HudSpan> spans = new ArrayList<>(3);
		if (weather != MicroWeather.CLEAR) {
			spans.add(HudSpan.translatable(
				"hud.canopycavern.weather." + weather.id(),
				weatherColor(weather)
			));
		}
		if (thermalInsulationPercent > 0) {
			spans.add(HudSpan.translatable(
				"hud.canopycavern.gear.warm",
				COLOR_GEAR_WARM,
				thermalInsulationPercent
			));
		}
		if (cavernCoolingPercent > 0) {
			spans.add(HudSpan.translatable(
				"hud.canopycavern.gear.cool",
				COLOR_GEAR_COOL,
				cavernCoolingPercent
			));
		}
		return spans;
	}

	/** Returns the status badge and left accent bar color for the climate state. */
	public static int statusColor(ClimateStatus status) {
		return switch (status) {
			case FREEZING -> ACCENT_FREEZING;
			case CHILLY -> ACCENT_CHILLY;
			case OVERHEATED -> ACCENT_OVERHEATED;
			case HUMID -> ACCENT_HUMID;
			case SHELTERED -> ACCENT_SHELTERED;
			case COMFORTABLE -> ACCENT_CALM;
		};
	}

	private static int weatherColor(MicroWeather weather) {
		return switch (weather) {
			case BLIZZARD_CHILL -> COLOR_WEATHER_BLIZZARD;
			case THERMAL_STEAM -> COLOR_WEATHER_STEAM;
			default -> COLOR_WEATHER;
		};
	}

	private static HudStyle styleFor(ClimateStatus status) {
		int background = switch (status) {
			case FREEZING -> BG_FREEZING;
			case OVERHEATED -> BG_OVERHEATED;
			default -> BG_CALM;
		};
		return new HudStyle(background, statusColor(status));
	}
}
