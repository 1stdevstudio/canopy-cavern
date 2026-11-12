package com.yogi.canopycavern.client;

import com.mojang.blaze3d.platform.InputConstants;
import com.yogi.canopycavern.CanopyCavernMod;
import com.yogi.canopycavern.client.atmosphere.ClientAtmosphereTicker;
import com.yogi.canopycavern.client.hud.WorldHudOverlay;
import com.yogi.canopycavern.config.CanopyCavernConfig;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.rendering.v1.hud.VanillaHudElements;
import net.minecraft.client.KeyMapping;
import net.minecraft.network.chat.Component;

/**
 * Client-first entrypoint registering the ambient telemetry HUD, keybindings,
 * and surface/cave atmospheric particle effects.
 */
public final class CanopyCavernClient implements ClientModInitializer {
	private static final KeyMapping.Category KEY_CATEGORY = KeyMapping.Category.register(
		CanopyCavernMod.id("general")
	);

	private static KeyMapping toggleHudKey;

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

		HudElementRegistry.attachElementBefore(
			VanillaHudElements.CHAT,
			CanopyCavernMod.id("world_telemetry_hud"),
			WorldHudOverlay::render
		);

		ClientTickEvents.END_CLIENT_TICK.register(client -> {
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

			ClientEnvironmentSampler.sampleTick(client);
			ClientAtmosphereTicker.tick(client);
		});
	}
}
