package com.yogi.canopycavern.client;

import com.yogi.canopycavern.core.EnvironmentTelemetry;
import com.yogi.canopycavern.core.EnvironmentTelemetry.AmbientInput;
import com.yogi.canopycavern.core.EnvironmentTelemetry.AmbientSnapshot;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.resources.ResourceKey;
import net.minecraft.tags.BiomeTags;
import net.minecraft.world.level.LightLayer;
import net.minecraft.world.level.biome.Biome;

import java.util.Optional;

/**
 * Samples local client world state once per tick and caches the evaluated telemetry snapshot
 * so HUD rendering stays allocation-light.
 */
public final class ClientEnvironmentSampler {
	private static volatile SampledEnvironment latestSample;

	private ClientEnvironmentSampler() {
	}

	/** Combined client snapshot ready for HUD presentation and ambient particle triggers. */
	public record SampledEnvironment(
		AmbientSnapshot snapshot,
		String biomeId,
		String biomeName,
		boolean forestBiome,
		boolean raining,
		boolean night
	) {
	}

	/** Refreshes the cached environmental reading from the active client player and level. */
	public static void sampleTick(Minecraft client) {
		LocalPlayer player = client.player;
		ClientLevel level = client.level;
		if (player == null || level == null) {
			latestSample = null;
			return;
		}

		BlockPos pos = player.blockPosition();
		Holder<Biome> biomeHolder = level.getBiome(pos);
		Biome biome = biomeHolder.value();

		boolean canSeeSky = level.canSeeSky(pos);
		int skyLight = level.getBrightness(LightLayer.SKY, pos);
		boolean raining = level.isRainingAt(pos);
		boolean night = level.isDarkOutside();

		AmbientInput input = new AmbientInput(
			biome.getBaseTemperature(),
			pos.getY(),
			level.getSeaLevel(),
			canSeeSky,
			skyLight,
			raining,
			night,
			player.isInWater()
		);
		AmbientSnapshot snapshot = EnvironmentTelemetry.evaluate(input);

		String rawBiomeKey = biomeHolder.unwrapKey()
			.map(ResourceKey::identifier)
			.map(Object::toString)
			.orElse("unknown");
		String biomeName = EnvironmentTelemetry.formatBiomeName(rawBiomeKey);
		boolean forest = biomeHolder.is(BiomeTags.IS_FOREST) || biomeHolder.is(BiomeTags.IS_TAIGA);

		latestSample = new SampledEnvironment(snapshot, rawBiomeKey, biomeName, forest, raining, night);
	}

	/** Returns the most recent environmental sample, if in-world. */
	public static Optional<SampledEnvironment> latest() {
		return Optional.ofNullable(latestSample);
	}
}
