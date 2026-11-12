package com.yogi.canopycavern.client;

import com.mojang.blaze3d.platform.InputConstants;
import com.yogi.canopycavern.CanopyCavernMod;
import com.yogi.canopycavern.client.atmosphere.ClientAtmosphereTicker;
import com.yogi.canopycavern.client.gui.CanopyFieldGuideScreen;
import com.yogi.canopycavern.client.hud.WorldHudOverlay;
import com.yogi.canopycavern.client.render.VillageSentinelRenderer;
import com.yogi.canopycavern.config.CanopyCavernConfig;
import com.yogi.canopycavern.entity.ModEntities;
import com.yogi.canopycavern.network.ModNetworking.ClimateSyncPayload;
import com.yogi.canopycavern.network.ModNetworking.OpenGuidePayload;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.hud.VanillaHudElements;
import net.minecraft.client.KeyMapping;
import net.minecraft.network.chat.Component;

/**
 * Client-first entrypoint registering the ambient telemetry HUD, keybindings,
 * network receivers, custom entity renderers, and atmospheric effects.
 */
public final class CanopyCavernClient implements ClientModInitializer {
	private static final KeyMapping.Category KEY_CATEGORY = KeyMapping.Category.register(
		CanopyCavernMod.id("general")
	);

	private static KeyMapping toggleHudKey;
	private static KeyMapping openGuideKey;

	@Override
	public void onInitializeClient() {
		toggleHudKey = KeyMappingHelper.registerKeyMapping(
			new KeyMapping(
				"key.canopycavern.toggle_hud",
				InputConstants.Type.KEYBOARD,
				InputConstants.KEY_H,
				KEY_CATEGORY
			)
		);
		openGuideKey = KeyMappingHelper.registerKeyMapping(
			new KeyMapping(
				"key.canopycavern.open_guide",
				InputConstants.Type.KEYBOARD,
				InputConstants.KEY_G,
				KEY_CATEGORY
			)
		);

		EntityRendererRegistry.register(ModEntities.VILLAGE_SENTINEL, VillageSentinelRenderer::new);

		ClientPlayNetworking.registerGlobalReceiver(ClimateSyncPayload.TYPE, (payload, context) ->
			ClientClimateCache.update(payload)
		);
		ClientPlayNetworking.registerGlobalReceiver(OpenGuidePayload.TYPE, (payload, context) ->
			context.client().execute(() -> context.client().gui.setScreen(new CanopyFieldGuideScreen()))
		);

		HudElementRegistry.attachElementBefore(
			VanillaHudElements.CHAT,
			CanopyCavernMod.id("world_telemetry_hud"),
			WorldHudOverlay::render
		);

		ClientTickEvents.END_CLIENT_TICK.register(client -> {
			if (client.level == null) {
				ClientClimateCache.reset();
				return;
			}
			while (toggleHudKey.consumeClick()) {
				CanopyCavernConfig current = CanopyCavernMod.getConfig();
				CanopyCavernConfig updated = current.withClientHudEnabled(!current.clientHudEnabled());
				CanopyCavernMod.updateConfig(updated);

				if (client.player != null) {
					String key = updated.clientHudEnabled()
						? "message.canopycavern.hud_enabled"
						: "message.canopycavern.hud_disabled";
					client.player.sendSystemMessage(Component.translatable(key));
				}
			}
			while (openGuideKey.consumeClick()) {
				if (client.gui.screen() == null) {
					client.gui.setScreen(new CanopyFieldGuideScreen());
				}
			}
			ClientEnvironmentSampler.sampleTick(client);
			ClientAtmosphereTicker.tick(client);
		});
	}
}
