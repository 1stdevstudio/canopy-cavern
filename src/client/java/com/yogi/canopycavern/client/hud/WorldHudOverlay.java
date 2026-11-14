package com.yogi.canopycavern.client.hud;

import com.yogi.canopycavern.CanopyCavernMod;
import com.yogi.canopycavern.client.ClientClimateCache;
import com.yogi.canopycavern.client.ClientEnvironmentSampler;
import com.yogi.canopycavern.client.ClientEnvironmentSampler.SampledEnvironment;
import com.yogi.canopycavern.config.CanopyCavernConfig;
import com.yogi.canopycavern.core.ClimateSimulation.ClimateStatus;
import com.yogi.canopycavern.core.ClimateSimulation.MicroWeather;
import com.yogi.canopycavern.core.HudTelemetryFormatter;
import com.yogi.canopycavern.core.HudTelemetryFormatter.HudLine;
import com.yogi.canopycavern.core.HudTelemetryFormatter.HudPresentation;
import com.yogi.canopycavern.core.HudTelemetryFormatter.HudSpan;
import com.yogi.canopycavern.network.ModNetworking.ClimateSyncPayload;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;

/**
 * Minimal top-left corner strip displaying biome, depth zone, temperature, humidity,
 * and non-idle climate status or gear protection without obstructing gameplay view.
 */
public final class WorldHudOverlay {

	private static final int MARGIN_X = 6;
	private static final int MARGIN_Y = 6;
	private static final int ACCENT_WIDTH = 2;
	private static final int PAD_LEFT = 5;
	private static final int PAD_RIGHT = 5;
	private static final int PAD_TOP = 3;
	private static final int PAD_BOTTOM = 2;
	private static final int ROW_STEP = 10;
	private static final String SEPARATOR = " \u00B7 ";

	private WorldHudOverlay() {
	}

	/** Renders the compact environmental strip unless hidden, in a menu, or under F3 debug. */
	public static void render(GuiGraphicsExtractor graphics, DeltaTracker deltaTracker) {
		Minecraft client = Minecraft.getInstance();
		CanopyCavernConfig config = CanopyCavernMod.getConfig();
		if (!config.clientHudEnabled() || client.player == null || client.level == null) {
			return;
		}
		if (client.gui.screen() != null || client.getDebugOverlay().showDebugScreen()) {
			return;
		}

		SampledEnvironment sample = ClientEnvironmentSampler.latest().orElse(null);
		if (sample == null) {
			return;
		}
		ClimateSyncPayload climate = ClientClimateCache.latest();
		drawMinimalStrip(graphics, client.font, sample, climate, config.useCelsius());
	}

	private static void drawMinimalStrip(
		GuiGraphicsExtractor graphics,
		Font font,
		SampledEnvironment sample,
		ClimateSyncPayload climate,
		boolean useCelsius
	) {
		var snapshot = sample.snapshot();
		HudPresentation model = HudTelemetryFormatter.buildPresentation(
			sample.biomeName(),
			snapshot.depthZone(),
			snapshot.thermalBand(),
			climate.perceivedCelsius(),
			climate.humidityPercent(),
			MicroWeather.fromId(climate.microWeatherId()),
			ClimateStatus.fromId(climate.climateStatusId()),
			climate.thermalInsulationPercent(),
			climate.cavernCoolingPercent(),
			useCelsius
		);

		int maxContentWidth = Math.max(88, Math.min(180, (graphics.guiWidth() / 2) - 18));
		Component headerComp = formatHeader(font, model.headerLine(), maxContentWidth);
		Component telemetryComp = toComponent(model.telemetryLine());
		Component modifierComp = model.modifierLine() == null ? null : toComponent(model.modifierLine());

		int contentWidth = Math.max(font.width(headerComp), font.width(telemetryComp));
		if (modifierComp != null) {
			contentWidth = Math.max(contentWidth, font.width(modifierComp));
		}

		int boxWidth = PAD_LEFT + contentWidth + PAD_RIGHT;
		int boxHeight = PAD_TOP + (model.rowCount() * ROW_STEP) + PAD_BOTTOM - 1;

		graphics.fill(
			MARGIN_X,
			MARGIN_Y,
			MARGIN_X + boxWidth,
			MARGIN_Y + boxHeight,
			model.style().backgroundColor()
		);
		graphics.fill(
			MARGIN_X,
			MARGIN_Y,
			MARGIN_X + ACCENT_WIDTH,
			MARGIN_Y + boxHeight,
			model.style().accentBarColor()
		);

		int textX = MARGIN_X + PAD_LEFT;
		int textY = MARGIN_Y + PAD_TOP;
		graphics.text(font, headerComp, textX, textY, 0xFFFFFFFF, true);
		graphics.text(font, telemetryComp, textX, textY + ROW_STEP, 0xFFFFFFFF, true);
		if (modifierComp != null) {
			graphics.text(font, modifierComp, textX, textY + (ROW_STEP * 2), 0xFFFFFFFF, true);
		}
	}

	private static Component formatHeader(Font font, HudLine headerLine, int maxContentWidth) {
		Component full = toComponent(headerLine);
		if (font.width(full) <= maxContentWidth || headerLine.spans().size() < 2) {
			return full;
		}
		HudSpan biomeSpan = headerLine.spans().get(0);
		HudSpan zoneSpan = headerLine.spans().get(1);
		Component zoneComp = spanToComponent(zoneSpan);
		int reserved = font.width(SEPARATOR) + font.width(zoneComp) + font.width("...");
		String rawBiome = biomeSpan.literal() == null ? "" : biomeSpan.literal();
		String trimmed = font.plainSubstrByWidth(rawBiome, Math.max(16, maxContentWidth - reserved)).stripTrailing();
		return Component.empty()
			.append(Component.literal(trimmed + "...").withColor(biomeSpan.color()))
			.append(Component.literal(SEPARATOR).withColor(HudTelemetryFormatter.COLOR_SEPARATOR))
			.append(zoneComp);
	}

	private static Component toComponent(HudLine line) {
		MutableComponent out = Component.empty();
		for (int i = 0; i < line.spans().size(); i++) {
			if (i > 0) {
				out.append(Component.literal(SEPARATOR).withColor(HudTelemetryFormatter.COLOR_SEPARATOR));
			}
			out.append(spanToComponent(line.spans().get(i)));
		}
		return out;
	}

	private static Component spanToComponent(HudSpan span) {
		MutableComponent comp = span.isTranslatable()
			? Component.translatable(span.key(), span.args().toArray())
			: Component.literal(span.literal());
		return comp.withColor(span.color());
	}
}
