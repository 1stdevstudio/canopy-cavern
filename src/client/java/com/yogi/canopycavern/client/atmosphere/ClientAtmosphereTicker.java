package com.yogi.canopycavern.client.atmosphere;

import com.yogi.canopycavern.CanopyCavernMod;
import com.yogi.canopycavern.client.ClientEnvironmentSampler;
import com.yogi.canopycavern.client.ClientEnvironmentSampler.SampledEnvironment;
import com.yogi.canopycavern.core.EnvironmentTelemetry.DepthZone;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.util.RandomSource;

/**
 * Spawns subtle client-side atmospheric particles around forest canopies and deep caves.
 */
public final class ClientAtmosphereTicker {
	private static int tickCounter;

	private ClientAtmosphereTicker() {
	}

	/** Emits sparse ambient dust or woodland particles when enabled and unpaused. */
	public static void tick(Minecraft client) {
		if (!CanopyCavernMod.getConfig().clientAtmosphereParticlesEnabled() || client.isPaused()) {
			return;
		}
		if (++tickCounter % 4 != 0) {
			return;
		}

		LocalPlayer player = client.player;
		ClientLevel level = client.level;
		if (player == null || level == null) {
			return;
		}

		ClientEnvironmentSampler.latest().ifPresent(sample -> spawnAmbientParticles(player, level, sample));
	}

	private static void spawnAmbientParticles(LocalPlayer player, ClientLevel level, SampledEnvironment sample) {
		RandomSource random = level.getRandom();
		DepthZone zone = sample.snapshot().depthZone();

		if (zone == DepthZone.SHALLOW_CAVE || zone == DepthZone.DEEP_CAVERN || zone == DepthZone.ABYSSAL_DEPTHS) {
			if (random.nextFloat() < 0.45f) {
				double px = player.getX() + (random.nextDouble() - 0.5) * 14.0;
				double py = player.getY() + random.nextDouble() * 4.5;
				double pz = player.getZ() + (random.nextDouble() - 0.5) * 14.0;
				level.addParticle(ParticleTypes.ASH, px, py, pz, 0.0, -0.01, 0.0);
			}
			return;
		}

		if (sample.forestBiome() && !sample.raining() && random.nextFloat() < 0.35f) {
			double px = player.getX() + (random.nextDouble() - 0.5) * 16.0;
			double py = player.getY() + 2.0 + random.nextDouble() * 5.0;
			double pz = player.getZ() + (random.nextDouble() - 0.5) * 16.0;
			level.addParticle(ParticleTypes.SPORE_BLOSSOM_AIR, px, py, pz, 0.01, -0.02, 0.01);
		}
	}
}
