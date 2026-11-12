package com.yogi.canopycavern.client.atmosphere;

import com.yogi.canopycavern.CanopyCavernMod;
import com.yogi.canopycavern.client.ClientClimateCache;
import com.yogi.canopycavern.client.ClientEnvironmentSampler;
import com.yogi.canopycavern.client.ClientEnvironmentSampler.SampledEnvironment;
import com.yogi.canopycavern.config.CanopyCavernConfig;
import com.yogi.canopycavern.core.ClimateSimulation.MicroWeather;
import com.yogi.canopycavern.network.ModNetworking.ClimateSyncPayload;
import net.minecraft.client.Minecraft;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;

/**
 * Emits lightweight environmental particles and throttled dynamic atmospheric sound cues
 * calibrated to depth tier, biome micro-weather, and FPS budget.
 */
public final class ClientAtmosphereTicker {

	private static final int PARTICLE_INTERVAL_TICKS = 4;
	private static final int AMBIENT_SOUND_INTERVAL_TICKS = 150;

	private ClientAtmosphereTicker() {
	}

	public static void tick(Minecraft client) {
		CanopyCavernConfig config = CanopyCavernMod.getConfig();
		if (client.isPaused() || client.player == null || client.level == null) {
			return;
		}
		SampledEnvironment sample = ClientEnvironmentSampler.latest().orElse(null);
		if (sample == null) {
			return;
		}

		long time = client.level.getGameTime();
		ClimateSyncPayload climate = ClientClimateCache.latest();
		MicroWeather weather = MicroWeather.fromId(climate.microWeatherId());

		if (config.clientAtmosphereParticlesEnabled() && time % PARTICLE_INTERVAL_TICKS == 0L) {
			spawnAmbientParticles(client, sample, weather);
		}
		if (config.dynamicAmbienceEnabled() && time % AMBIENT_SOUND_INTERVAL_TICKS == 75L) {
			playSubtleAmbienceSound(client, sample, weather);
		}
	}

	private static void spawnAmbientParticles(Minecraft client, SampledEnvironment sample, MicroWeather weather) {
		var random = client.level.getRandom();
		var player = client.player;
		ParticleOptions particle = switch (weather) {
			case BLIZZARD_CHILL -> ParticleTypes.SNOWFLAKE;
			case MISTY_WIND -> ParticleTypes.WHITE_ASH;
			case CAVERN_HUMID -> sample.biomeId().contains("verdant_grotto") || sample.biomeId().contains("lush_caves")
				? ParticleTypes.SPORE_BLOSSOM_AIR
				: ParticleTypes.GLOW;
			case THERMAL_STEAM -> ParticleTypes.ASH;
			case CLEAR -> null;
		};
		if (particle == null) {
			return;
		}

		int count = weather == MicroWeather.BLIZZARD_CHILL ? 3 : 1;
		for (int i = 0; i < count; i++) {
			double px = player.getX() + (random.nextDouble() - 0.5) * 14.0;
			double py = player.getY() + 0.8 + random.nextDouble() * 4.5;
			double pz = player.getZ() + (random.nextDouble() - 0.5) * 14.0;
			double vx = weather == MicroWeather.MISTY_WIND || weather == MicroWeather.BLIZZARD_CHILL ? 0.04 : 0.0;
			client.level.addParticle(particle, px, py, pz, vx, -0.01, 0.0);
		}
	}

	private static void playSubtleAmbienceSound(Minecraft client, SampledEnvironment sample, MicroWeather weather) {
		var player = client.player;
		if (weather == MicroWeather.MISTY_WIND || weather == MicroWeather.BLIZZARD_CHILL) {
			client.level.playLocalSound(
				player.getX(),
				player.getY() + 1.5,
				player.getZ(),
				SoundEvents.ELYTRA_FLYING,
				SoundSource.AMBIENT,
				0.08F,
				0.95F,
				false
			);
		} else if (weather == MicroWeather.CAVERN_HUMID && sample.snapshot().dampCave()) {
			client.level.playLocalSound(
				player.getX() + 1.5,
				player.getY() + 2.0,
				player.getZ() - 1.5,
				SoundEvents.POINTED_DRIPSTONE_DRIP_WATER,
				SoundSource.AMBIENT,
				0.28F,
				1.05F,
				false
			);
		}
	}
}
