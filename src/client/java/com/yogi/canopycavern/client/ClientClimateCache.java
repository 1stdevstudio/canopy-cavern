package com.yogi.canopycavern.client;

import com.yogi.canopycavern.core.ClimateSimulation;
import com.yogi.canopycavern.core.ClimateSimulation.ClimateSnapshot;
import com.yogi.canopycavern.network.ModNetworking.ClimateSyncPayload;

/**
 * Client-side cache of the latest authoritative server climate, micro-weather,
 * shelter/campfire buff, and armor insulation payload.
 */
public final class ClientClimateCache {

	private static volatile ClimateSyncPayload latest = neutralPayload();

	private ClientClimateCache() {
	}

	public static void update(ClimateSyncPayload payload) {
		latest = payload;
	}

	public static ClimateSyncPayload latest() {
		return latest;
	}

	public static void reset() {
		latest = neutralPayload();
	}

	private static ClimateSyncPayload neutralPayload() {
		ClimateSnapshot neutral = ClimateSimulation.ClimateSnapshot.neutral();
		return new ClimateSyncPayload(
			neutral.humidityPercent(),
			neutral.microWeather().id(),
			neutral.status().id(),
			neutral.thermalInsulationPercent(),
			neutral.cavernCoolingPercent(),
			neutral.perceivedCelsius(),
			neutral.frostPenaltyActive(),
			neutral.heatPenaltyActive(),
			neutral.warmthRecoveryActive(),
			false,
			false
		);
	}
}
