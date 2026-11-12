package com.yogi.canopycavern.client.hud;

import com.yogi.canopycavern.CanopyCavernMod;
import com.yogi.canopycavern.client.ClientClimateCache;
import com.yogi.canopycavern.client.ClientEnvironmentSampler;
import com.yogi.canopycavern.client.ClientEnvironmentSampler.SampledEnvironment;
import com.yogi.canopycavern.config.CanopyCavernConfig;
import com.yogi.canopycavern.core.ClimateSimulation.ClimateStatus;
import com.yogi.canopycavern.core.ClimateSimulation.MicroWeather;
import com.yogi.canopycavern.core.EnvironmentTelemetry;
import com.yogi.canopycavern.network.ModNetworking.ClimateSyncPayload;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.network.chat.Component;

/**
 * Compact top-left environmental HUD showing biome, depth zone, live climate & humidity telemetry,
 * micro-weather condition, campfire/shelter buffer, and armor protection percentages.
 */
public final class WorldHudOverlay {

	private static final int CARD_X = 8;
	private static final int CARD_Y = 8;
	private static final int CARD_WIDTH = 192;
	private static final int CARD_HEIGHT = 68;

	private WorldHudOverlay() {
	}

	public static void render(GuiGraphicsExtractor graphics, DeltaTracker deltaTracker) {
		Minecraft client = Minecraft.getInstance();
		CanopyCavernConfig config = CanopyCavernMod.getConfig();
		if (!config.clientHudEnabled() || client.player == null || client.level == null) {
			return;
		}
		if (client.gui.screen() != null) {
			return;
		}

		SampledEnvironment sample = ClientEnvironmentSampler.latest().orElse(null);
		if (sample == null) {
			return;
		}
		ClimateSyncPayload climate = ClientClimateCache.latest();
		drawPanel(graphics, client.font, sample, climate, config.useCelsius());
	}

	private static void drawPanel(
		GuiGraphicsExtractor graphics,
		Font font,
		SampledEnvironment sample,
		ClimateSyncPayload climate,
		boolean useCelsius
	) {
		graphics.fill(CARD_X, CARD_Y, CARD_X + CARD_WIDTH, CARD_Y + CARD_HEIGHT, 0xA60E1614);
		graphics.outline(CARD_X, CARD_Y, CARD_WIDTH, CARD_HEIGHT, 0xFF4AA87F);

		var snapshot = sample.snapshot();
		String biomeLabel = sample.biomeName();
		graphics.text(font, biomeLabel, CARD_X + 7, CARD_Y + 6, 0xFFE8F5EE, false);

		Component zone = Component.translatable(snapshot.depthZone().translationKey());
		graphics.text(font, zone, CARD_X + 7, CARD_Y + 18, snapshot.depthZone().accentColor(), false);

		String tempStr = EnvironmentTelemetry.formatTemperature(climate.perceivedCelsius(), useCelsius);
		Component weatherComp = Component.translatable("hud.canopycavern.weather." + MicroWeather.fromId(climate.microWeatherId()).id());
		String line3 = tempStr + "  |  " + climate.humidityPercent() + "% RH  |  " + weatherComp.getString();
		graphics.text(font, line3, CARD_X + 7, CARD_Y + 30, snapshot.thermalBand().accentColor(), false);

		ClimateStatus status = ClimateStatus.fromId(climate.climateStatusId());
		Component statusComp = Component.translatable("hud.canopycavern.status." + status.id());
		int statusColor = switch (status) {
			case FREEZING -> 0xFF7FD7FF;
			case CHILLY -> 0xFFB0E4FF;
			case OVERHEATED -> 0xFFFF7D6B;
			case HUMID -> 0xFF9DF0B8;
			case SHELTERED -> 0xFFFFD885;
			case COMFORTABLE -> 0xFFD9E8E0;
		};
		graphics.text(font, statusComp, CARD_X + 7, CARD_Y + 42, statusColor, false);

		Component gearLine = Component.translatable(
			"hud.canopycavern.protection",
			climate.thermalInsulationPercent(),
			climate.cavernCoolingPercent()
		);
		graphics.text(font, gearLine, CARD_X + 7, CARD_Y + 54, 0xFFAABDB4, false);
	}
}
