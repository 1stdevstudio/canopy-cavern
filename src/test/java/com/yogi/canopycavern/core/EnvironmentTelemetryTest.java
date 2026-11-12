package com.yogi.canopycavern.core;

import com.yogi.canopycavern.core.EnvironmentTelemetry.AmbientInput;
import com.yogi.canopycavern.core.EnvironmentTelemetry.AmbientSnapshot;
import com.yogi.canopycavern.core.EnvironmentTelemetry.DepthZone;
import com.yogi.canopycavern.core.EnvironmentTelemetry.ThermalBand;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class EnvironmentTelemetryTest {

	@Test
	void classifiesSurfaceAndHighRidgeZones() {
		AmbientInput plains = new AmbientInput(0.8f, 68, 63, true, 15, false, false, false);
		AmbientInput ridge = new AmbientInput(0.2f, 125, 63, true, 15, false, false, false);

		assertEquals(DepthZone.SURFACE, EnvironmentTelemetry.classifyDepthZone(plains));
		assertEquals(DepthZone.HIGH_RIDGE, EnvironmentTelemetry.classifyDepthZone(ridge));
	}

	@Test
	void classifiesCaveTiersWhenEnclosedAndDark() {
		AmbientInput shallowCave = new AmbientInput(0.8f, 40, 63, false, 0, false, false, false);
		AmbientInput deepCavern = new AmbientInput(0.8f, -5, 63, false, 1, false, false, false);
		AmbientInput abyssal = new AmbientInput(0.8f, -45, 63, false, 0, false, false, false);

		assertEquals(DepthZone.SHALLOW_CAVE, EnvironmentTelemetry.classifyDepthZone(shallowCave));
		assertEquals(DepthZone.DEEP_CAVERN, EnvironmentTelemetry.classifyDepthZone(deepCavern));
		assertEquals(DepthZone.ABYSSAL_DEPTHS, EnvironmentTelemetry.classifyDepthZone(abyssal));
	}

	@Test
	void treatsLitHouseBelowSeaLevelAsSurfaceRatherThanCave() {
		AmbientInput skylightBasement = new AmbientInput(0.8f, 50, 63, false, 8, false, false, false);
		assertEquals(DepthZone.SURFACE, EnvironmentTelemetry.classifyDepthZone(skylightBasement));
	}

	@Test
	void coolsMountainPeaksAndDampensCaveTemperature() {
		AmbientSnapshot desertNoon = EnvironmentTelemetry.evaluate(
			new AmbientInput(2.0f, 64, 63, true, 15, false, false, false)
		);
		AmbientSnapshot desertCave = EnvironmentTelemetry.evaluate(
			new AmbientInput(2.0f, 32, 63, false, 0, false, false, false)
		);
		AmbientSnapshot freezingPeak = EnvironmentTelemetry.evaluate(
			new AmbientInput(-0.3f, 140, 63, true, 15, true, true, false)
		);

		assertEquals(ThermalBand.SCORCHING, desertNoon.thermalBand());
		assertTrue(desertCave.apparentCelsius() < desertNoon.apparentCelsius());
		assertTrue(desertCave.dampCave());
		assertEquals(ThermalBand.FREEZING, freezingPeak.thermalBand());
	}

	@Test
	void warmsSlightlyInAbyssalDepthsAndCoolsInWater() {
		AmbientSnapshot dryAbyss = EnvironmentTelemetry.evaluate(
			new AmbientInput(0.5f, -50, 63, false, 0, false, false, false)
		);
		AmbientSnapshot wetAbyss = EnvironmentTelemetry.evaluate(
			new AmbientInput(0.5f, -50, 63, false, 0, false, false, true)
		);

		assertFalse(dryAbyss.dampCave());
		assertTrue(wetAbyss.dampCave());
		assertTrue(dryAbyss.apparentCelsius() > wetAbyss.apparentCelsius());
	}

	@Test
	void formatsTemperatureAndBiomeNamesCleanly() {
		assertEquals("20.0°C", EnvironmentTelemetry.formatTemperature(20.0, true));
		assertEquals("68.0°F", EnvironmentTelemetry.formatTemperature(20.0, false));
		assertEquals("Dripstone Caves", EnvironmentTelemetry.formatBiomeName("minecraft:dripstone_caves"));
		assertEquals("Unknown", EnvironmentTelemetry.formatBiomeName(" "));
	}
}
