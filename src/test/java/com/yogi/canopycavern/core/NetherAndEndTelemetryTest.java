package com.yogi.canopycavern.core;

import com.yogi.canopycavern.core.ClimateSimulation.ClimateInput;
import com.yogi.canopycavern.core.ClimateSimulation.ClimateSnapshot;
import com.yogi.canopycavern.core.ClimateSimulation.ClimateStatus;
import com.yogi.canopycavern.core.ClimateSimulation.MicroWeather;
import com.yogi.canopycavern.core.EnvironmentTelemetry.AmbientInput;
import com.yogi.canopycavern.core.EnvironmentTelemetry.AmbientSnapshot;
import com.yogi.canopycavern.core.EnvironmentTelemetry.DepthZone;
import com.yogi.canopycavern.core.HudTelemetryFormatter.HudPresentation;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class NetherAndEndTelemetryTest {

	@Test
	void netherBiomesClassifyAsNetherCavernWithoutUnfairOverheatAwayFromLava() {
		AmbientInput netherAmbient = new AmbientInput(2.0f, 58, 32, false, 0, false, false, false);
		AmbientSnapshot wastes = EnvironmentTelemetry.evaluateForBiome(netherAmbient, "minecraft:nether_wastes");
		assertEquals(DepthZone.NETHER_CAVERN, wastes.depthZone());
		assertTrue(wastes.apparentCelsius() >= 30.0 && wastes.apparentCelsius() < 35.0);

		ClimateSnapshot awayFromLava = ClimateSimulation.evaluate(new ClimateInput(
			netherAmbient, "minecraft:nether_wastes", 0, 0, false, false, false, false, 1200L
		));
		assertEquals(DepthZone.NETHER_CAVERN, awayFromLava.telemetry().depthZone());
		assertEquals(MicroWeather.CLEAR, awayFromLava.microWeather());
		assertFalse(awayFromLava.heatPenaltyActive());
		HudPresentation netherHud = HudTelemetryFormatter.buildPresentation(
			"Nether Wastes",
			awayFromLava.telemetry().depthZone(),
			awayFromLava.telemetry().thermalBand(),
			awayFromLava.perceivedCelsius(),
			awayFromLava.humidityPercent(),
			awayFromLava.microWeather(),
			awayFromLava.status(),
			0,
			0,
			true
		);
		assertEquals(DepthZone.NETHER_CAVERN.translationKey(), netherHud.headerLine().spans().getLast().key());

		ClimateSnapshot besideLava = ClimateSimulation.evaluate(new ClimateInput(
			netherAmbient, "minecraft:basalt_deltas", 0, 0, false, false, false, true, 1200L
		));
		assertEquals(MicroWeather.THERMAL_STEAM, besideLava.microWeather());
		assertEquals(ClimateStatus.OVERHEATED, besideLava.status());
		assertTrue(besideLava.heatPenaltyActive());
	}

	@Test
	void soulSandValleyFeelsCoolerAndEndIslandsStayChillAndNonPunishing() {
		AmbientInput netherAmbient = new AmbientInput(2.0f, 55, 32, false, 0, false, false, false);
		AmbientSnapshot soulValley = EnvironmentTelemetry.evaluateForBiome(netherAmbient, "minecraft:soul_sand_valley");
		AmbientSnapshot basaltDeltas = EnvironmentTelemetry.evaluateForBiome(netherAmbient, "minecraft:basalt_deltas");
		assertEquals(DepthZone.NETHER_CAVERN, soulValley.depthZone());
		assertTrue(soulValley.apparentCelsius() < basaltDeltas.apparentCelsius());

		AmbientInput endAmbient = new AmbientInput(0.5f, 64, 0, true, 15, false, false, false);
		ClimateSnapshot endHighlands = ClimateSimulation.evaluate(new ClimateInput(
			endAmbient, "minecraft:end_highlands", 0, 0, false, false, false, false, 1200L
		));
		assertEquals(DepthZone.END_ISLANDS, endHighlands.telemetry().depthZone());
		assertFalse(endHighlands.frostPenaltyActive());
		assertFalse(endHighlands.heatPenaltyActive());
		assertEquals(ClimateStatus.COMFORTABLE, endHighlands.status());

		HudPresentation hud = HudTelemetryFormatter.buildPresentation(
			"End Highlands",
			endHighlands.telemetry().depthZone(),
			endHighlands.telemetry().thermalBand(),
			endHighlands.perceivedCelsius(),
			endHighlands.humidityPercent(),
			endHighlands.microWeather(),
			endHighlands.status(),
			0,
			0,
			true
		);
		assertEquals(DepthZone.END_ISLANDS.translationKey(), hud.headerLine().spans().getLast().key());
	}
}
