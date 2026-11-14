package com.yogi.canopycavern.core;

import com.yogi.canopycavern.core.ClimateSimulation.ClimateStatus;
import com.yogi.canopycavern.core.ClimateSimulation.MicroWeather;
import com.yogi.canopycavern.core.EnvironmentTelemetry.DepthZone;
import com.yogi.canopycavern.core.EnvironmentTelemetry.ThermalBand;
import com.yogi.canopycavern.core.HudTelemetryFormatter.HudPresentation;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;

class HudTelemetryFormatterTest {

	@Test
	void neutralExplorationCollapsesToTwoMinimalLinesWithNoNoise() {
		HudPresentation hud = HudTelemetryFormatter.buildPresentation(
			"Elder Bough Grove",
			DepthZone.SURFACE,
			ThermalBand.COMFORTABLE,
			20.4,
			82,
			MicroWeather.CLEAR,
			ClimateStatus.COMFORTABLE,
			0,
			0,
			true
		);

		assertEquals(2, hud.rowCount());
		assertNull(hud.modifierLine());
		assertEquals("Elder Bough Grove", hud.headerLine().spans().get(0).literal());
		assertEquals("hud.canopycavern.zone.surface", hud.headerLine().spans().get(1).key());
		assertEquals(2, hud.telemetryLine().spans().size());
		assertEquals("20.4°C", hud.telemetryLine().spans().get(0).literal());
		assertEquals("82% RH", hud.telemetryLine().spans().get(1).literal());
		assertEquals(HudTelemetryFormatter.BG_CALM, hud.style().backgroundColor());
		assertEquals(HudTelemetryFormatter.ACCENT_CALM, hud.style().accentBarColor());
	}

	@Test
	void activeHazardStatusAndMicroWeatherAppearConditionallyWithHazardStyling() {
		HudPresentation freezingHud = HudTelemetryFormatter.buildPresentation(
			"Whispering Peaks",
			DepthZone.HIGH_RIDGE,
			ThermalBand.FREEZING,
			-6.5,
			64,
			MicroWeather.BLIZZARD_CHILL,
			ClimateStatus.FREEZING,
			75,
			0,
			true
		);

		assertEquals(3, freezingHud.rowCount());
		assertEquals(3, freezingHud.telemetryLine().spans().size());
		assertEquals("hud.canopycavern.chip.freezing", freezingHud.telemetryLine().spans().get(2).key());
		assertNotNull(freezingHud.modifierLine());
		assertEquals(2, freezingHud.modifierLine().spans().size());
		assertEquals("hud.canopycavern.weather.blizzard_chill", freezingHud.modifierLine().spans().get(0).key());
		assertEquals("hud.canopycavern.gear.warm", freezingHud.modifierLine().spans().get(1).key());
		assertEquals(75, freezingHud.modifierLine().spans().get(1).args().get(0));
		assertEquals(HudTelemetryFormatter.BG_FREEZING, freezingHud.style().backgroundColor());
		assertEquals(HudTelemetryFormatter.ACCENT_FREEZING, freezingHud.style().accentBarColor());
	}

	@Test
	void nonZeroCoolingOnlyOmitsZeroWarmthAndSupportsFahrenheit() {
		HudPresentation caveHud = HudTelemetryFormatter.buildPresentation(
			"   ",
			DepthZone.DEEP_CAVERN,
			ThermalBand.WARM,
			35.0,
			70,
			MicroWeather.CLEAR,
			ClimateStatus.OVERHEATED,
			0,
			50,
			false
		);

		assertEquals("Unknown", caveHud.headerLine().spans().get(0).literal());
		assertEquals("95.0°F", caveHud.telemetryLine().spans().get(0).literal());
		assertEquals("hud.canopycavern.chip.overheated", caveHud.telemetryLine().spans().get(2).key());
		assertEquals(3, caveHud.rowCount());
		assertNotNull(caveHud.modifierLine());
		assertEquals(1, caveHud.modifierLine().spans().size());
		assertEquals("hud.canopycavern.gear.cool", caveHud.modifierLine().spans().get(0).key());
		assertEquals(50, caveHud.modifierLine().spans().get(0).args().get(0));
		assertEquals(HudTelemetryFormatter.BG_OVERHEATED, caveHud.style().backgroundColor());
		assertEquals(HudTelemetryFormatter.ACCENT_OVERHEATED, caveHud.style().accentBarColor());
	}

	@Test
	void shelteredStateAppearsOnTelemetryLineWithoutThirdLineWhenClearAndNoArmor() {
		HudPresentation sheltered = HudTelemetryFormatter.buildPresentation(
			"Snowy Plains",
			DepthZone.SURFACE,
			ThermalBand.COOL,
			14.0,
			40,
			MicroWeather.CLEAR,
			ClimateStatus.SHELTERED,
			0,
			0,
			true
		);

		assertEquals(2, sheltered.rowCount());
		assertNull(sheltered.modifierLine());
		assertEquals("hud.canopycavern.chip.sheltered", sheltered.telemetryLine().spans().get(2).key());
		assertEquals(HudTelemetryFormatter.ACCENT_SHELTERED, sheltered.style().accentBarColor());
	}
}
