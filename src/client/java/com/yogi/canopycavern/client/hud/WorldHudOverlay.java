package com.yogi.canopycavern.client.hud;

import com.yogi.canopycavern.CanopyCavernMod;
import com.yogi.canopycavern.client.ClientEnvironmentSampler;
import com.yogi.canopycavern.client.ClientEnvironmentSampler.SampledEnvironment;
import com.yogi.canopycavern.config.CanopyCavernConfig;
import com.yogi.canopycavern.core.EnvironmentTelemetry;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.network.chat.Component;

/**
 * Renders a compact top-left ambient world telemetry card showing depth zone, biome,
 * apparent temperature, and surface/cave atmospheric condition.
 */
public final class WorldHudOverlay {
	private static final int MARGIN_X = 8;
	private static final int MARGIN_Y = 8;
	private static final int PADDING = 6;
	private static final int LINE_GAP = 2;
	private static final int BG_COLOR = 0xAA11161C;
	private static final int BORDER_COLOR = 0xCC334455;
	private static final int TEXT_MUTED = 0xFFB8C4D0;

	private WorldHudOverlay() {
	}

	/** Renders the telemetry panel when enabled and a sampled client environment is available. */
	public static void render(GuiGraphicsExtractor graphics, DeltaTracker deltaTracker) {
		CanopyCavernConfig config = CanopyCavernMod.getConfig();
		if (!config.clientHudEnabled()) {
			return;
		}

		Minecraft client = Minecraft.getInstance();
		if (client.player == null || client.level == null) {
			return;
		}

		ClientEnvironmentSampler.latest().ifPresent(sample -> drawPanel(graphics, client.font, sample, config));
	}

	private static void drawPanel(
		GuiGraphicsExtractor graphics,
		Font font,
		SampledEnvironment sample,
		CanopyCavernConfig config
	) {
		var snapshot = sample.snapshot();
		Component zoneLine = Component.translatable(snapshot.depthZone().translationKey());
		Component biomeLine = Component.literal(sample.biomeName());

		String tempText = EnvironmentTelemetry.formatTemperature(snapshot.apparentCelsius(), config.useCelsius());
		Component thermalLabel = Component.translatable(snapshot.thermalBand().translationKey());
		Component conditionLabel = resolveCondition(sample);
		Component statsLine = Component.literal(tempText + " · ")
			.append(thermalLabel)
			.append(" · ")
			.append(conditionLabel);

		int contentWidth = Math.max(
			font.width(zoneLine),
			Math.max(font.width(biomeLine), font.width(statsLine))
		);
		int boxWidth = contentWidth + (PADDING * 2) + 4;
		int boxHeight = (font.lineHeight * 3) + (LINE_GAP * 2) + (PADDING * 2);

		int x1 = MARGIN_X;
		int y1 = MARGIN_Y;
		int x2 = x1 + boxWidth;
		int y2 = y1 + boxHeight;

		graphics.fill(x1 - 1, y1 - 1, x2 + 1, y2 + 1, BORDER_COLOR);
		graphics.fill(x1, y1, x2, y2, BG_COLOR);
		graphics.fill(x1, y1, x1 + 3, y2, snapshot.depthZone().accentColor());

		int textX = x1 + PADDING + 2;
		int row1Y = y1 + PADDING;
		int row2Y = row1Y + font.lineHeight + LINE_GAP;
		int row3Y = row2Y + font.lineHeight + LINE_GAP;

		graphics.text(font, zoneLine, textX, row1Y, snapshot.depthZone().accentColor(), true);
		graphics.text(font, biomeLine, textX, row2Y, TEXT_MUTED, true);
		graphics.text(font, statsLine, textX, row3Y, snapshot.thermalBand().accentColor(), true);
	}

	private static Component resolveCondition(SampledEnvironment sample) {
		if (sample.snapshot().dampCave()) {
			return Component.translatable("hud.canopycavern.condition.damp_cave");
		}
		if (sample.raining()) {
			return Component.translatable("hud.canopycavern.condition.rain");
		}
		if (sample.night()) {
			return Component.translatable("hud.canopycavern.condition.night");
		}
		return Component.translatable("hud.canopycavern.condition.clear");
	}
}
