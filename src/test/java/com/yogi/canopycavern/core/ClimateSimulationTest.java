package com.yogi.canopycavern.core;

import com.yogi.canopycavern.core.ClimateSimulation.ClimateInput;
import com.yogi.canopycavern.core.ClimateSimulation.ClimateSnapshot;
import com.yogi.canopycavern.core.ClimateSimulation.ClimateStatus;
import com.yogi.canopycavern.core.ClimateSimulation.MicroWeather;
import com.yogi.canopycavern.core.EnvironmentTelemetry.AmbientInput;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ClimateSimulationTest {

	@Test
	void fullThermalSetPreventsFrostPenaltyOnFreezingPeaks() {
		AmbientInput alpineStorm = new AmbientInput(-0.3f, 148, 63, true, 15, false, true, false);
		ClimateSnapshot unarmored = ClimateSimulation.evaluate(
			new ClimateInput(alpineStorm, "canopycavern:whispering_peaks", 0, 0, false, false, false, false, 0L)
		);
		ClimateSnapshot armored = ClimateSimulation.evaluate(
			new ClimateInput(alpineStorm, "canopycavern:whispering_peaks", 4, 0, false, false, false, false, 0L)
		);

		assertEquals(MicroWeather.BLIZZARD_CHILL, unarmored.microWeather());
		assertTrue(unarmored.frostPenaltyActive());
		assertFalse(armored.frostPenaltyActive());
		assertEquals(100, armored.thermalInsulationPercent());
		assertTrue(armored.perceivedCelsius() > unarmored.perceivedCelsius());
	}

	@Test
	void mossweaveSetAndGlowLanternMitigateCavernHeatAndHumidity() {
		AmbientInput deepThermalCave = new AmbientInput(0.8f, -40, 63, false, 0, false, false, false);
		ClimateSnapshot exposed = ClimateSimulation.evaluate(
			new ClimateInput(deepThermalCave, "canopycavern:verdant_grotto", 0, 0, false, false, false, true, 1000L)
		);
		ClimateSnapshot protectedPlayer = ClimateSimulation.evaluate(
			new ClimateInput(deepThermalCave, "canopycavern:verdant_grotto", 0, 4, true, false, false, true, 1000L)
		);

		assertEquals(MicroWeather.THERMAL_STEAM, exposed.microWeather());
		assertEquals(ClimateStatus.OVERHEATED, exposed.status());
		assertTrue(exposed.heatPenaltyActive());
		assertFalse(protectedPlayer.heatPenaltyActive());
		assertEquals(100, protectedPlayer.cavernCoolingPercent());
	}

	@Test
	void campfireAndEnclosedShelterProvideWarmthComfort() {
		AmbientInput coldNight = new AmbientInput(0.1f, 95, 63, true, 14, false, false, false);
		ClimateSnapshot sheltered = ClimateSimulation.evaluate(
			new ClimateInput(coldNight, "canopycavern:whispering_peaks", 0, 0, false, true, true, false, 3000L)
		);

		assertTrue(sheltered.warmthRecoveryActive());
		assertEquals(ClimateStatus.SHELTERED, sheltered.status());
		assertFalse(sheltered.frostPenaltyActive());
	}

	@Test
	void drySubmergedAirlockDomeGrantsShelteredRecoveryWithoutFrost() {
		AmbientInput deepOceanCold = new AmbientInput(0.15f, 24, 63, true, 12, false, false, false);
		ClimateSnapshot inDome = ClimateSimulation.evaluate(
			new ClimateInput(deepOceanCold, "minecraft:deep_ocean", 0, 0, false, true, true, false, 4000L)
		);

		assertTrue(inDome.warmthRecoveryActive());
		assertEquals(ClimateStatus.SHELTERED, inDome.status());
		assertFalse(inDome.frostPenaltyActive());
	}

	@Test
	void thermalWeaveInsulationAddsToArmorAndCapsAtOneHundredPercent() {
		AmbientInput coldPeak = new AmbientInput(-0.3f, 148, 63, true, 15, false, true, false);
		ClimateSnapshot unenchanted = ClimateSimulation.evaluate(
			new ClimateInput(coldPeak, "canopycavern:whispering_peaks", 1, 0, false, false, false, false, 0L)
		);
		ClimateSnapshot weave = ClimateSimulation.evaluate(
			new ClimateInput(coldPeak, "canopycavern:whispering_peaks", 1, 0, false, false, false, false, 0L, 2, 0)
		);
		ClimateSnapshot fullSet = ClimateSimulation.evaluate(
			new ClimateInput(coldPeak, "canopycavern:whispering_peaks", 4, 0, false, false, false, false, 0L, 2, 0)
		);
		assertEquals(45, weave.thermalInsulationPercent());
		assertEquals(100, fullSet.thermalInsulationPercent());
		assertTrue(weave.perceivedCelsius() > unenchanted.perceivedCelsius());
	}

	@Test
	void sporeFilterChangesExposureStatusWithoutChangingMeasuredHumidity() {
		AmbientInput dampGrotto = new AmbientInput(0.7f, 10, 63, false, 0, false, false, false);
		ClimateSnapshot exposed = ClimateSimulation.evaluate(
			new ClimateInput(dampGrotto, "canopycavern:verdant_grotto", 0, 0, false, false, false, false, 1000L)
		);
		ClimateSnapshot filtered = ClimateSimulation.evaluate(
			new ClimateInput(dampGrotto, "canopycavern:verdant_grotto", 0, 0, false, false, false, false, 1000L, 0, 2)
		);
		assertEquals(ClimateStatus.HUMID, exposed.status());
		assertEquals(ClimateStatus.COMFORTABLE, filtered.status());
		assertEquals(exposed.humidityPercent(), filtered.humidityPercent());
		assertEquals(exposed.microWeather(), filtered.microWeather());
	}
}
